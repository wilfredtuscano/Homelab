# 213 — LXC: Plex (Container)

**IP:** 192.168.1.203 (took over from VM 203 after migration)
**OS:** Ubuntu 22.04 LTS
**Host:** Proxmox (192.168.1.200)
**Type:** Privileged LXC container

## LXC Specs

| Resource | Value |
|---|---|
| vCPU | 4 cores |
| RAM | 6 GB |
| Swap | 512 MB |
| Disk | 80 GB (local-nvme — Samsung PM9A1 1TB) |
| iGPU | Intel Xe (i7-13700K) via `/dev/dri` passthrough |

> Reduced from 8 GB to 6 GB on 2026-08-10 — 30 days of data showed a 2.19 GB peak working set.
> Deliberately **not** cut to 4 GB: page cache counts toward the LXC cgroup limit and Plex averages
> ~5 GB cached, so a tighter limit would force reclaim during streaming. Cores stay at 4 — the plex
> container alone peaked at 295% CPU during transcodes.
> iGPU passthrough works because LXC shares the Proxmox host kernel directly, unlike VMs which require SR-IOV or GVT-g (unsupported on 12th gen+ Intel).

## Role

Runs Plex Media Server with Intel QuickSync hardware transcoding, plus Audiobookshelf and Calibre-web for book/audiobook management.

## Setup

See [guides/lxc-docker.md](../../guides/lxc-docker.md) for the full LXC + Docker setup procedure.

1. Create privileged LXC in Proxmox UI (see guide)
2. Add iGPU and NFS passthrough to LXC config
3. Install Docker with fuse-overlayfs storage driver
4. Create `plex` user (uid 1000)
5. Mount NFS share from TrueNAS
6. Deploy stacks

## Docker Stacks

| Folder | Services |
|---|---|
| [docker/portainer-agent/](docker/portainer-agent/) | Portainer Edge Agent |
| [docker/plex/](docker/plex/) | Plex Media Server |
| [docker/audiobookshelf/](docker/audiobookshelf/) | Audiobookshelf |
| [docker/calibre-web/](docker/calibre-web/) | Calibre-web |
| [docker/monitoring-agent/](docker/monitoring-agent/) | Promtail, node-exporter, cAdvisor |

## NFS Mount

```
192.168.1.201:/mnt/Vault/Media  /mnt/nfs/media  nfs  defaults  0  0
```

NFS access requires enabling the `mount` feature in LXC Options → Features in the Proxmox UI.
