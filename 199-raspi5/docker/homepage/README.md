# Homepage

Service dashboard and launcher for all homelab services.

Accessible at: `https://homepage.local.wilfredtuscano.com`

## What it does

Provides a single landing page with links to every service, grouped by category, with live ping checks to show if each service is reachable. Designed to be the browser start page when on the local network.

## Service groups

| Group | Services |
|-------|----------|
| Infrastructure | Portainer, Proxmox, TrueNAS, Pi-hole, Traefik |
| Monitoring | Grafana |
| Media | Plex, Sonarr, Radarr, Lidarr, Readarr, Prowlarr, qBittorrent, MeTube |
| Cloud | Nextcloud, Vaultwarden, Collabora |
| AI | Open WebUI, Ollama |

## Config files

All config lives in `./config/` as YAML files — no database, no UI editor:

| File | Purpose |
|------|---------|
| `services.yaml` | Service groups, links, icons, ping targets |
| `settings.yaml` | Theme, title, layout columns per group |
| `widgets.yaml` | Top bar widgets (greeting, clock, search) |
| `bookmarks.yaml` | Bookmark groups (kept empty to suppress Homepage defaults) |

## Setup

1. Start the stack:
   ```bash
   docker compose up -d
   ```

2. Add DNS entry in Pi-hole: `homepage.local.wilfredtuscano.com` → `192.168.1.199`

3. Open `https://homepage.local.wilfredtuscano.com`

## Notes

- Icons use the built-in icon library — use the service name as `icon: <name>.svg`. For services without a built-in icon, use Material Design Icons with `icon: mdi-<icon-name>`
- Ping checks use HTTPS — services with self-signed certs may show as unreachable even if working
- Config changes take effect immediately without restarting the container
- `HOMEPAGE_ALLOWED_HOSTS` must be set to the domain used to access Homepage, otherwise requests will be blocked with a host validation error
