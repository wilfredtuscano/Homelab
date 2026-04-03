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

Self-hosted cloud services: password manager and file/photo sync.

## Setup

1. [Enable SSH server](../../guides/ssh.md)
2. [Set a static IP](../../guides/static-ip.md)
3. [Install Docker](../../guides/docker-install.md)
4. Mount NFS share from TrueNAS for NextCloud data:
   ```bash
   sudo apt install -y nfs-common
   sudo mkdir -p /mnt/nfs/nextcloud
   sudo systemctl daemon-reload
   # Add to /etc/fstab:
   # 192.168.1.201:/mnt/<pool>/Nextcloud  /mnt/nfs/nextcloud  nfs  defaults,_netdev  0  0
   sudo mount -a
   ```
5. Deploy stacks:
   1. `docker/portainer/` — see [Portainer Edge Agent guide](../../guides/portainer-edge-agent.md)
   2. `docker/vaultwarden/`
   3. `docker/nextcloud/`

## Docker Stacks

| Folder | Services | Host Port |
|---|---|---|
| [docker/portainer/](docker/portainer/) | Portainer Edge Agent | — |
| [docker/vaultwarden/](docker/vaultwarden/) | VaultWarden | 8082 → 80 |
| [docker/nextcloud/](docker/nextcloud/) | NextCloud, MariaDB, Redis, Collabora | 8443 → 443, 9980 → 9980 |

Traefik on 199 routes traffic via file provider — see `199-raspi5/docker/traefik/data/config.yml`.

## TrueNAS — NFS dataset setup

Only one dataset is needed for NextCloud. MariaDB runs on a local bind mount (`./db`).

```bash
# In TrueNAS Shell — set ownership to uid=1000 (matches VM user and PUID in compose)
chown -R 1000:1000 /mnt/<pool>/Nextcloud
chmod -R 750 /mnt/<pool>/Nextcloud
```


## NextCloud — post-install config

After first-run wizard, add to `/config/www/nextcloud/config/config.php` inside the array:

```php
'trusted_proxies' => ['192.168.1.199'],
'overwriteprotocol' => 'https',
'overwritehost' => 'nextcloud.local.wilfredtuscano.com',
```

### Redis caching

```php
'memcache.local' => '\\OC\\Memcache\\Redis',
'memcache.distributed' => '\\OC\\Memcache\\Redis',
'memcache.locking' => '\\OC\\Memcache\\Redis',
'redis' => [
  'host' => 'nextcloud_redis',
  'port' => 6379,
],
```

Restart after editing config.php:
```bash
docker compose restart nextcloud
```

### Background cron

In NextCloud Admin → Basic Settings → Background jobs → select **Cron**.

Add to VM crontab (`crontab -e`):
```
*/5 * * * * docker exec -u abc nextcloud php /app/www/public/occ cron.php
```

### Pre-generate image previews

Install the **Preview Generator** app first (Admin → Apps), then run:

```bash
docker exec -u abc nextcloud php /app/www/public/occ preview:generate-all -vvv
```

Runs once — takes a while for large libraries. Safe to run in background while using NextCloud.

### Recommended apps to install

| App | Purpose |
|---|---|
| Memories | Photos — timeline, map, face recognition |
| Recognize | AI face/object tagging |
| Preview Generator | Pre-generates thumbnails (critical for performance) |
| Nextcloud Office | In-browser DOCX/XLSX/PPTX editing (requires Collabora container) |
| Calendar | CalDAV sync |
| Contacts | CardDAV sync |
| Tasks | To-do lists |
| Talk | Video calls + chat |
| Notes | Markdown notes |
| External Storage | Mount Google Drive, S3, SMB |
| Social Login | OAuth via Google account |

### Nextcloud Office (Collabora)

The built-in CODE server is incompatible with the linuxserver image (Alpine/musl). Collabora runs as a separate container in the same compose stack.

After `docker compose up -d`, configure in NextCloud:
Admin → Administration Settings → Nextcloud Office → **Use your own server** → `https://collabora.local.wilfredtuscano.com`

## VaultWarden — post-install

1. Temporarily set `SIGNUPS_ALLOWED=true`, restart, create your account.
2. Set `SIGNUPS_ALLOWED=false` and restart:
   ```bash
   docker compose up -d
   ```
3. Use any Bitwarden-compatible client (iOS, Android, browser extension) — point server to `https://vaultwarden.local.wilfredtuscano.com`.
