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

1. [Set a static IP](../../guides/static-ip.md)
2. [Install Docker](../../guides/docker-install.md)
3. [Mount NFS share from TrueNAS](../../guides/zfs-mount.md)
4. Deploy stacks:
   1. `docker/portainer/`
   2. `docker/plex/`

## Docker Stacks

| Folder | Services |
|---|---|
| [docker/portainer/](docker/portainer/) | Portainer Edge Agent |
| [docker/plex/](docker/plex/) | Plex |
