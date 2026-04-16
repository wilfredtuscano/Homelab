# Plex Media Server

Streams movies, series, and music from the NFS media share to all devices on the network (and remotely).

## Access

| Interface | URL |
|-----------|-----|
| Web UI | `http://192.168.1.203:32400/web` |

## Volume mounts

| Container path | Host path | Purpose |
|----------------|-----------|---------|
| `/config` | `./config` | Plex database, metadata, preferences |
| `/movies` | `/mnt/nfs/media/Movies` | Movie library |
| `/series` | `/mnt/nfs/media/Series` | TV series library |
| `/music` | `/mnt/nfs/media/Music` | Music library |

## Notes

- Runs with `network_mode: host` — required for Plex local network discovery (GDM)
- Hardware transcoding enabled via `/dev/dri` device passthrough (Intel/AMD iGPU)
- `privileged: true` is set for full hardware access
- Libraries should point to `/movies`, `/series`, `/music` inside the container
