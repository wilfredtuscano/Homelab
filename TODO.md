# TODO

## Infrastructure

- [ ] **Decommission Nextcloud** (`214-lxc-cloud`): Immich covers photos and Paperless-ngx covers
      documents, so Nextcloud + MariaDB + Redis + Collabora are redundant. Stop and remove the
      stack from cloud-ct, keep `docker/nextcloud/` in the repo as reference-only / non-deployed.
      Frees the largest single block of RAM on the densest CT.
- [x] ~~**Right-size LXC resources**~~ Done 2026-08-10 from 30 days of data: starr 8→6 GB / 4→2
      cores, plex 8→6 GB, cloud 8→12 GB / 4→6 cores. Total allocation unchanged at 48 GB. The
      80→40 GB disk shrink is cancelled permanently — the pool is 4% full.
- [ ] **Enable SSH + monitoring on TrueNAS (201).** It holds 24 GB, 38% of host RAM, and is the
      only guest with no metrics at all. Any further rebalancing is blocked on this.
- [ ] **Move `immich-machine-learning` to jarvis.** It is what saturated cloud-ct's CPU (187% peak,
      1.23 GB) while jarvis sits at 4.2 of 32 threads with an idle 96 GB-UMA GPU. Immich supports a
      remote ML endpoint via `IMMICH_MACHINE_LEARNING_URL`. Needs validating against jarvis's ROCm
      stack, and accepts a network dependency: if jarvis is down, ML degrades but Immich keeps
      working.
- [ ] **Look at `paperless-ai`** — peaks at 1.78 GB, larger than the entire Nextcloud stack, for an
      auxiliary service.
- [ ] **Refresh Ollama models on `jarvis`**: most of the library is ~11 months old and superseded.
      `mistral-small3.1:24b` is strictly redundant with the `3.2` already present. Keep
      `qwen2.5vl:32b` — Paperless-GPT depends on it for vision OCR.
- [ ] **TrueNAS SSH is disabled** (201 refuses port 22): decide whether to enable it for
      automation, or document the web UI / Proxmox console as the only management path.

## Defects found in the 2026-08-10 access sweep

- [x] ~~**Proxmox host (200) is not monitored at all.**~~ Fixed 2026-08-10: `prometheus-node-exporter`
      installed natively on the hypervisor and added to the Prometheus `node` job as host
      `proxmox`. Let it accumulate history before making sizing decisions from it.
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
- [ ] **Audit repo compose files against what is actually deployed.** For every stack on every
      host, diff the repo `docker-compose.y*ml` (and its config files) against the copy running on
      the box, and reconcile in whichever direction is correct. The repo is the blueprint but has
      never been verified as the source of truth. Spot-checked on 2026-08-10: `prometheus.yml`
      differed only by a trailing newline, which is benign — the rest is unverified.

## Media

- [ ] **Add ~20 regional films to TMDB** so Radarr and Plex can identify them (currently sitting in
      `downloads/radarr`, e.g. Bhagubai 2026, Chennai Central 2020, Frame 2026, Tighee 2026,
      Vastupurush 2002). Until then they stay unmonitored with Plex reading names from filenames.
