# 204 — Ubuntu Server: Cloud (VM)

**IP:** 192.168.1.204
**OS:** Ubuntu Server
**Host:** Proxmox (192.168.1.200)

## VM Specs

| Resource | Value |
|---|---|
| vCPU | 4 cores |
| RAM | 8 GB |

## Role

Planned self-hosted cloud services.

## Planned Services

- VaultWarden (Bitwarden-compatible password manager)
- Nextcloud (file sync / cloud storage)

## Docker Stacks

| Folder | Services |
|---|---|
| `docker/portainer/` | Portainer Edge Agent |
