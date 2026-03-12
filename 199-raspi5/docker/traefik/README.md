# Traefik

Reverse proxy with automatic TLS via Cloudflare DNS challenge (Let's Encrypt wildcard cert for `*.local.wilfredtuscano.com`).

## Prerequisites

- `proxy` Docker network must exist before starting:
  ```bash
  docker network create proxy
  ```
- Cloudflare API token with DNS edit permissions stored as a Docker secret:
  ```bash
  echo "your-cf-api-token" > cf_api_token.txt
  chmod 600 cf_api_token.txt
  ```
- `TRAEFIK_DASHBOARD_CREDENTIALS` in `.env` (htpasswd format):
  ```bash
  echo $(htpasswd -nb <user> <password>) > .env  # requires apache2-utils
  ```
- Create `acme.json` before first run (Traefik writes TLS certs here — never commit this file):
  ```bash
  touch data/acme.json && chmod 600 data/acme.json
  ```

## Config files

| File | Purpose |
|---|---|
| `data/traefik.yml` | Static Traefik config (entrypoints, providers, cert resolver) |
| `data/config.yml` | Dynamic config (middlewares, routers) |
| `data/acme.json` | TLS certificates — gitignored, populated by Traefik at runtime |
