# 212 — LXC: Starr (Container)

**IP:** 192.168.1.202 (took over from VM 202 after migration)
**OS:** Ubuntu 22.04 LTS
**Host:** Proxmox (192.168.1.200)
**Type:** Privileged LXC container

## LXC Specs

| Resource | Value |
|---|---|
| vCPU | 2 cores |
| RAM | 6 GB |
| Swap | 512 MB |
| Disk | 80 GB (local-nvme — Samsung PM9A1 1TB) |
| TUN device | `/dev/net/tun` passthrough (for Gluetun WireGuard) |

> Reduced from 4 cores / 8 GB on 2026-08-10 — 30 days of data showed a peak of 1.34 cores and
> 3.08 GB. If qBittorrent behaviour changes (many simultaneous hash checks), this is the first
> guest to revisit.

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

## Host tools: ffprobe and ffmpeg

Media management on this host reads file metadata (codec, HDR / Dolby Vision, bitrate, audio
languages) and grabs sample frames, so `ffprobe` and `ffmpeg` are installed on the host, from
Jellyfin's apt repository. The `jellyfin-ffmpeg8` package is a self-contained media-server build
under `/usr/lib/jellyfin-ffmpeg/`; it does not replace system libraries, and the routine
`apt upgrade` keeps it current. Ubuntu 22.04's own `ffmpeg` is 4.4 (2021) and pulls in about 160
packages.

Run as root (the login user has no sudo here, so from the Proxmox host: `pct exec 212 -- sh -c '...'`):

```bash
install -d -m 0755 /etc/apt/keyrings
curl -fsSL https://repo.jellyfin.org/jellyfin_team.gpg.key -o /etc/apt/keyrings/jellyfin.asc
cat > /etc/apt/sources.list.d/jellyfin.sources <<'SRC'
Types: deb
URIs: https://repo.jellyfin.org/ubuntu
Suites: jammy
Components: main
Architectures: amd64
Signed-By: /etc/apt/keyrings/jellyfin.asc
SRC
apt-get update
apt-get install -y --no-install-recommends jellyfin-ffmpeg8
ln -sfn /usr/lib/jellyfin-ffmpeg/ffmpeg  /usr/local/bin/ffmpeg
ln -sfn /usr/lib/jellyfin-ffmpeg/ffprobe /usr/local/bin/ffprobe
```

The key is kept ASCII-armoured (`.asc`), which apt accepts directly, because the host has no `gpg`.
Check: `ffprobe -version` reports `8.1.3-Jellyfin` (or newer). Reading headers needs no GPU, and
this host has none (no `/dev/dri`). It is not a transcoding host: two cores decode 4K HEVC at
about real time. Bulk re-encoding is planned for the GPU host.

## Docker Stacks

| Folder | Services |
|---|---|
| [docker/portainer-agent/](docker/portainer-agent/) | Portainer Edge Agent |
| [docker/vpn/](docker/vpn/) | Gluetun (Surfshark WireGuard), qBittorrent |
| [docker/starr/](docker/starr/) | Sonarr, Radarr, Prowlarr, Lidarr, Readarr, FlareSolverr, Metube |
| [docker/monitoring-agent/](docker/monitoring-agent/) | Promtail, node-exporter, cAdvisor |

## NFS Mounts

```
192.168.1.201:/mnt/Vault/Downloads    /mnt/nfs/downloads     nfs  defaults,_netdev,retry=15,x-systemd.mount-timeout=20min  0  0
192.168.1.201:/mnt/Vault/Media        /mnt/nfs/media         nfs  defaults,_netdev,retry=15,x-systemd.mount-timeout=20min  0  0
192.168.1.201:/mnt/Vault/RecycleBin   /mnt/nfs/recycle-bin   nfs  defaults,_netdev,retry=15,x-systemd.mount-timeout=20min  0  0
192.168.1.201:/mnt/Vault/Games        /mnt/nfs/games         nfs  defaults,_netdev,retry=15,x-systemd.mount-timeout=20min  0  0
```

Options: `_netdev,retry=15,x-systemd.mount-timeout=20min`. A share that is not ready at boot keeps
retrying for up to 15 minutes instead of failing once.

**Docker waits for these mounts.** `/etc/systemd/system/docker.service.d/nfs-mounts.conf`:

```ini
[Unit]
RequiresMountsFor=/mnt/nfs/downloads /mnt/nfs/media /mnt/nfs/recycle-bin
```

`/mnt/nfs/games` is deliberately not listed: no container uses it (it is mounted for file work
only), so a problem with that share should not hold back the *arr apps and qBittorrent.

Without it Docker starts as soon as the network is up. If TrueNAS is not serving NFS yet, the apps
start against the **empty local mountpoint directories** and write there instead of the NAS. With
it, a slow or absent TrueNAS only delays the apps. `RequiresMountsFor` implies `Requires=`, so
unmounting a listed share also stops Docker: remove it from the drop-in first.
qBittorrent additionally waits for a healthy VPN tunnel: see `docker/vpn/README.md` (vpn-watchdog).
Apply with `systemctl daemon-reload`; check with `systemctl show docker -p Requires`.

NFS access requires enabling the `mount` feature in LXC Options → Features in the Proxmox UI.
