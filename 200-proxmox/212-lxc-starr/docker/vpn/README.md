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

## vpn-watchdog: qBittorrent only runs behind a healthy tunnel

When gluetun reconnects its WireGuard tunnel while qBittorrent keeps running, qBittorrent's UDP
tracker and DHT sockets go stale. Public torrents stall (magnets sit on "Downloading metadata")
while private HTTPS-tracker torrents keep moving, which hides the problem. Restarting only the
qbittorrent container fixes it. Separately, `depends_on: condition: service_healthy` only applies
inside `docker compose up`: after a reboot the Docker daemon would start both containers together.

So qbittorrent has `restart: "no"`, and [`vpn-watchdog`](vpn-watchdog), run every minute from cron
as the login user, is its only automatic starter:

| Situation | Action |
|---|---|
| qbittorrent stopped by a reboot or daemon restart | start it once gluetun has been healthy for 2 min |
| tunnel reconnected (or gluetun restarted) after qbittorrent started | restart it once the tunnel has been up 10 min |
| qbittorrent still attached to a gluetun container that no longer exists | recreate it with compose |
| qbittorrent stopped by hand | leave it stopped |

At most one action per 30 minutes, so a reconnect storm produces one restart. It never touches
gluetun, and never qBittorrent's settings or API. gluetun's healthcheck tests real traffic through
the tunnel (TLS to `cloudflare.com:443` / `github.com:443`, ICMP to `1.1.1.1` / `8.8.8.8`), so
"healthy" means connected.

**Install** (no root needed; the login user is in the `docker` group):

```bash
install -D -m 0755 vpn-watchdog ~/.local/bin/vpn-watchdog
( crontab -l 2>/dev/null; echo '* * * * * VPN_WATCHDOG_ARMED=1 $HOME/.local/bin/vpn-watchdog' ) | crontab -
```

Without `VPN_WATCHDOG_ARMED=1` it runs in dry-run and only logs what it would do. Every decision
goes to `~/vpn-watchdog.log`. Disable it with `touch ~/.vpn-watchdog.pause`.

**Test** after any change, with fake `docker` and `systemctl` (touches no container):

```bash
./vpn-watchdog.test
```
