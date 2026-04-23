# Audiobookshelf

Self-hosted audiobook and ebook server. Stream audiobooks and read EPUBs from any device. Official Android/iOS apps available.

## Access

| Interface | URL |
|-----------|-----|
| Web UI | `http://192.168.1.203:13378` |

## Volume mounts

| Container path | Host path | Purpose |
|----------------|-----------|---------|
| `/config` | `./config` | Server config and user data |
| `/metadata` | `./metadata` | Cover art cache and metadata |
| `/audiobooks` | `/mnt/nfs/media/Audiobooks` | Audiobook library (M4B, MP3) |
| `/books` | `/mnt/nfs/media/Books` | Ebook library (EPUB, PDF) |

## Setup

After deploying, create an admin account on first visit, then add libraries:
- **Audiobooks** → point to `/audiobooks` — set type to "Audiobooks"
- **Books** → point to `/books` — set type to "Books"

## Notes

- Downloads are handled by LazyLibrarian on the starr VM — Audiobookshelf is serve-only
- Preferred formats: **M4B** for audiobooks (chapters + cover art embedded), **EPUB** for ebooks
- The Android app (Audiobookshelf on Play Store) is free and supports offline downloads
