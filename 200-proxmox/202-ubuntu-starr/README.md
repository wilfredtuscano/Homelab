# 202 — Ubuntu Server: Starr (VM)

**IP:** 192.168.1.202
**OS:** Ubuntu Server
**Host:** Proxmox (192.168.1.200)

## VM Specs

| Resource | Value |
|---|---|
| vCPU | 4 cores |
| RAM | 8 GB |

## Role

Runs the *arr media management stack and a VPN-isolated download stack.

## Setup

1. [Enable SSH server](../../guides/ssh.md)
2. [Set a static IP](../../guides/static-ip.md)
3. [Install Docker](../../guides/docker-install.md)
4. [Mount NFS share from TrueNAS](../../guides/zfs-mount.md)
5. Deploy stacks:
   1. `docker/portainer/` — see [Portainer Edge Agent guide](../../guides/portainer-edge-agent.md)
   2. `docker/starr/`
   3. `docker/vpn/`

## Docker Stacks

| Folder | Services |
|---|---|
| [docker/portainer/](docker/portainer/) | Portainer Edge Agent |
| [docker/starr/](docker/starr/) | Sonarr, Radarr, Prowlarr, Lidarr, Readarr, Bazarr |
| [docker/vpn/](docker/vpn/) | Gluetun (VPN), qBittorrent, Firefox |
