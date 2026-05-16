# Docker in a Proxmox LXC Container

How to create a privileged LXC on Proxmox and get Docker running inside it, including iGPU passthrough for Intel QuickSync and NFS mounts from TrueNAS.

## 1. Prepare the Proxmox host

### Install Intel VA-API driver

```bash
ssh root@192.168.1.200
apt install -y intel-media-va-driver libva-utils
vainfo  # should list VAProfileH264*, VAProfileHEVC*, VAProfileAV1*, etc.
```

### Fix apt repos (no subscription)

If `apt update` fails with 401 errors from enterprise repos:

```bash
echo "# disabled - no subscription" > /etc/apt/sources.list.d/pve-enterprise.list
echo "# disabled - no subscription" > /etc/apt/sources.list.d/ceph.list
echo "deb http://download.proxmox.com/debian/pve bookworm pve-no-subscription" \
  > /etc/apt/sources.list.d/pve-no-subscription.list
apt update
```

## 2. Create the LXC

In Proxmox UI → **Create CT**:

| Field | Value |
|---|---|
| Template | Ubuntu 22.04 LTS (24.04 not supported for privileged on this PVE version) |
| **Unprivileged container** | ☐ **unchecked** (must be privileged) |
| Disk | 80 GB |
| CPU | 6 cores |
| Memory | 8192 MB |
| IP | static IP / 24, gateway 192.168.1.1 |
| DNS | 192.168.1.199 (Pi-hole) |
| Features | ☑ Nesting |

**Do not start the CT yet.**

## 3. Add iGPU and AppArmor config

On the Proxmox host, edit the LXC config (replace `213` with your CT ID):

```bash
nano /etc/pve/lxc/213.conf
```

Update the existing `features:` line and append the rest:

```
features: mount=nfs,nesting=1,fuse=1
lxc.apparmor.profile: unconfined
lxc.cgroup2.devices.allow: c 226:0 rwm
lxc.cgroup2.devices.allow: c 226:128 rwm
lxc.mount.entry: /dev/dri dev/dri none bind,optional,create=dir
```

> If a `features:` line already exists from LXC creation, update it in place rather than adding a second one.

Now start the CT.

## 4. Enable NFS in LXC features

In Proxmox UI → CT 213 → **Options** → **Features** → check **NFS** → OK.

## 5. Fix SSH access

In the Proxmox console (CT → Console):

```bash
passwd root
sed -i 's/#PermitRootLogin.*/PermitRootLogin yes/' /etc/ssh/sshd_config
sed -i 's/PasswordAuthentication no/PasswordAuthentication yes/' /etc/ssh/sshd_config
systemctl restart ssh
```

## 6. Set up the LXC

```bash
ssh root@<ct-ip>

apt update && apt upgrade -y
apt install -y curl screen nfs-common

# Install Docker
curl -fsSL https://get.docker.com | sh
```

### Fix Docker — fuse-overlayfs storage driver

Docker's default overlay2 storage driver fails in LXC due to kernel namespace restrictions. Use fuse-overlayfs instead:

```bash
apt install -y fuse-overlayfs

mkdir -p /etc/docker
cat > /etc/docker/daemon.json << 'EOF'
{
  "storage-driver": "fuse-overlayfs"
}
EOF

systemctl restart docker
```

### Fix Docker — AppArmor

Docker tries to load AppArmor profiles into the host kernel, which fails inside LXC. Two fixes are needed:

**Stub out apparmor_parser** (so Docker's profile loading check succeeds):

```bash
mv /usr/sbin/apparmor_parser /usr/sbin/apparmor_parser.real
cat > /usr/sbin/apparmor_parser << 'EOF'
#!/bin/bash
exit 0
EOF
chmod +x /usr/sbin/apparmor_parser
```

**Disable AppArmor service** inside the LXC:

```bash
systemctl disable apparmor --now
systemctl restart docker
```

**Add `security_opt` to all compose files** (prevents runc from applying AppArmor profiles):

```yaml
security_opt:
  - apparmor=unconfined
```

## 7. Create plex user and directory structure

```bash
useradd -m -u 1000 -s /bin/bash plex
usermod -aG docker plex
passwd plex

mkdir -p /home/plex/docker/{plex,audiobookshelf,calibre-web,portainer-agent,monitoring-agent}
chown -R plex:plex /home/plex/docker
```

## 8. Mount NFS

```bash
mkdir -p /mnt/nfs/media
echo "192.168.1.201:/mnt/Vault/Media  /mnt/nfs/media  nfs  defaults  0  0" >> /etc/fstab
mount -a

# Verify
ls /mnt/nfs/media
```

## 9. Verify iGPU

```bash
ls /dev/dri
# Expect: by-path  card0  renderD128
```

## 10. Deploy stacks

Switch to the plex user and bring up stacks one by one:

```bash
su - plex
cd ~/docker/portainer-agent && docker compose up -d
cd ~/docker/plex && docker compose up -d
cd ~/docker/audiobookshelf && docker compose up -d
cd ~/docker/calibre-web && docker compose up -d
```
