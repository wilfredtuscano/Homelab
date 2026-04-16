# Pi-hole

Network-wide DNS ad blocker. Acts as the DNS server for the local network, blocking ads and trackers at the DNS level for all devices.

## Access

| Interface | URL |
|-----------|-----|
| Admin UI | `http://192.168.1.199:8080/admin` |

## Ports

| Port | Protocol | Purpose |
|------|----------|---------|
| 53 | TCP/UDP | DNS |
| 8080 | TCP | Web admin UI |

## Config files

| Path | Purpose |
|------|---------|
| `etc-pihole/` | Pi-hole config, blocklists, custom DNS entries — persisted across restarts |

## Notes

- DNS upstream is set to `8.8.8.8` (Google) — change in the admin UI under Settings → DNS if preferred
- Add local DNS records under Local DNS → DNS Records for homelab hostnames
