# 214 — LXC: Cloud (Container)

**IP:** 192.168.1.204 (took over from VM 204 after migration)
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

> Migrated from VM 204 to remove full-OS overhead and put MariaDB / SQLite databases on the fast local NVMe pool.

## Role

Self-hosted cloud services: password manager, photo sync, document management (with local-LLM
enrichment against Ollama on `jarvis`), recipes, and task management.

> **Densest host in the lab.** 23 containers across 8 stacks. Right-sizing this CT is tracked
> separately — see [Resource allocation](../README.md#resource-allocation).

## Setup

See [guides/lxc-docker.md](../../guides/lxc-docker.md) for the base LXC + Docker setup procedure.

LXC config in `/etc/pve/lxc/214.conf` on the Proxmox host (no special device passthrough needed — unlike starr/plex):

```
features: mount=nfs,nesting=1,fuse=1
lxc.apparmor.profile: unconfined
```

1. Create privileged LXC in Proxmox UI on `local-nvme` storage (see guide)
2. Add NFS passthrough + AppArmor unconfined to LXC config
3. Install Docker with fuse-overlayfs storage driver
4. Create `cloud` user (uid 1000)
5. Mount NFS share from TrueNAS (Nextcloud data only)
6. Deploy stacks

## Docker Stacks

| Folder | Services | Host Port |
|---|---|---|
| [docker/portainer-agent/](docker/portainer-agent/) | Portainer Edge Agent | — |
| [docker/monitoring-agent/](docker/monitoring-agent/) | Promtail, node-exporter, cAdvisor | 9080 (cadvisor) |
| [docker/vaultwarden/](docker/vaultwarden/) | VaultWarden | 8082 → 80 |
| [docker/mealie/](docker/mealie/) | Mealie recipe manager | 9000 |
| [docker/immich/](docker/immich/) | Immich server, machine-learning, PostgreSQL, Redis | 2283 |
| [docker/paperless/](docker/paperless/) | Paperless-ngx, PostgreSQL, Redis broker, Gotenberg, Tika, Paperless-AI, Paperless-GPT | 8000 (ngx), 8080 (gpt), 3000 (ai) |
| [docker/vikunja/](docker/vikunja/) | Vikunja, PostgreSQL | 3456 |
| [docker/nextcloud/](docker/nextcloud/) | NextCloud, MariaDB, Redis, Collabora | 8443 → 443, 9980 (collabora) |

> **Nextcloud is slated for decommissioning.** Immich now covers photos and Paperless-ngx covers
> documents, which were the reasons it was kept. The plan is to stop the stack on this CT and
> retain `docker/nextcloud/` in the repo as reference-only, non-deployed. Not yet actioned — the
> stack is still running as documented above.

Traefik on 199 routes traffic via file provider — see `199-raspi5/docker/traefik/data/config.yml`.

## NFS Mounts

```
192.168.1.201:/mnt/Vault/Nextcloud  /mnt/nfs/nextcloud  nfs  defaults  0  0
192.168.1.201:/mnt/Vault/Immich     /mnt/nfs/immich     nfs  defaults  0  0
192.168.1.201:/mnt/Vault/Paperless  /mnt/nfs/paperless  nfs  defaults  0  0
```

NFS access requires enabling the `mount` feature in LXC Options → Features in the Proxmox UI.

## TrueNAS — NFS dataset setup

One dataset per bulk-data app (Nextcloud, Immich, Paperless). **Databases never live on NFS** —
MariaDB and the three PostgreSQL instances all use local bind mounts (`./db`) on the NVMe rootfs,
for speed and to avoid file-locking problems over NFS.

```bash
# In TrueNAS Shell — set ownership to uid=1000 (matches cloud user and PUID in compose)
chown -R 1000:1000 /mnt/<pool>/Nextcloud
chmod -R 750 /mnt/<pool>/Nextcloud
```

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

## VaultWarden — post-install

1. Temporarily set `SIGNUPS_ALLOWED=true`, restart, create your account.
2. Set `SIGNUPS_ALLOWED=false` and restart:
   ```bash
   docker compose up -d
   ```
3. Use any Bitwarden-compatible client (iOS, Android, browser extension) — point server to `https://vaultwarden.local.wilfredtuscano.com`.
