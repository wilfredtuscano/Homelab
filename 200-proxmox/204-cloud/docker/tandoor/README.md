# Tandoor Recipes

> **Not currently deployed.** Mealie is being trialled first (`../mealie/`). Deploy Tandoor if Mealie doesn't suffice.

Self-hosted recipe manager with advanced features — per-step images, sub-recipes, and ingredient sections.

## Why Tandoor over Mealie

| Feature | Mealie | Tandoor |
|---------|--------|---------|
| Per-step images | No | Yes |
| Sub-recipes (components assembled into parent) | No | Yes |
| Ingredient sections | Limited | Yes |
| UI polish | Better | Good |

Sub-recipes example: "Béchamel Sauce" and "Bolognese" are standalone recipes, both embedded as components in "Lasagna" — their ingredients automatically fold into the parent shopping list.

## Access (when deployed)

| Interface | URL |
|-----------|-----|
| Web UI | `http://192.168.1.204:8002` |

## Setup

```bash
cp .env.example .env
# Fill in .env:
#   SECRET_KEY — generate with: openssl rand -base64 50
#   POSTGRES_PASSWORD — strong random password

docker compose up -d
```

First login creates the admin account.

## Volume mounts

| Container path | Host path | Purpose |
|----------------|-----------|---------|
| `/opt/recipes/staticfiles` | `./staticfiles` | Static assets |
| `/opt/recipes/mediafiles` | `./mediafiles` | Uploaded recipe images |
| `/var/lib/postgresql/data` | `./db` | Postgres database |
