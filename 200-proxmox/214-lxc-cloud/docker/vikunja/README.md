# Vikunja

Self-hosted project & task manager — one board per project, tracking tasks and
timelines across everything managed from the personal hub. Designed to be
**driven programmatically**: Claude Code manages the whole workflow through an MCP server that
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
# The binary lives at /app/vikunja/vikunja (it is not on $PATH inside the image).
docker compose exec -T vikunja /app/vikunja/vikunja user create -u <user> -e <email> -p '<password>'

# Reset a password later. Takes the USER ID positionally, not a username, and --direct is
# required because the default path mails a reset link and the mailer is disabled here.
# Omit -p so it prompts, keeping the password out of shell history.
docker compose exec vikunja /app/vikunja/vikunja user reset-password <id> --direct

# `vikunja user list` shows the ids.
```

Use the **same username as the Nextcloud / Immich / Paperless accounts** for consistency.

> **There is no mailer configured**, so "Forgot your password" on the login page can never work.
> It accepts the request and has nowhere to send it. The CLI above is the only reset path. A wrong
> password returns HTTP **403** with `"code":1011`, which reads like a permissions problem and is
> not one.

## API token for automation (MCP)

The MCP server authenticates with a long-lived **API token** (not a JWT). Create one
in the web UI → **Settings → API Tokens** → grant the scopes the automation needs
(projects + tasks read/write at minimum). Store it wherever the MCP server reads its
config from — never commit it.

## MCP integration

Claude Code controls Vikunja through the community MCP server
[`@democratize-technology/vikunja-mcp`](https://github.com/democratize-technology/vikunja-mcp)
(npx-based, understands long-lived `tk_` API tokens, with guard-rails on destructive
ops). Register it once at **user scope** so it's available wherever Claude starts:

```bash
claude mcp add vikunja --scope user \
  --env VIKUNJA_URL=https://vikunja.local.wilfredtuscano.com/api/v1 \
  --env VIKUNJA_API_TOKEN=<tk_… token> \
  -- npx -y @democratize-technology/vikunja-mcp
```

- **API version** - the MCP is configured against `/api/v1`, which 2.x still serves as a
  compatibility shim while the web UI calls `/api/v2`. v1 works today, long-lived `tk_` tokens
  included, but it is the thing most likely to disappear in a future major. If MCP calls start
  failing after an upgrade, check this first.
- **URL** — the Traefik hostname is used (valid Let's Encrypt `*.local.wilfredtuscano.com`
  cert, so Node trusts it without extra flags; survives an IP change). The direct
  `http://192.168.1.204:3456/api/v1` is a fine fallback if DNS/Traefik is down.
- **Token** — lives only in `~/.claude.json`, never this repo. Mint one in the UI
  (Settings → API Tokens) with project + task scopes.

Restart Claude after registering; projects/tasks/labels/dates then become native tools
(create task, list projects, set due dates, move between projects, …). Verify with
`claude mcp list` — it should show `vikunja: … ✔ Connected`.

## Upgrading

`vikunja` is pinned to `2.7.0`. **Do not put it back on `latest`.** It was unpinned until
2026-10-13, and in that time a `latest` pull carried the stack from 0.24.x to 2.7.0 with no prompt
and no record: a major version jump that moved the API to `/api/v2` and renamed CLI subcommands.
The `db` service is on `postgres:16`, which holds the major and still picks up 16.x patches.

To bump, read the upstream release notes first, then:

```bash
cd ~/docker/vikunja
# Edit docker-compose.yml, changing the tag to the version you intend
docker compose pull
docker compose up -d
docker compose logs -f vikunja   # confirm migrations ran and the version is what you expect
```

Migrations run automatically on boot and are not reversible, so **back up the database before a
major bump**. Rolling the tag back does not roll the schema back.

## Notes

- Everything runs on the isolated `vikunja` bridge network.
- `security_opt: apparmor=unconfined` is required for Docker inside the privileged LXC
  (same as Paperless/Immich/Nextcloud here).
- `VIKUNJA_SERVICE_SECRET` signs JWTs — rotating it invalidates all active sessions.
