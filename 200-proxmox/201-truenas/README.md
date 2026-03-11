# 201 — TrueNAS Core 13 (VM)

**IP:** 192.168.1.201
**OS:** TrueNAS Core 13
**Host:** Proxmox (192.168.1.200)

## Role

NAS and ZFS storage server. Shares media over NFS to other VMs.

## Setup

1. Create VM in Proxmox and pass through storage disks.
2. Install TrueNAS Core 13 from ISO.
3. Configure ZFS pool via **Storage → Pools** in the TrueNAS UI.
4. Create NFS shares via **Sharing → Unix Shares (NFS)**.

## NFS Exports

| Dataset | Mount path | Consumers |
|---|---|---|
| — | — | 202-ubuntu-starr, 203-ubuntu-plex |

See [ZFS / NFS mount guide](../../guides/zfs-mount.md) for mounting on Linux VMs.
