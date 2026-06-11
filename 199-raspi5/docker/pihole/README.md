# Pi-hole + Unbound

Network-wide DNS ad blocker (Pi-hole) backed by a local recursive resolver (Unbound). Pi-hole blocks ads/trackers at the DNS layer for the whole LAN, then forwards anything not blocked to Unbound, which resolves queries directly against the DNS root servers instead of trusting a third party (Google/Cloudflare/etc).

## Access

| Interface | URL |
|-----------|-----|
| Admin UI | `http://192.168.1.199:8080/admin` |

## Ports

| Port | Protocol | Purpose |
|------|----------|---------|
| 53 | TCP/UDP | DNS (Pi-hole) |
| 8080 | TCP | Web admin UI |

Unbound listens on `10.55.0.2:53` inside the `pihole_net` Docker network only — not exposed to the host. Pi-hole forwards to it via the `PIHOLE_DNS_` env var.

## Config files

| Path | Purpose |
|------|---------|
| `etc-pihole/` | Pi-hole config, blocklists, custom DNS entries — persisted across restarts |

The `mvance/unbound-rpi` image ships a complete working config (DNSSEC on, root hints, sane caching) baked into the image. No external mount needed.

## Notes

- DNS upstream is **Unbound only** (`10.55.0.2#53`) — set via `PIHOLE_DNS_` env, no upstream needs to be ticked in the admin UI under Settings → DNS.
- Add local DNS records under Local DNS → DNS Records for homelab hostnames.
- Image is `mvance/unbound-rpi:latest` — ARM-native (multi-arch). The plain `mvance/unbound:latest` is amd64-only and runs under QEMU emulation on the Pi.

## Network subnet

The compose pins `pihole_net` to `10.55.0.0/24`. This is intentional — Docker auto-assigns subnets from `172.17.0.0/16` through `172.31.0.0/16` for stacks that don't pin one, and we kept colliding when another stack auto-grabbed `172.20`. Anything in `10.0.0.0/8` (outside the LAN's `192.168.1.0/24`) is safe and won't collide.

## Why Unbound

- **Privacy** — queries go straight to authoritative servers, no Google/Cloudflare logging every lookup.
- **No rate limits** — public resolvers throttle heavy users; a local resolver doesn't.
- **DNSSEC validation** — the mvance image enables this by default.
- **Caching** — repeated lookups are answered locally without hitting upstream.

## Verification

After `docker compose up -d` (wait for both containers to be `(healthy)`):

```bash
# Unbound resolves a normal name
docker exec pihole dig @10.55.0.2 cloudflare.com +short

# DNSSEC validation is on — dnssec-failed.org should return SERVFAIL
docker exec pihole dig @10.55.0.2 dnssec-failed.org

# From a LAN client, Pi-hole + Unbound chain works end-to-end
dig @192.168.1.199 cloudflare.com +short
nslookup doubleclick.net 192.168.1.199    # → 0.0.0.0 (blocked)
```
