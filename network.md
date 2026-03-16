# Network

## IP Assignments

| Host | IP | MAC | Notes |
|---|---|---|---|
| Router | 192.168.1.1 | — | Gateway |
| Raspberry Pi 5 | 192.168.1.199 | — | Static via router DHCP reservation |
| Proxmox Server | 192.168.1.200 | — | Static via router DHCP reservation |
| TrueNAS Core 13 | 192.168.1.201 | — | VM on Proxmox |
| Ubuntu - Starr | 192.168.1.202 | — | VM on Proxmox |
| Ubuntu - Plex | 192.168.1.203 | — | VM on Proxmox |
| GMKTec Evo-X2 | 192.168.1.205 | — | Static via router DHCP reservation |

## DNS (Pi-hole on 192.168.1.199)

Pi-hole is the primary DNS for the network. Local DNS records are managed in the Pi-hole admin UI.

| Domain | Resolves To | Service |
|---|---|---|
| pihole.home | 192.168.1.199 | Pi-hole |
| traefik.home | 192.168.1.199 | Traefik dashboard |
| portainer.home | 192.168.1.199 | Portainer |

## Ports

| Machine | Port | Service |
|---|---|---|
| 192.168.1.199 | 53 | Pi-hole DNS |
| 192.168.1.199 | 80/443 | Traefik |
| 192.168.1.199 | 8080 | Traefik dashboard |
| 192.168.1.199 | 9000 | Portainer |
| 192.168.1.202 | 8989 | Sonarr |
| 192.168.1.202 | 7878 | Radarr |
| 192.168.1.202 | 9696 | Prowlarr |
| 192.168.1.202 | 8686 | Lidarr |
| 192.168.1.202 | 8787 | Readarr |
| 192.168.1.202 | 6767 | Bazarr |
| 192.168.1.202 | 8080 | qBittorrent (via VPN) |
| 192.168.1.203 | 32400 | Plex |
| 192.168.1.205 | 11434 | Ollama API |
| 192.168.1.205 | 3000 | OpenWebUI |
