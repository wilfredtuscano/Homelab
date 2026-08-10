# TODO

## Infrastructure

- [ ] **Decommission Nextcloud** (`214-lxc-cloud`): Immich covers photos and Paperless-ngx covers
      documents, so Nextcloud + MariaDB + Redis + Collabora are redundant. Stop and remove the
      stack from cloud-ct, keep `docker/nextcloud/` in the repo as reference-only / non-deployed.
      Frees the largest single block of RAM on the densest CT.
- [ ] **Right-size LXC resources**: decide 212/213/214 RAM and core allocation from the Grafana
      Node Exporter + cAdvisor dashboards, *after* the Nextcloud removal changes the numbers.
      Current allocation is 48 / 62 GB across all guests — see [200-proxmox/README.md](200-proxmox/README.md#resource-allocation).
- [ ] **Refresh Ollama models on `jarvis`**: most of the library is ~11 months old and superseded.
      `mistral-small3.1:24b` is strictly redundant with the `3.2` already present. Keep
      `qwen2.5vl:32b` — Paperless-GPT depends on it for vision OCR.
- [ ] **TrueNAS SSH is disabled** (201 refuses port 22): decide whether to enable it for
      automation, or document the web UI / Proxmox console as the only management path.

## Defects found in the 2026-08-10 access sweep

- [ ] **Proxmox host (200) is not monitored at all.** Prometheus scrapes 199/202/203/204/205 but
      never the hypervisor — there is no node-exporter on it. Blocks any resourcing decision that
      needs host-level RAM/CPU pressure. Fix before the right-sizing review.
- [ ] **Traefik's Docker provider is broken.** `traefik:v3.0` (3.0.4) negotiates Docker API 1.24;
      the daemon on dnspi now requires ≥1.40, so the provider is in a permanent retry loop and
      floods the logs. Consequence: routers defined via Docker labels are never registered, which
      is why `traefik-dashboard.local.wilfredtuscano.com` returns 404. The file provider
      (`config.yml`) is unaffected, so all other services still route. Fix by bumping the Traefik
      image, or pin `DOCKER_API_VERSION` on the container.
- [ ] **`router.local.wilfredtuscano.com` returns 502.** The service sets `passHostHeader: true`,
      and the router at 192.168.1.1 drops the connection when the Host header is not its own
      (verified: 401 with default Host, no response at all with the proxied Host). Set
      `passHostHeader: false` on that service. `gateway` → 10.0.0.1 is unaffected.
- [ ] **Prometheus has two permanently-down targets** — `cadvisor` and `node` on 192.168.1.199.
      The RasPi runs the monitoring *server*, not the agent, so these were never going to come up.
      Either deploy the agent there or drop the targets from the scrape config.

## Cleanup

- [ ] **Traefik**: remove the dead `firefox.local.wilfredtuscano.com` router from
      `199-raspi5/docker/traefik/data/config.yml` — the Firefox container was dropped in PR #14.
      Also clean up the Firefox references in `200-proxmox/212-lxc-starr/docker/vpn/README.md`.
- [ ] **Pi-hole**: Add `WEBPASSWORD` via `.env` file — `WEBPASSWORD=${PIHOLE_PASSWORD}` in `199-raspi5/docker/pihole/docker-compose.yml`
- [ ] **Traefik**: Rename `199-raspi5/docker/traefik/data/` config folder (e.g., to `config/`) to avoid conflict with the global `data/` gitignore rule. Currently worked around with a gitignore override in root `.gitignore`.
- [ ] **`203-ubuntu-plex/`**: superseded by `213-lxc-plex/` after the VM→LXC migration. Decide
      whether to keep it as historical reference or drop it.

## Media

- [ ] **Add ~20 regional films to TMDB** so Radarr and Plex can identify them (currently sitting in
      `downloads/radarr`, e.g. Bhagubai 2026, Chennai Central 2020, Frame 2026, Tighee 2026,
      Vastupurush 2002). Until then they stay unmonitored with Plex reading names from filenames.
