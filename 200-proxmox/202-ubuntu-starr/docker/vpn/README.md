# VPN Stack

Routes torrent traffic through a Surfshark WireGuard VPN tunnel via Gluetun. qBittorrent and Firefox share the VPN network — all their traffic exits through the tunnel.

## Services

| Service | Purpose | Port |
|---------|---------|------|
| Gluetun | WireGuard VPN tunnel (Surfshark) | — |
| qBittorrent | Torrent client | 8090 (UI), 56881 (torrenting) |
| Firefox | VPN-routed browser (for protected browsing) | 3000 (HTTP), 3001 (HTTPS) |

## Setup

Create a `.env` file (gitignored):

```env
WIREGUARD_PRIVATE_KEY=<your-surfshark-wireguard-private-key>
WIREGUARD_ADDRESSES=<your-wireguard-address>
```

Obtain these from the Surfshark dashboard under VPN → Manual setup → WireGuard.

## Volume mounts

| Container path | Host path | Purpose |
|----------------|-----------|---------|
| `/downloads` | `/mnt/nfs/downloads` | Shared download area with \*arr apps |

## Notes

- qBittorrent and Firefox use `network_mode: service:gluetun` — they have no network access if Gluetun is unhealthy
- Gluetun must be healthy before dependent containers start (`condition: service_healthy`)
- qBittorrent categories use paths relative to `/downloads` (e.g. `radarr`, `sonarr`)
- Access qBittorrent UI at `http://192.168.1.202:8090` (default credentials: `admin` / `adminadmin`, change on first login)
