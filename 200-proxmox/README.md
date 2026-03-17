# 200 — Proxmox Server

**IP:** 192.168.1.200
**OS:** Proxmox VE

## Hardware

| Component | Details |
|---|---|
| Case | JONSBO N3 Mini-ITX NAS |
| Motherboard | ASUS ROG Strix B760-I Gaming WiFi (LGA 1700, Mini-ITX) |
| CPU | Intel Core i7-13700K (16 cores: 8 P-cores + 8 E-cores) |
| CPU Cooler | Noctua Dual Tower (LGA 1700) |
| RAM | TEAMGROUP T-Force Vulcan DDR5 64 GB (2×32 GB) 5200 MHz CL40 |
| PSU | Corsair SF750 SFX 750W 80+ Platinum |
| Storage (NAS) | 8× Seagate IronWolf 8 TB NAS HDD (3.5" SATA 6 Gb/s, 7200 RPM, 256 MB cache) |
| HBA | LSI 9211-8i (IT mode, FW P20) + 2× SFF-8087 breakout cables |

## Role

Hypervisor hosting all VMs. HBA controller is passed through to TrueNAS VM via IOMMU for direct disk access.

## VMs

| VM | IP | Role | Folder |
|---|---|---|---|
| TrueNAS Core 13 | 192.168.1.201 | NAS / ZFS storage | [201-truenas/](201-truenas/) |
| Ubuntu - Starr | 192.168.1.202 | *arr apps + VPN downloader | [202-ubuntu-starr/](202-ubuntu-starr/) |
| Ubuntu - Plex | 192.168.1.203 | Plex media server | [203-ubuntu-plex/](203-ubuntu-plex/) |
| Ubuntu - Cloud | 192.168.1.204 | VaultWarden, Nextcloud (planned) | [204-cloud/](204-cloud/) |

## IOMMU Setup (PCI Passthrough for HBA)

Required to pass the LSI 9211-8i HBA directly to the TrueNAS VM, giving TrueNAS full control of the disks.

### 1. Enable IOMMU in GRUB

```bash
sudo nano /etc/default/grub
```

Find `GRUB_CMDLINE_LINUX_DEFAULT` and add `intel_iommu=on iommu=pt`:

```
GRUB_CMDLINE_LINUX_DEFAULT="quiet intel_iommu=on iommu=pt"
```

```bash
sudo update-grub
```

### 2. Load VFIO kernel modules

```bash
echo -e "vfio\nvfio_iommu_type1\nvfio_pci\nvfio_virqfd" | sudo tee /etc/modules-load.d/vfio.conf
```

### 3. Update initramfs and reboot

```bash
sudo update-initramfs -u -k all
sudo reboot
```

### 4. Verify IOMMU is active

```bash
dmesg | grep -e DMAR -e IOMMU
# Should show: DMAR: IOMMU enabled
```

Check IOMMU groups to confirm the HBA is in its own group:

```bash
for d in /sys/kernel/iommu_groups/*/devices/*; do
  echo "$(basename $(dirname $(dirname $d))): $(lspci -nns $(basename $d))";
done | sort -V | grep -i "SAS\|HBA\|LSI\|1000"
```

### 5. Pass through HBA to TrueNAS VM in Proxmox UI

1. Select TrueNAS VM → **Hardware** → **Add** → **PCI Device**
2. Select the LSI 9211-8i from the list
3. Check **All Functions** and **ROM-Bar**
4. Leave **Primary GPU** unchecked
5. Start the VM — TrueNAS should detect all 8 drives directly
