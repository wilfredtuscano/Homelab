# Add an NVMe ZFS Pool to Proxmox

Add a NVMe drive to a Proxmox host as a dedicated ZFS pool (`local-nvme`) for low-latency LXC rootfs and VM disks. Bulk storage stays on TrueNAS over NFS; only hot, latency-sensitive workloads (SQLite, Docker overlays, container metadata) live on the NVMe.

## Why a separate pool

The Proxmox boot pool (`rpool`) often lives on slower SATA SSDs. Putting `*arr` SQLite DBs and Docker overlays on a dedicated NVMe pool keeps fast IO off the boot disks and gives you a clean separation:

- `rpool` — boot/system, legacy disks, low churn
- `local-nvme` — LXC rootfs, fast SQLite/Docker writes
- TrueNAS NFS — bulk media, downloads, anything that fits "large + sequential"

A single NVMe gives no redundancy. Snapshots via ZFS partially compensate, but treat the pool as cattle — keep configs on a backup share so a drive failure means rebuild-not-restore.

## 1. Heads-up: adding the drive may rename the LAN interface

Adding a PCIe device shifts bus enumeration. The Linux interface name follows the bus position (`enp4s0` → `enp5s0` is typical when an NVMe is added), and Proxmox's `/etc/network/interfaces` references the old name, so the bridge comes up without a backing port and the host loses its IP.

When this happens, the host boots fine but isn't reachable. Connect a monitor + keyboard and:

```bash
ip -br addr               # find the new interface name (it'll be DOWN)
cat /etc/network/interfaces  # see the stale reference
nano /etc/network/interfaces  # replace old name with new in both spots
ifup <new-name>
systemctl restart networking
```

(There's a permanent fix using a systemd `.link` file to pin the interface name to the NIC's MAC — out of scope for this guide.)

## 2. Identify the new drive (do not wipe the wrong disk)

```bash
ssh root@192.168.1.200

# See all block devices
lsblk -d -o NAME,SIZE,MODEL,SERIAL,TRAN

# Get the stable by-id path — use this for the pool
ls -l /dev/disk/by-id/ | grep -i nvme | grep -v part

# Confirm no existing zpools on it
zpool list
zpool import 2>&1 | head -20
```

Confirm by **size and model** that you're looking at the new drive, not a system disk. The `by-id` name (e.g. `nvme-SAMSUNG_MZVL21T0HCLR-00B00_S676NF0R523656`) is what the pool should reference — `/dev/nvmeXn1` numbering can shift on reboot.

> If `zpool import` lists pools from a guest VM (e.g. TrueNAS), that's TrueNAS's boot pool leaking into the host's view — ignore it, do not import.

## 3. Wipe existing data

```bash
sgdisk --zap-all /dev/nvme0n1
wipefs -a /dev/nvme0n1
lsblk /dev/nvme0n1   # should show just the device, no partitions
```

## 4. Create the pool

Use the **by-id** path, not `/dev/nvme0n1`:

```bash
zpool create -f \
  -o ashift=12 \
  -o autotrim=on \
  -O compression=lz4 \
  -O atime=off \
  -O xattr=sa \
  -O acltype=posixacl \
  -O dnodesize=auto \
  local-nvme \
  /dev/disk/by-id/nvme-SAMSUNG_MZVL21T0HCLR-00B00_S676NF0R523656
```

| Flag | Why |
|---|---|
| `ashift=12` | 4 KiB sectors — standard for modern NVMe. Wrong value is permanent. |
| `autotrim=on` | Periodic TRIM — important for sustained NVMe write performance. |
| `compression=lz4` | Fast, near-free compression; helps small SQLite writes. |
| `atime=off` | No metadata write on every read. |
| `xattr=sa`, `acltype=posixacl`, `dnodesize=auto` | Proxmox + Docker best-practice defaults. |

Verify:

```bash
zpool status local-nvme
zfs list -r local-nvme
```

## 5. Cap the ZFS ARC

ZFS uses up to 50% of system RAM for its ARC cache by default — too greedy on a hypervisor where most RAM is meant for VMs/CTs. Cap at 8 GiB (adjust for your host):

```bash
cat /sys/module/zfs/parameters/zfs_arc_max
# 0 = default (50% of RAM)

echo "options zfs zfs_arc_max=8589934592" > /etc/modprobe.d/zfs.conf
update-initramfs -u

# Apply now without rebooting:
echo 8589934592 > /sys/module/zfs/parameters/zfs_arc_max
cat /sys/module/zfs/parameters/zfs_arc_max
# Should now show: 8589934592
```

## 6. Register as Proxmox storage

```bash
pvesm add zfspool local-nvme --pool local-nvme --content rootdir,images --sparse 1
pvesm status
```

| Flag | Effect |
|---|---|
| `--content rootdir,images` | Available for both LXC rootfs and VM disks |
| `--sparse 1` | Thin provisioning — an 80 GB CT only consumes what it actually uses |

The pool now appears in the Proxmox UI storage picker.

## 7. Move an existing LXC onto the new pool

```bash
# Stop the CT
pct stop 213

# Current location
pct config 213 | grep rootfs
# Expect: rootfs: local-zfs:subvol-213-disk-0,size=80G

# Move + delete old volume
pct move-volume 213 rootfs local-nvme --delete 1

# Confirm
pct config 213 | grep rootfs
# Expect: rootfs: local-nvme:subvol-213-disk-0,size=80G

pct start 213
```

For VMs, the equivalent is `qm move-disk <vmid> <disk> local-nvme --delete 1`.
