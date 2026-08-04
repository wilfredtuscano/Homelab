# Paperless-ngx

Self-hosted document management for the household — scan/drop a document, it gets
OCR'd, auto-classified, and filed. Replaces paper folders and scattered PDFs, and
is the ingestion front end for the eventual document RAG.

## Services

| Service | Image | Role |
|---------|-------|------|
| webserver | `paperless-ngx` | Web UI, API, OCR (Tesseract/ocrmypdf), consumer, classifier |
| db | `postgres:16` | Documents, correspondents, tags, users |
| broker | `redis:7` | Async task queue for the consumer |
| gotenberg | `gotenberg:8` | Renders Office docs / emails → PDF for archiving + OCR |
| tika | `apache/tika` | Text extraction from Office/odd formats |
| paperless-ai *(profile `ai`)* | `clusterzx/paperless-ai` | LLM auto title/tags/correspondent suggestions |
| paperless-gpt *(profile `ai`)* | `icereed/paperless-gpt` | Vision-model OCR for scans/handwriting Tesseract fails on |

All inference is offloaded to Ollama on **jarvis** (`https://ollama.local.wilfredtuscano.com`);
cloud-ct has no GPU. See [`../../../205-gmktek/docker/ollama/`](../../../../205-gmktek/docker/ollama/README.md).

## Access

| Interface | URL |
|-----------|-----|
| Web UI + API | `https://paperless.local.wilfredtuscano.com` (Traefik → `192.168.1.204:8000`) |
| paperless-ai UI | `http://cloud-ct:3000` (add Traefik route once verified) |
| paperless-gpt UI | `http://cloud-ct:8080` (add Traefik route once verified) |

## Prerequisites

1. **TrueNAS dataset** `/mnt/Vault/Paperless`, owned `wtuscano:Admin` (UID/GID 1000),
   NFS-exported to cloud-ct — same settings as the Immich share. *(Done.)*
2. **NFS mount on cloud-ct** at `/mnt/nfs/paperless`. Add to `/etc/fstab`:

   ```
   <truenas-ip>:/mnt/Vault/Paperless  /mnt/nfs/paperless  nfs  defaults,_netdev  0  0
   ```

   Then `sudo mkdir -p /mnt/nfs/paperless/{media,inbox} && sudo mount -a`.
3. **Pi-hole DNS** record `paperless.local.wilfredtuscano.com` → `192.168.1.199` (Traefik). *(Done.)*

## Storage layout

| Container path | Host path | Purpose |
|----------------|-----------|---------|
| `/usr/src/paperless/media` | `/mnt/nfs/paperless/media` (NFS) | The document archive — Paperless nests `documents/{originals,archive,thumbnails}` here |
| `/usr/src/paperless/consume` | `/mnt/nfs/paperless/inbox` (NFS) | Drop zone — files dropped here get ingested |
| `/usr/src/paperless/data` | `./data` (local) | Search index + trained classifier model — regenerable |
| `/var/lib/postgresql/data` | `./db` (local) | Postgres — **must be local**, NFS+Postgres corrupts |
| redis | `./redis` (local) | Task queue state |

`inotify` doesn't fire over NFS, so the consumer runs in **polling** mode
(`PAPERLESS_CONSUMER_POLLING=30`) — a dropped file is picked up within ~30s.

## Setup

Create `.env` on cloud-ct from the template (gitignored — never commit it):

```bash
cp .env.example .env
# Fill POSTGRES_PASSWORD, PAPERLESS_SECRET_KEY, PAPERLESS_ADMIN_PASSWORD:
#   openssl rand -base64 24   # postgres password
#   openssl rand -base64 48   # secret key
```

Bring up the core stack:

```bash
docker compose up -d
docker compose logs -f webserver   # wait for "start worker" / listening on :8000
```

First boot creates the Postgres schema and the `PAPERLESS_ADMIN_USER` superuser.
Log in at `https://paperless.local.wilfredtuscano.com`.

## Users

Create one Paperless user per household member (**same username as their Nextcloud /
Immich account** — `Wilfred`, `Sharal`) under **Settings → Users & Groups**. Paperless
enforces per-document ownership, so each user only sees their own docs. This ownership
boundary is what the future RAG layer keys off for household isolation.

## AI add-ons (profile `ai`)

Only after the core stack is up and healthy.

### 0. Cap the context on jarvis's Ollama (one-time, **required**)

Large vision models default to a 128k context; with flash attention off that
inflates the attention compute graph past jarvis's VRAM, and the load fails with
`model requires more system memory (41.0 GiB) than is available`. jarvis carves
96 GB into VRAM leaving only ~30 GB system RAM, so there's no headroom to spill
into. Set a sane default on the Ollama box once (needs sudo; jarvis has no
passwordless sudo, so use `ssh -t`):

```bash
ssh -t jarvis "sudo bash -c 'cat > /etc/systemd/system/ollama.service.d/override.conf <<EOF
[Service]
Environment=\"OLLAMA_FLASH_ATTENTION=1\"
Environment=\"OLLAMA_CONTEXT_LENGTH=32768\"
EOF
systemctl daemon-reload && systemctl restart ollama'"
```

### 1. Pull the vision model on jarvis

```bash
ssh jarvis 'ollama pull qwen2.5vl:32b'
```

Ollama auto-unloads idle models after ~5 min, so the vision model only occupies
VRAM during an ingest and frees it afterward.

### 2. Create an API token, then start the AI services

Generate a DRF token for the admin superuser straight from the container — run it
as the `paperless` user (UID 1000) so the pre-flight system check can read the
NFS-backed dirs — then drop it into `.env` and bring the profile up:

```bash
docker compose exec -u paperless webserver python3 manage.py drf_create_token admin
# put the token in .env as PAPERLESS_API_TOKEN, then:
docker compose --profile ai up -d
```

### 3. Configure the tools

- **paperless-gpt** (`:8080`) is fully env-driven (see compose — token, Ollama URL,
  models). To vision-OCR a document, tag it **`paperless-gpt-ocr-auto`**: the worker
  picks it up within ~30s, replaces the content with the vision OCR, and removes the
  tag (applying `paperless-gpt-failed` if it errors 3×). Recreate the container after
  changing the token so it reloads env: `docker compose --profile ai up -d --force-recreate paperless-gpt`.
- **paperless-ai** (`:3000`) keeps its config in its own sqlite via a setup wizard,
  not the compose env: Paperless URL `http://webserver:8000`, the API token, provider
  **Ollama**, URL `https://ollama.local.wilfredtuscano.com`, model `qwen2.5vl:32b`
  (or a lighter text model like `mistral-small3.2:24b` for metadata).

### Verifying the work really runs on our Ollama

While a tagged document processes, on jarvis `ollama ps` shows the model resident
(`qwen2.5vl:32b … 100% GPU`), and paperless-gpt logs it explicitly:

```
msg="Successfully processed image" model="qwen2.5vl:32b" provider=ollama …
```

Vision OCR measurably beats Tesseract on scans — e.g. it corrected a challan amount
Tesseract misread (`1720.00` → `17220.00 INR`) and reconstructed the table layout.

> **Per-user permissions:** verify each AI tool respects Paperless document ownership
> before trusting it on the shared library — a tool that queries across all users would
> break household isolation. Test with a Sharal-owned doc while authed as Wilfred.

## Ingestion methods

- **Consume folder** — drop into `/mnt/nfs/paperless/inbox` from any host that mounts
  the NAS (or via a Nextcloud/Syncthing target pointed there).
- **Web upload** — drag onto the Paperless UI.
- **Mobile** — the Paperless share-target apps (e.g. Paperless Mobile) → share a phone
  scan straight into the consumer.
- **Email** *(optional, later)* — configure a mail account so forwarded e-bills auto-ingest.

## Upgrading Paperless

Pin `webserver` to a specific tag after first boot, then bump deliberately:

```bash
cd ~/docker/paperless
# Edit docker-compose.yml — change `:latest` to e.g. `:2.18.4`
docker compose pull
docker compose up -d
```

Postgres major bumps (16 → …) need a dump/restore — follow release notes.

## Notes

- Everything runs on the isolated `paperless` bridge network.
- `security_opt: apparmor=unconfined` is required for Docker inside the privileged LXC
  (same as Immich/Nextcloud here).
- `USERMAP_UID/GID=1000` makes the container write to the NFS media dir as
  `wtuscano:Admin` — without it, NFS root_squash blocks writes.
- The `ai` profile keeps the two community AI tools out of the default `up` — the core
  DMS stands alone and stays healthy even if an AI tool or jarvis is down.
