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

Version: **TrueNAS-13.0-U6.8** on FreeBSD 13.1-RELEASE-p9.

## Role

NAS and ZFS storage server. Shares media over NFS to the other guests.

## Pools

| Pool | Size | Used | Health |
|---|---|---|---|
| `Vault` | 58.2 TB | 38.8 TB (66%) | ONLINE |
| `boot-pool` | 79.5 GB | 7.6 GB (9%) | ONLINE |

## How the 24 GB is actually used

Measured 2026-08-10:

| | |
|---|---|
| Physical | 23.94 GiB |
| **ZFS ARC** | **20.26 GiB** — cache, elastic and reclaimable |
| Real process memory | ~2.9 GiB |
| **ARC hit ratio** | **98.10%** over 62 days |

The hypervisor reports this VM at ~95% memory permanently, which looks alarming and is not. Almost
all of it is ARC, and ARC always expands to fill what it is given. **Do not right-size this VM from
the Proxmox figure** — use the SNMP metrics, which separate the two.

Reclaiming memory here is possible but it is a real trade, not free slack: a 98% hit ratio against
317 million NFS reads is what makes media streaming and *arr library scans feel fast. Shrinking the
VM shrinks ARC proportionally.

## Access

**SSH** is enabled, key-only. Password authentication is off for *all* users — the server offers
`publickey` alone (verified, not just read from the config):

```
PermitRootLogin without-password
PubkeyAuthentication yes
ChallengeResponseAuthentication no
```

Recovery if the key is ever lost: the web UI, or the Proxmox console for VM 201. Neither depends
on SSH.

**SNMP** is enabled for monitoring — see [monitoring README](../../199-raspi5/docker/monitoring/README.md#snmp-exporter--truenas).

> **Gotcha:** on TrueNAS Core, changing SNMP settings in the UI does not reliably rewrite
> `/etc/local/snmpd.conf`. The service can run happily while serving a stale community string, and
> queries just time out with no error anywhere. If SNMP stops answering, restart the service:
> `midclt call service.restart snmp`.

## Setup

1. [Enable IOMMU on Proxmox](../README.md#iommu-setup-pci-passthrough-for-hba) and pass through the LSI 9211-8i HBA.
2. Create VM with specs above (disable ballooning under Options).
3. Install TrueNAS Core 13 from ISO.
3. Configure ZFS pool via **Storage → Pools** in the TrueNAS UI.
4. Create NFS shares via **Sharing → Unix Shares (NFS)**.
5. Enable SSH: **System Settings → Services → SSH** (password auth off), then add the public key
   under **Accounts → Users → root → Authorized Keys**.
6. Enable SNMP: **System Settings → Services → SNMP**, set a community string, then restart the
   service so the config is actually written.

## Setup

1. [Enable IOMMU on Proxmox](../README.md#iommu-setup-pci-passthrough-for-hba) and pass through the LSI 9211-8i HBA.
2. Create VM with specs above (disable ballooning under Options).
3. Install TrueNAS Core 13 from ISO.
3. Configure ZFS pool via **Storage → Pools** in the TrueNAS UI.
4. Create NFS shares via **Sharing → Unix Shares (NFS)**.

## NFS Exports

| Dataset | Mount path on guest | Consumer |
|---|---|---|
| `Vault/Downloads` | `/mnt/nfs/downloads` | starr-ct (212) |
| `Vault/Media` | `/mnt/nfs/media` | starr-ct (212), plex-ct (213) |
| `Vault/RecycleBin` | `/mnt/nfs/recycle-bin` | starr-ct (212) |
| `Vault/Games` | `/mnt/nfs/games` | starr-ct (212) |
| `Vault/Nextcloud` | `/mnt/nfs/nextcloud` | cloud-ct (214) |
| `Vault/Immich` | `/mnt/nfs/immich` | cloud-ct (214) |
| `Vault/Paperless` | `/mnt/nfs/paperless` | cloud-ct (214) |

> `downloads` and `media` are separate filesystems, so **hardlinks between them do not work** —
> staging media is a copy, never a move.

See [ZFS / NFS mount guide](../../guides/zfs-mount.md) for mounting on Linux VMs.
