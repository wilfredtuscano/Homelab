# TODO

- [ ] **Pi-hole**: Add `WEBPASSWORD` via `.env` file — `WEBPASSWORD=${PIHOLE_PASSWORD}` in `199-raspi5/docker/pihole/docker-compose.yml`
- [ ] **Traefik**: Rename `199-raspi5/docker/traefik/data/` config folder (e.g., to `config/`) to avoid conflict with the global `data/` gitignore rule. Currently worked around with a gitignore override in root `.gitignore`.
