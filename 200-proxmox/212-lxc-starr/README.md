# 212 — LXC: Starr (Container)

**IP:** 192.168.1.202 (took over from VM 202 after migration)
**OS:** Ubuntu 22.04 LTS
**Host:** Proxmox (192.168.1.200)
**Type:** Privileged LXC container

## LXC Specs

| Resource | Value |
|---|---|
| vCPU | 4 cores |
| RAM | 8 GB |
| Swap | 512 MB |
| Disk | 80 GB (local-nvme — Samsung PM9A1 1TB) |
| TUN device | `/dev/net/tun` passthrough (for Gluetun WireGuard) |

> Migrated from VM 202 to remove the full-OS overhead and stop swap pressure caused by qBittorrent's OS page cache. LXC shares the host kernel, so memory is used directly without VM ballooning.

## Role

Runs the *arr media management stack and a VPN-isolated download stack (Gluetun + qBittorrent).

## Setup

See [guides/lxc-docker.md](../../guides/lxc-docker.md) for the base LXC + Docker setup procedure.

Extra config specific to this CT (in `/etc/pve/lxc/212.conf` on the Proxmox host) — adds `/dev/net/tun` for the VPN:

```
features: mount=nfs,nesting=1,fuse=1
lxc.apparmor.profile: unconfined
lxc.cgroup2.devices.allow: c 10:200 rwm
lxc.mount.entry: /dev/net/tun dev/net/tun none bind,create=file
```

1. Create privileged LXC in Proxmox UI (see guide)
2. Add TUN + NFS passthrough to LXC config
3. Install Docker with fuse-overlayfs storage driver
4. Create `starr` user (uid 1000)
5. Mount NFS shares from TrueNAS
6. Deploy stacks

## Docker Stacks

| Folder | Services |
|---|---|
| [docker/portainer-agent/](docker/portainer-agent/) | Portainer Edge Agent |
| [docker/vpn/](docker/vpn/) | Gluetun (Surfshark WireGuard), qBittorrent |
| [docker/starr/](docker/starr/) | Sonarr, Radarr, Prowlarr, Lidarr, Readarr, FlareSolverr, Metube |
| [docker/monitoring-agent/](docker/monitoring-agent/) | Promtail, node-exporter, cAdvisor |

## NFS Mounts

```
192.168.1.201:/mnt/Vault/Downloads    /mnt/nfs/downloads     nfs  defaults  0  0
192.168.1.201:/mnt/Vault/Media        /mnt/nfs/media         nfs  defaults  0  0
192.168.1.201:/mnt/Vault/RecycleBin   /mnt/nfs/recycle-bin   nfs  defaults  0  0
192.168.1.201:/mnt/Vault/Games        /mnt/nfs/games         nfs  defaults  0  0
```

NFS access requires enabling the `mount` feature in LXC Options → Features in the Proxmox UI.
