# 201 — TrueNAS Core 13 (VM)

**IP:** 192.168.1.201
**OS:** TrueNAS Core 13
**Host:** Proxmox (192.168.1.200)

## VM Specs

| Resource | Value |
|---|---|
| vCPU | 6 cores |
| RAM | 24 GB (no ballooning) |
| Disk passthrough | LSI 9211-8i HBA (PCIe passthrough) — 8× Seagate IronWolf 8 TB |

> RAM ballooning is disabled intentionally — ZFS ARC requires stable memory allocation.

## Role

NAS and ZFS storage server. Shares media over NFS to other VMs.

## Setup

1. [Enable IOMMU on Proxmox](../README.md#iommu-setup-pci-passthrough-for-hba) and pass through the LSI 9211-8i HBA.
2. Create VM with specs above (disable ballooning under Options).
3. Install TrueNAS Core 13 from ISO.
3. Configure ZFS pool via **Storage → Pools** in the TrueNAS UI.
4. Create NFS shares via **Sharing → Unix Shares (NFS)**.

## NFS Exports

| Dataset | Mount path | Consumers |
|---|---|---|
| — | — | 202-ubuntu-starr, 203-ubuntu-plex |

See [ZFS / NFS mount guide](../../guides/zfs-mount.md) for mounting on Linux VMs.
