# Nextcloud — DECOMMISSIONED (not deployed)

> **This stack is retained for reference only and is not running anywhere.**
> Decommissioned 2026-08-16. Do not `docker compose up` this without reading the note below.

Self-hosted file sync and collaboration platform. Includes Collabora Online for in-browser document editing.

## Why it was retired

An audit of actual usage found almost nothing in it. Of 12 GB on disk, ~12 GB was preview cache and
deleted files; **live user data was ~23 MB**, mostly Nextcloud's own sample documents.

| Use case | What was actually there | Covered by |
|---|---|---|
| Photos / video | — | **Immich** |
| Documents | 4 files, all stock samples | **Paperless-ngx** |
| Files / sync | 67 entries, mostly samples, nothing newer than 2026-04 | not a real use case here |
| Notes | **0 notes** | — |
| Calendar | 8 calendars, **6 events** | — |
| Contacts | **6 contacts** | — |
| **Deck (kanban)** | the only real data | **migrated to Vikunja** |

The Deck boards were the one thing worth keeping. All non-sample cards were migrated into Vikunja,
labelled and with their original board and column recorded, before this stack was removed.

## What was removed

- All four containers (`nextcloud`, `nextcloud_db`, `nextcloud_redis`, `collabora`)
- The `nextcloud` and `collabora` Traefik routers and services
- The `*/5 * * * *` cron entry on the `cloud` user's crontab

## What was kept

- **This compose file and README**, for reference — including the upgrade notes below, which
  document the linuxserver image-layout trap that is easy to rediscover the hard way.
- **A full backup** at `~/nextcloud-decom-20260816/` on cloud-ct: 29 MB database dump, 127 MB
  archive of live user files, the deployed compose, and the `.env`.
- **The NFS data at `/mnt/nfs/nextcloud`** (TrueNAS `Vault/Nextcloud`) is untouched and still on
  disk. Deleting it is a separate, deliberate decision.

## If you ever redeploy it

The database and files are in the backup above. Restore the dump into a fresh MariaDB before
starting the app, and be aware the version pin below still matters.

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

---

# Reference: original deployment notes

_Retained from the CT README when this stack was decommissioned. Historical — nothing below is live._

## Migration notes — VM 204 → LXC 214

VM 204 had been silently switched from bind mounts to **Docker named volumes** for Nextcloud's `/config`, `/db`, and `/redis`. A naïve `rsync ~/docker/` only captured stale leftover data — the live state lives in `/var/lib/docker/volumes/nextcloud_nextcloud_{config,db,redis}/_data/`.

If you ever need to redo this migration: enable root SSH on the source VM, then rsync from the **named volume paths** (not `~/docker/...`):

```bash
# As root on the LXC target
rsync -avh root@<source-vm>:/var/lib/docker/volumes/nextcloud_nextcloud_config/_data/ ~/docker/nextcloud/config/
rsync -avh root@<source-vm>:/var/lib/docker/volumes/nextcloud_nextcloud_db/_data/ ~/docker/nextcloud/db/
```

The compose in this repo uses bind mounts (`./config`, `./db`) so this trap shouldn't recur.

## NextCloud — post-install config

Edit `/config/www/nextcloud/config/config.php` inside the array:

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

Install on the host crontab (`crontab -e` as the `cloud` user):

```
*/5 * * * * docker exec -u abc nextcloud php /app/www/public/cron.php
```

Note: `cron.php` is a standalone script, **not** an `occ` subcommand.

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

### Upgrading Nextcloud

The compose pins to `lscr.io/linuxserver/nextcloud:33.0.5` rather than `:latest`. **Don't unpin.** Linuxserver refactored the image layout between NC 33 and NC 34 (app code moved out of `/config/www/nextcloud/` into `/app/www/public/`), and an unattended `:latest` pull will silently break install detection. Linuxserver also doesn't ship rolling minor tags (no `:33` or `:33.0`), so the only way to get patches automatically is `:latest`, which is what we're avoiding.

Upgrade workflow (run periodically, e.g. monthly):

```bash
# 1. See what's available
curl -s "https://registry.hub.docker.com/v2/repositories/linuxserver/nextcloud/tags?page_size=20" | \
  python3 -c "import sys,json; [print(t['name']) for t in json.load(sys.stdin)['results']]"

# 2. Snapshot before touching anything — easy rollback
ssh root@192.168.1.200 'zfs snapshot local-nvme/subvol-214-disk-0@pre-nc-upgrade'

# 3. Bump the tag in compose. Stay within the major (33.0.X → 33.0.Y) first.
sed -i 's|nextcloud:33.0.5|nextcloud:33.0.6|' docker-compose.yaml

# 4. Pull + restart
docker compose pull nextcloud
docker compose up -d nextcloud

# 5. Run migrations if needed (occ tells you)
docker exec -u abc nextcloud php /app/www/public/occ upgrade
docker exec -u abc nextcloud php /app/www/public/occ status   # confirm installed: true

# 6. Test the UI + apps, then commit the bump
```

**Major-version jumps (33 → 34)** are a separate exercise. Read the Nextcloud release notes for breaking changes, verify your installed apps support the new version, and plan for downtime. The same snapshot/pull/`occ upgrade` flow applies, but expect to spend longer validating apps and the new image layout.

Rollback if something goes wrong:

```bash
ssh root@192.168.1.200 'pct stop 214 && zfs rollback local-nvme/subvol-214-disk-0@pre-nc-upgrade && pct start 214'
```
