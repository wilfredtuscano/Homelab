# Mealie

Self-hosted recipe manager. Import recipes from URLs, organise into collections, plan meals, and generate shopping lists.

## Access

| Interface | URL |
|-----------|-----|
| Web UI | `https://mealie.local.wilfredtuscano.com` |
| Direct | `http://192.168.1.204:9000` |

## Notes

- Uses SQLite by default — no separate database needed
- `ALLOW_SIGNUP=false` — create your account on first login, then signups are closed
- Default credentials on first run: `changeme@example.com` / `MyPassword` — change immediately
- Recipe data stored in `./data`

## Limitations vs Tandoor

If Mealie doesn't meet your needs, Tandoor Recipes is already configured at `../tandoor/` and offers:
- Per-step images
- Sub-recipes (components that assemble into a parent recipe, e.g. "Béchamel" embedded in "Lasagna")

See `../tandoor/README.md` for details.
