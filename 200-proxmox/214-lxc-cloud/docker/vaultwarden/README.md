# Vaultwarden

Self-hosted Bitwarden-compatible password manager. Use any official Bitwarden client (browser extension, mobile app, desktop) to connect to this instance.

## Access

| Interface | URL |
|-----------|-----|
| Web UI | `https://vaultwarden.local.wilfredtuscano.com` |

## Notes

- `SIGNUPS_ALLOWED=false` — new account registration is disabled; create accounts via the admin panel
- Admin panel: `https://vaultwarden.local.wilfredtuscano.com/admin` (requires `ADMIN_TOKEN` in `.env`)
- Data persisted in `./data/`
- Served behind Traefik — direct port `8082` is internal only

## Client setup

In any Bitwarden client, set the **Server URL** to `https://vaultwarden.local.wilfredtuscano.com` before logging in.
