# Vikunja

Self-hosted project & task manager for `~/workspace` — the single place that tracks
projects, tasks, and timelines across Study, Fitness, JobSearch, personal projects,
Starr/media chores, etc. Designed to be **driven programmatically**: Claude Code,
launched from `~/workspace`, manages the whole workflow through an MCP server that
talks to Vikunja's REST API.

## Services

| Service | Image | Role |
|---------|-------|------|
| vikunja | `vikunja/vikunja` | API + web UI in one image (projects, tasks, labels, dates, kanban/list/Gantt) |
| db | `postgres:16` | Projects, tasks, users, tokens |

## Access

| Interface | URL |
|-----------|-----|
| Web UI + API | `https://vikunja.local.wilfredtuscano.com` (Traefik → `192.168.1.204:3456`) |
| API base | `https://vikunja.local.wilfredtuscano.com/api/v1` |

## Prerequisites

1. **Pi-hole DNS** record `vikunja.local.wilfredtuscano.com` → `192.168.1.199` (Traefik).
2. **Traefik route** (router + service) on raspi5 — added in `199-raspi5/docker/traefik/data/config.yml`.

## Storage layout

| Container path | Host path | Purpose |
|----------------|-----------|---------|
| `/app/vikunja/files` | `./files` (local) | Task attachments — must be owned by uid 1000 |
| `/var/lib/postgresql/data` | `./db` (local) | Postgres — **must be local**, never NFS |

## Setup

Create `.env` on cloud-ct from the template (gitignored — never commit it):

```bash
cp .env.example .env
#   openssl rand -base64 24   # POSTGRES_PASSWORD
#   openssl rand -base64 32   # VIKUNJA_SERVICE_SECRET
mkdir -p files    # created by the cloud user (uid 1000), so Vikunja can write attachments
docker compose up -d
docker compose logs -f vikunja   # wait for "Vikunja is now running on :3456"
```

## Users

Registration is **disabled** (`VIKUNJA_SERVICE_ENABLEREGISTRATION=false`), so create
users with the CLI instead of the signup page:

```bash
docker compose exec vikunja vikunja user create -u wilfred -e wilfredtuscano@gmail.com -p '<password>'
```

Use the **same username as the Nextcloud / Immich / Paperless accounts** for consistency.

## API token for automation (MCP)

The MCP server authenticates with a long-lived **API token** (not a JWT). Create one
in the web UI → **Settings → API Tokens** → grant the scopes the automation needs
(projects + tasks read/write at minimum). Store it wherever the MCP server reads its
config from — never commit it.

## MCP integration

Claude Code controls Vikunja through an MCP server configured against
`https://vikunja.local.wilfredtuscano.com/api/v1` with the API token above. Once
wired, projects/tasks/timelines become native tools (create task, list projects, set
due dates, …) available whenever Claude is started from `~/workspace`. See the MCP
config commit for the exact server + settings.

## Upgrading

Pin `vikunja` to a specific tag after first boot, then bump deliberately:

```bash
cd ~/docker/vikunja
# Edit docker-compose.yml — change `:latest` to e.g. `:0.24.6`
docker compose pull
docker compose up -d
```

## Notes

- Everything runs on the isolated `vikunja` bridge network.
- `security_opt: apparmor=unconfined` is required for Docker inside the privileged LXC
  (same as Paperless/Immich/Nextcloud here).
- `VIKUNJA_SERVICE_SECRET` signs JWTs — rotating it invalidates all active sessions.
