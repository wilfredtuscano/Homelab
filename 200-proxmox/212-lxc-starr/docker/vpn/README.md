# VPN Stack

Routes torrent traffic through a Surfshark WireGuard VPN tunnel via Gluetun. qBittorrent shares the VPN network — all its traffic exits through the tunnel.

## Services

| Service | Purpose | Port |
|---------|---------|------|
| Gluetun | WireGuard VPN tunnel (Surfshark) | — |
| qBittorrent | Torrent client | 8090 (UI), 56881 (torrenting) |

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

- qBittorrent uses `network_mode: service:gluetun` — it has no network access if Gluetun is unhealthy
- Gluetun must be healthy before dependent containers start (`condition: service_healthy`)
- qBittorrent categories use paths relative to `/downloads` (e.g. `radarr`, `sonarr`)
- Access qBittorrent UI at `http://192.168.1.202:8090` (default credentials: `admin` / `adminadmin`, change on first login)

## Verifying the VPN exit IP

No browser needed — query Gluetun directly:

```bash
docker exec gluetun wget -qO- https://ipinfo.io
```

Returns JSON with IP, country, city, organisation. Use this to confirm the tunnel is up and exits where expected. Gluetun also logs the public IP on startup:

```bash
docker logs gluetun 2>&1 | grep -i "public ip" | tail -3
```

> Gluetun ≥3.40 also exposes a control server on port 8000 with the same info via `/v1/publicip/ip`, but it requires an auth-config file to use. Not worth the extra config for a one-line `docker exec` equivalent.

If you ever need a full browser inside the tunnel (e.g. for WebRTC leak testing), spin one up ad-hoc and kill it when done:

```bash
docker run --rm -it --network=container:gluetun -p 3000:3000 lscr.io/linuxserver/firefox
```
