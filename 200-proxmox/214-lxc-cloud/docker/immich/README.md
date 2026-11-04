# Immich

Self-hosted photo and video library. Replaces Google Photos and Nextcloud Photos as the primary photo/video experience for household users.

## Services

| Service | Purpose |
|---------|---------|
| immich-server | Web UI and API |
| immich-machine-learning | CLIP-based search + face recognition |
| immich_redis | Session cache and job queue |
| immich_db | Postgres 14 with vectorchord extension for embeddings |

## Access

| Interface | URL |
|-----------|-----|
| Web UI + API | `http://cloud-ct:2283` (add Traefik route once verified) |

## Prerequisites

1. **TrueNAS dataset**: `/mnt/Vault/Immich` with NFS share allowing cloud-ct (`mapall_user=cloud, mapall_group=cloud`).
2. **NFS mount on cloud-ct** at `/mnt/nfs/immich`. Add to `/etc/fstab`:

   ```
   <truenas-ip>:/mnt/Vault/Immich  /mnt/nfs/immich  nfs  defaults,_netdev  0  0
   ```

   Then `sudo mkdir -p /mnt/nfs/immich && sudo mount -a`.

3. **Verify image tags** against Immich's current release compose before first `docker compose up`:
   `https://github.com/immich-app/immich/blob/main/docker/docker-compose.yml`

## Setup

Create a `.env` file (gitignored):

```env
DB_PASSWORD=<strong-postgres-password>
```

Then:

```bash
docker compose up -d
```

First boot pulls all images (~3 GB) and initializes Postgres. Watch `docker compose logs -f immich-server` until you see `Immich Server is listening`.

## Volume mounts

| Container path | Host path | Purpose |
|----------------|-----------|---------|
| `/usr/src/app/upload` | `/mnt/nfs/immich` (NFS) | Photo library, thumbs, backups |
| `/cache` (ML) | `./ml-cache` | Downloaded CLIP/face-rec models (~2 GB) |
| `/var/lib/postgresql/data` | `./db` | Postgres data — **must be local**, NFS+Postgres corrupts |

## Users

Bootstrap: first visit to `http://cloud-ct:2283` prompts to create the admin account. Then create one Immich user per household member with **the same username as their Nextcloud account** (e.g., `Wilfred`, `Sharal`) so future integrations line up.

Under **Administration → Users**, create each user with:
- Storage quota (optional — default is unlimited)
- Storage label (matches subdirectory under `/mnt/nfs/immich/library/`)

## Bulk import from existing Nextcloud photos

Existing photos live under `/mnt/nfs/nextcloud/<user>/files/Photos/`. Import them into Immich preserving EXIF timestamps:

```bash
# One-time: install the CLI on cloud-ct
sudo npm install -g @immich/cli

# Generate an API key per user under Account Settings → API Keys
immich login-key http://cloud-ct:2283/api <api-key>

# Bulk upload, tagged into a migration album for easy verification
immich upload \
  --album-name "Migrated from Nextcloud" \
  --recursive \
  /mnt/nfs/nextcloud/Wilfred/files/Photos/
```

Repeat per user with their own API key.

## Verification checklist (before deleting Nextcloud copies)

- [ ] Immich reports the expected photo count under **Administration → Statistics** (compare against `find /mnt/nfs/nextcloud/<user>/files/Photos -type f | wc -l`)
- [ ] Sample of 5 random photos: EXIF timestamps preserved (spot-check dates in timeline)
- [ ] CLIP search works: query something specific like "beach" or "car"
- [ ] Mobile Immich app installed, backup enabled, new phone photo lands in Immich
- [ ] Cloud-ct memory usage steady, no OOM (`docker stats`, watch for 10 minutes under load)

## Post-migration cleanup

Once verified:

1. Disable Nextcloud photo apps (photos stay on disk; only the UI hides):
   ```bash
   docker exec -u abc nextcloud php /app/www/public/occ app:disable photos
   docker exec -u abc nextcloud php /app/www/public/occ app:disable memories
   docker exec -u abc nextcloud php /app/www/public/occ app:disable recognize
   ```
2. Delete the migrated photo folders on the NFS mount:
   ```bash
   sudo rm -rf /mnt/nfs/nextcloud/Wilfred/files/Photos
   sudo rm -rf /mnt/nfs/nextcloud/Sharal/files/Photos
   ```
3. Rescan Nextcloud so the file index matches disk:
   ```bash
   docker exec -u abc nextcloud php /app/www/public/occ files:scan --all
   ```
4. Run preview generation on the doc-only remainder (was previously blocked by 50 GB of photos):
   ```bash
   docker exec -u abc nextcloud php /app/www/public/occ preview:generate-all -vvv
   ```

## Upgrading Immich

All four images are pinned: `immich-server` and `immich-machine-learning` to an exact release
(`v3.3.5`), and the database and cache images to the exact digests in upstream's compose for that
release. The ML container on jarvis (`205-gmktek/docker/immich-ml/`) carries the matching
`-rocm` tag. **Bump them together**, never one at a time, or server and ML can end up on
different versions.

```bash
# 1. Read the release notes from the current version up to the target.
# 2. Diff upstream's docker/docker-compose.yml at the target tag against this file, and take
#    any database / cache image (with digest) and shm_size changes from it.
# 3. Back up first:
docker exec immich_db pg_dumpall --clean --if-exists -U immich | gzip > ~/immich-dumpall.sql.gz
# 4. Pull, then recreate:
cd ~/docker/immich && docker compose pull && docker compose up -d
```

**Vector extension upgrades are automatic.** When the database image carries a newer VectorChord,
Immich runs `ALTER EXTENSION vchord UPDATE` and reindexes `clip_index` and `face_index` at startup,
because the `immich` DB user is superuser. Watch for `Updating VectorChord extension` in the
server log. After that the previous database image refuses to start, so **rollback is a restore
or a snapshot, not a tag change**. On the Proxmox host, take the snapshot with
`zfs snapshot local-nvme/subvol-214-disk-0@<name>`, **not** `pct snapshot`: this container has
`fuse=1`, and `pct snapshot` deadlocked it frozen.

Postgres major-version bumps (e.g. 14 to 16) require a data migration; follow Immich's release notes
carefully.

**Docker in this LXC needs `security_opt: apparmor=unconfined`** on every service. Upstream's
compose does not include it; add it to any new service taken from there.

## Notes

- All services run on an isolated `immich_internal` network — only the server is exposed
- Machine-learning container downloads CLIP + face-rec models on first job; expect ~10 minutes of high CPU on the first full library scan
- NFS is fine for the photo library; **never** move `./db` or `./ml-cache` onto NFS (postgres corruption, model load races)
- The Nextcloud photo apps stay installed but disabled — users who explore the web UI won't see stale photo timelines
