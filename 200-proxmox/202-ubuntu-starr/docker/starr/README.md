# Starr Apps

Media automation stack. Monitors RSS feeds, searches indexers, and sends grabs to qBittorrent. Automatically renames and moves completed downloads to the NFS media share.

## Services

| Service | Purpose | Port |
|---------|---------|------|
| Prowlarr | Indexer manager — syncs indexers to all \*arr apps | 9696 |
| Radarr | Movie automation | 7878 |
| Sonarr | TV series automation | 8989 |
| Lidarr | Music automation | 8686 |
| Readarr | Book automation | 8787 |
| FlareSolverr | Cloudflare bypass proxy (used by Prowlarr) | 8191 |
| Metube | YouTube/web video downloader | 8081 |

## Volume mounts

| Container path | Host path | Purpose |
|----------------|-----------|---------|
| `/movies` | `/mnt/nfs/media/Movies` | Final movie library |
| `/series` | `/mnt/nfs/media/Series` | Final series library |
| `/music` | `/mnt/nfs/media/Music` | Final music library |
| `/books` | `/mnt/nfs/media/Books` | Final books library |
| `/audiobooks` | `/mnt/nfs/media/Audiobooks` | Final audiobooks library |
| `/downloads` | `/mnt/nfs/downloads` | Download staging area |
| `/recycle-bin` | `/mnt/nfs/recycle-bin/<type>` | Trash for each media type |

## Notes

- All \*arr apps run as `PUID=1000 PGID=1000` — ensure NFS share permissions match
- Connect Prowlarr to each \*arr app under Settings → Apps, then sync indexers
- Connect each \*arr app to qBittorrent (vpn stack) at `http://192.168.1.202:8090`
- Metube downloads to `/mnt/nfs/downloads/metube`
