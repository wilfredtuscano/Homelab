# Network

## IP Assignments

| Host | IP | SSH alias | Notes |
|---|---|---|---|
| Router | 192.168.1.1 | — | Gateway |
| Raspberry Pi 5 | 192.168.1.199 | `dnspi` | Debian 12 (bookworm). Static via router DHCP reservation |
| Proxmox Server | 192.168.1.200 | `homelab` | Proxmox VE 8.1.3. Static via router DHCP reservation |
| TrueNAS Core 13 | 192.168.1.201 | `truenas` | VM on Proxmox. SSH disabled — see note below |
| LXC - Starr | 192.168.1.202 | `starr-ct` | Ubuntu 22.04.5, privileged LXC 212 on Proxmox |
| LXC - Plex | 192.168.1.203 | `plex-ct` | Ubuntu 22.04.5, privileged LXC 213 on Proxmox |
| LXC - Cloud | 192.168.1.204 | `cloud-ct` | Ubuntu 22.04.5, privileged LXC 214 on Proxmox |
| GMKTec Evo-X2 | 192.168.1.205 | `jarvis` | Ubuntu 24.04.4. Static via router DHCP reservation |

> 202/203/204 are **LXC containers**, not VMs — they were migrated off VMs 202/203/204 and kept the IPs.
> TrueNAS refuses SSH on port 22 (service disabled); manage it via the web UI or the Proxmox console.

## DNS (Pi-hole on 192.168.1.199)

Pi-hole is the primary DNS for the network, with Unbound as the upstream recursive resolver.
Local DNS records are managed in the Pi-hole admin UI.

All services are reached through Traefik on `*.local.wilfredtuscano.com` — every hostname below
resolves to **192.168.1.199** and Traefik routes it onward. The older `*.home` names are retired.

| Hostname (`*.local.wilfredtuscano.com`) | Backend |
|---|---|
| `pihole` | Pi-hole admin (199:8080) |
| `traefik-dashboard` | Traefik dashboard (199) |
| `portainer` | Portainer (199:9443) |
| `grafana` | Grafana (199:3001) |
| `homepage` | Homepage dashboard (199:3002) |
| `proxmox` | Proxmox UI (200:8006) |
| `truenas` | TrueNAS UI (201) |
| `router` / `gateway` | Router UI (192.168.1.1) |
| `sonarr` `radarr` `prowlarr` `lidarr` `readarr` | *arr apps (202) |
| `qbittorrent` | qBittorrent via Gluetun (202:8090) |
| `metube` | MeTube (202:8081) |
| `plex` | Plex (203:32400) |
| `audiobookshelf` | Audiobookshelf (203:13378) |
| `calibre-web` | Calibre-web (203:8083) |
| `vaultwarden` | VaultWarden (204:8082) |
| `mealie` | Mealie (204:9000) |
| `immich` | Immich (204:2283) |
| `paperless` | Paperless-ngx (204:8000) |
| `vikunja` | Vikunja (204:3456) |
| `nextcloud` | Nextcloud (204:8443) |
| `collabora` | Collabora (204:9980) |
| `chat` | OpenWebUI (205:3000) |
| `ollama` | Ollama API (205:11434) |

> The Traefik file provider still carries a `firefox.local.wilfredtuscano.com` router, but the
> Firefox container was dropped in PR #14. That route is dead and should be removed.

## Remote Access (Tailscale)

Tailscale is installed on RasPi5 as a **subnet router**, advertising `192.168.1.0/24`. Client devices (Mac, Android) connect to Tailscale and can reach all homelab LAN IPs without any router port forwarding.

Split DNS is configured in the Tailscale admin console to route `local.wilfredtuscano.com` queries through Pi-hole when connected to Tailscale.

See [guides/tailscale.md](guides/tailscale.md) for full setup.

## Ports

Published host ports, as observed on the running hosts. Prefer the Traefik hostnames above for
day-to-day access; these are the direct backends.

| Machine | Port | Service |
|---|---|---|
| 192.168.1.199 | 53 | Pi-hole DNS (Unbound upstream, internal only) |
| 192.168.1.199 | 80/443 | Traefik |
| 192.168.1.199 | 8000 / 9443 | Portainer (edge tunnel / UI) |
| 192.168.1.199 | 3001 | Grafana |
| 192.168.1.199 | 3002 | Homepage |
| 192.168.1.199 | 3100 | Loki |
| 192.168.1.199 | 8080 | Pi-hole admin UI |
| 192.168.1.199 | 9090 | Prometheus |
| 192.168.1.200 | 8006 | Proxmox VE UI |
| 192.168.1.202 | 7878 | Radarr |
| 192.168.1.202 | 8081 | MeTube |
| 192.168.1.202 | 8090 | qBittorrent WebUI (published by Gluetun) |
| 192.168.1.202 | 8191 | FlareSolverr |
| 192.168.1.202 | 8686 | Lidarr |
| 192.168.1.202 | 8787 | Readarr |
| 192.168.1.202 | 8989 | Sonarr |
| 192.168.1.202 | 9696 | Prowlarr |
| 192.168.1.202 | 56881 | Gluetun — torrent listen port (TCP/UDP) |
| 192.168.1.203 | 8083 | Calibre-web |
| 192.168.1.203 | 13378 | Audiobookshelf |
| 192.168.1.203 | 32400 | Plex |
| 192.168.1.204 | 2283 | Immich |
| 192.168.1.204 | 3000 | Paperless-AI |
| 192.168.1.204 | 3456 | Vikunja |
| 192.168.1.204 | 8000 | Paperless-ngx |
| 192.168.1.204 | 8080 | Paperless-GPT |
| 192.168.1.204 | 8082 | VaultWarden |
| 192.168.1.204 | 8443 | Nextcloud |
| 192.168.1.204 | 9000 | Mealie |
| 192.168.1.204 | 9980 | Collabora |
| 192.168.1.205 | 3000 | OpenWebUI |
| 192.168.1.205 | 11434 | Ollama API (native systemd service, not Docker) |
| .199 / .202 / .203 / .204 / .205 | 9080 | cAdvisor (monitoring agent, all hosts) |

**Bazarr is not deployed.** It was listed here historically but no such container runs on 202.
