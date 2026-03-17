# 199 — Raspberry Pi 5

**IP:** 192.168.1.199
**OS:** Raspberry Pi OS (64-bit) / Ubuntu Server

## Hardware

| Component | Details |
|---|---|
| Board | Raspberry Pi 5 |
| RAM | 8 GB |

## Role

- Network-wide DNS ad-blocking (Pi-hole)
- Reverse proxy for all local services (Traefik)
- Container management (Portainer)
- Remote access gateway (Tailscale subnet router)

## Setup

1. [Set a static IP](../guides/static-ip.md)
2. [Install Docker](../guides/docker-install.md)
3. Deploy stacks in order:
   1. `docker/portainer/` — Portainer
   2. `docker/pihole/` — Pi-hole (set as DNS on router after this step)
   3. `docker/traefik/` — Traefik
4. [Set up Tailscale subnet router](../guides/tailscale.md)

## Docker Stacks

| Folder | Services |
|---|---|
| [docker/portainer/](docker/portainer/) | Portainer |
| [docker/pihole/](docker/pihole/) | Pi-hole |
| [docker/traefik/](docker/traefik/) | Traefik |
