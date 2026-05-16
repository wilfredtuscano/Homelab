# Calibre-web

Web interface for browsing, reading, and downloading ebooks from the NFS books library.

## Access

| Interface | URL |
|-----------|-----|
| Web UI | `https://calibre-web.local.wilfredtuscano.com` |
| Direct | `http://192.168.1.203:8083` |

## Default credentials

| Field | Value |
|---|---|
| Username | `admin` |
| Password | `admin123` |

Change immediately after first login.

## First-time setup

### 1. Initialize metadata.db

Calibre-web requires a Calibre library database to exist before it can use the books path. Run this once on the plex VM to create it:

```bash
docker run --rm \
  --user 1000:1000 \
  -v /mnt/nfs/media/Books:/books \
  lscr.io/linuxserver/calibre \
  calibredb list --with-library /books
```

Verify it was created:

```bash
ls -la /mnt/nfs/media/Books/metadata.db
```

### 2. Configure library path

On first login, set the library path to `/books` when prompted.

### 3. Enable uploads

Admin → Edit Basic Configuration → check **Enable Uploads** → Save.

## Adding books

### Directory structure

Books must follow the `Author/Title/` layout before importing:

```
/mnt/nfs/media/Books/
└── Author Name/
    └── Book Title/
        └── book.epub
```

Use the author's name exactly as it appears on the book (e.g. `Andy Weir`, `J.K. Rowling`). Calibre treats name variations as separate authors.

### Import a book

After placing the EPUB in the correct directory, SSH into the plex VM and run:

```bash
docker run --rm \
  --user 1000:1000 \
  -v /mnt/nfs/media/Books:/books \
  lscr.io/linuxserver/calibre \
  calibredb add "/books/Author Name/Book Title/book.epub" --with-library /books
```

Example:

```bash
docker run --rm \
  --user 1000:1000 \
  -v /mnt/nfs/media/Books:/books \
  lscr.io/linuxserver/calibre \
  calibredb add "/books/Andy Weir/Project Hail Mary/Project Hail Mary - Andy Weir.epub" --with-library /books
```

Look for `Added book ids: X` in the output. The book appears in Calibre-web immediately — no restart needed.

### Import all books at once

To bulk-import everything under `/books` (e.g. after initial setup):

```bash
docker run --rm \
  --user 1000:1000 \
  -v /mnt/nfs/media/Books:/books \
  lscr.io/linuxserver/calibre \
  calibredb add --recurse /books --with-library /books
```

## Supported formats

| Read in browser | Download only |
|---|---|
| EPUB, PDF, CBZ, CBR | MOBI, AZW, AZW3, FB2, LIT, RTF, TXT, DOCX |

## Volume mounts

| Container path | Host path | Purpose |
|----------------|-----------|---------|
| `/config` | `./config` | Calibre-web config and database |
| `/books` | `/mnt/nfs/media/Books` | Ebook library |

## Notes

- Ebooks managed separately from audiobooks — Audiobookshelf handles audiobooks
- Calibre-web reads/writes `metadata.db` inside `/books` — created during first-time setup above
- Books downloaded via Prowlarr land in `/mnt/nfs/downloads/` — move to `/mnt/nfs/media/Books/Author/Title/` before importing
