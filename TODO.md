# TODO

## Infrastructure

- [ ] **Decommission Nextcloud** (`214-lxc-cloud`): Immich covers photos and Paperless-ngx covers
      documents, so Nextcloud + MariaDB + Redis + Collabora are redundant. Stop and remove the
      stack from cloud-ct, keep `docker/nextcloud/` in the repo as reference-only / non-deployed.
      Frees the largest single block of RAM on the densest CT.
- [x] ~~**Right-size LXC resources**~~ Done 2026-08-10 from 30 days of data: starr 8→6 GB / 4→2
      cores, plex 8→6 GB, cloud 8→12 GB / 4→6 cores. Total allocation unchanged at 48 GB. The
      80→40 GB disk shrink is cancelled permanently — the pool is 4% full.
- [x] ~~**Enable SSH + monitoring on TrueNAS (201).**~~ Done 2026-08-10: SSH key-only, SNMP scraped
      via snmp-exporter. Measured 20.26 GiB ARC / ~2.9 GiB real, 98.10% hit ratio.
- [ ] **Decide whether to reclaim RAM from TrueNAS.** Only ~2.9 GB of its 24 GB is real process
      memory; the rest is ARC. But the 98.10% hit ratio against 317M NFS reads is what makes
      streaming and library scans fast, so shrinking it is a genuine trade. Watch the hit ratio
      trend in Grafana for a few weeks before deciding.
- [x] ~~**Move `immich-machine-learning` to jarvis.**~~ Done 2026-08-10 on the ROCm image: 24.0 →
      61.9 img/s at 8-way concurrency, GPU verified at 64%.
- [ ] **Remove the fallback ML container from cloud-ct** after a clean week (i.e. on/after
      2026-08-17). Frees ~1.2 GB. Until then it is deliberately running but unused.
- [ ] **Confirm Immich ML end-to-end on the next upload.** The health probe passes and Immich
      logged the jarvis server as healthy, but no ML work was queued at cutover time, so real
      inference through the new path has not been observed yet.
- [ ] **Consider automatic ML failover.** `IMMICH_MACHINE_LEARNING_URL` takes one URL, so fallback
      is currently manual. Setting `machineLearning.urls` as an array in Admin → Settings → Machine
      Learning would fail over automatically, at the cost of moving the setting out of this repo.
- [ ] **Look at `paperless-ai`** — peaks at 1.78 GB, larger than the entire Nextcloud stack, for an
      auxiliary service.
- [x] ~~**Refresh Ollama models on `jarvis`**~~ Done 2026-08-12: pruned 15 models → 4, freeing
      220 GB (disk 21% → 9%). `qwen2.5vl:32b` kept — paperless-gpt depends on it. Replacements
      deliberately not pulled; `ollama pull` on demand when a real need appears.
- [ ] **TrueNAS SSH is disabled** (201 refuses port 22): decide whether to enable it for
      automation, or document the web UI / Proxmox console as the only management path.

## Defects found in the 2026-08-10 access sweep

- [x] ~~**Proxmox host (200) is not monitored at all.**~~ Fixed 2026-08-10: `prometheus-node-exporter`
      installed natively on the hypervisor and added to the Prometheus `node` job as host
      `proxmox`. Let it accumulate history before making sizing decisions from it.
- [x] ~~**Traefik's Docker provider is broken.**~~ Fixed 2026-08-12 by upgrading `traefik:v3.0`
      (3.0.4) → `v3.7.10`. Provider errors went 290-per-10-min → 0 and the dashboard returns 401
      (auth challenge) instead of 404. Certificate serial unchanged, so nothing was re-issued.
      Note: `DOCKER_API_VERSION` does **not** work around this — v3.0 hardcodes API 1.24 and
      ignores the variable. Verified against a throwaway container before touching ingress.
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
- [x] ~~**Audit repo compose files against what is actually deployed.**~~ Done 2026-08-15: 25 stacks
      diffed, 18 identical, 7 drifting, all reconciled. Found VaultWarden and Mealie with open
      registration live, and Plex running `privileged: true`. All 25 now identical.
- [ ] **Audit mounted config files and `.env` structure** — the compose audit did not cover
      Traefik's `config.yml`, Prometheus, Promtail or Loki configs. `prometheus.yml` was
      spot-checked (clean); the rest are unverified and a plausible source of drift.
- [ ] **Standardise on one compose filename.** Every host mixes `docker-compose.yml` and
      `.yaml` — `dnspi` has one of each. This caused two failed deploys on 2026-08-15. Until it is
      fixed, any automation must glob `docker-compose.y*ml`.

## Media

- [ ] **Add ~20 regional films to TMDB** so Radarr and Plex can identify them (currently sitting in
      `downloads/radarr`, e.g. Bhagubai 2026, Chennai Central 2020, Frame 2026, Tighee 2026,
      Vastupurush 2002). Until then they stay unmonitored with Plex reading names from filenames.
