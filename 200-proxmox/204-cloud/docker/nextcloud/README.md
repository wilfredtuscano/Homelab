# Nextcloud

Self-hosted file sync and collaboration platform. Includes Collabora Online for in-browser document editing.

## Services

| Service | Purpose |
|---------|---------|
| Nextcloud | Main application |
| MariaDB | Database backend |
| Redis | Session cache and file locking |
| Collabora | Online office document editor (Writer, Calc, Impress) |

## Access

| Interface | URL |
|-----------|-----|
| Nextcloud | `https://nextcloud.local.wilfredtuscano.com` |
| Collabora | `https://collabora.local.wilfredtuscano.com` |

## Setup

Create a `.env` file (gitignored):

```env
MARIADB_ROOT_PASSWORD=<root-password>
MARIADB_PASSWORD=<nextcloud-db-password>
```

## Volume mounts

| Container path | Host path | Purpose |
|----------------|-----------|---------|
| `/config` | `./config` | Nextcloud config and apps |
| `/data` | `/mnt/nfs/nextcloud` | User files (NFS-backed) |
| `/var/lib/mysql` | `./db` | MariaDB data |

## Notes

- All services run on an isolated `nextcloud_internal` network — only Nextcloud is exposed via Traefik
- Collabora is configured to trust requests from `nextcloud.local.wilfredtuscano.com`
- SSL termination is handled by Traefik (`ssl.termination=true`, `ssl.enable=false` inside the container)
- Enable the **Nextcloud Office** app inside Nextcloud and point it to `https://collabora.local.wilfredtuscano.com`
