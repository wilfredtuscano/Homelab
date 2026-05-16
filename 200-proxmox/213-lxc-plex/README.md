# 213 — LXC: Plex (Container)

**IP:** 192.168.1.213 (temporary — will be reassigned to 192.168.1.203 after VM decommission)
**OS:** Ubuntu 22.04 LTS
**Host:** Proxmox (192.168.1.200)
**Type:** Privileged LXC container

## LXC Specs

| Resource | Value |
|---|---|
| vCPU | 6 cores |
| RAM | 8 GB |
| Disk | 80 GB (local-zfs) |
| iGPU | Intel Xe (i7-13700K) via `/dev/dri` passthrough |

> Uses 8 GB instead of the previous VM's 16 GB — LXC has no full OS overhead.
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

## NFS Mount

```
192.168.1.201:/mnt/Vault/Media  /mnt/nfs/media  nfs  defaults  0  0
```

NFS access requires enabling the `mount` feature in LXC Options → Features in the Proxmox UI.
