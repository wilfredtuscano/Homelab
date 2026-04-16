# Portainer

Web UI for managing Docker containers, stacks, images, volumes, and networks on this host.

## Access

| Interface | URL |
|-----------|-----|
| Web UI (HTTPS) | `https://192.168.1.204:9443` |

## Ports

| Port | Purpose |
|------|---------|
| 9443 | HTTPS web UI |
| 8000 | Portainer agent tunnel (for remote host management) |

## Notes

- Mounts the Docker socket (`/var/run/docker.sock`) for full Docker control
- Data persisted in `./data/`
