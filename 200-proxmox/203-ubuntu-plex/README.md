# 203 — Ubuntu Server: Plex (VM)

**IP:** 192.168.1.203
**OS:** Ubuntu Server
**Host:** Proxmox (192.168.1.200)

## VM Specs

| Resource | Value |
|---|---|
| vCPU | 6 cores |
| RAM | 16 GB |

## Role

Runs Plex Media Server, consuming media from TrueNAS over NFS.

## Setup

1. [Enable SSH server](../../guides/ssh.md)
2. [Set a static IP](../../guides/static-ip.md)
3. [Install Docker](../../guides/docker-install.md)
4. [Mount NFS share from TrueNAS](../../guides/zfs-mount.md)
5. Deploy stacks:
   1. `docker/portainer/` — see [Portainer Edge Agent guide](../../guides/portainer-edge-agent.md)
   2. `docker/plex/`

## Docker Stacks

| Folder | Services |
|---|---|
| [docker/portainer/](docker/portainer/) | Portainer Edge Agent |
| [docker/plex/](docker/plex/) | Plex |
