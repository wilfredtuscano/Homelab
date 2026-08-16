# 214 — LXC: Cloud (Container)

**IP:** 192.168.1.204 (took over from VM 204 after migration)
**OS:** Ubuntu 22.04 LTS
**Host:** Proxmox (192.168.1.200)
**Type:** Privileged LXC container

## LXC Specs

| Resource | Value |
|---|---|
| vCPU | 6 cores |
| RAM | 12 GB |
| Swap | 512 MB |
| Disk | 80 GB (local-nvme — Samsung PM9A1 1TB) |

> Migrated from VM 204 to remove full-OS overhead and put MariaDB / SQLite databases on the fast local NVMe pool.
>
> Raised from 4 cores / 8 GB on 2026-08-10. Over the preceding 30 days this CT saturated all 4
> cores (`immich-server` peaked at 219%, `immich-machine-learning` at 187%) and hit 76% of its RAM
> with a rising trend of ~0.04 GB/day. Funded by reclaiming 2 GB each from starr-ct and plex-ct, so
> total host allocation was unchanged.

## Role

Self-hosted cloud services: password manager, photo sync, document management (with local-LLM
enrichment against Ollama on `jarvis`), recipes, and task management.

> **Densest host in the lab.** 19 containers across 7 stacks (was 23 across 8 before Nextcloud was
> decommissioned on 2026-08-16). See [Resource allocation](../README.md#resource-allocation).

## Setup

See [guides/lxc-docker.md](../../guides/lxc-docker.md) for the base LXC + Docker setup procedure.

LXC config in `/etc/pve/lxc/214.conf` on the Proxmox host (no special device passthrough needed — unlike starr/plex):

```
features: mount=nfs,nesting=1,fuse=1
lxc.apparmor.profile: unconfined
```

1. Create privileged LXC in Proxmox UI on `local-nvme` storage (see guide)
2. Add NFS passthrough + AppArmor unconfined to LXC config
3. Install Docker with fuse-overlayfs storage driver
4. Create `cloud` user (uid 1000)
5. Mount the NFS shares from TrueNAS (see NFS Mounts below)
6. Deploy stacks

## Docker Stacks

| Folder | Services | Host Port |
|---|---|---|
| [docker/portainer-agent/](docker/portainer-agent/) | Portainer Edge Agent | — |
| [docker/monitoring-agent/](docker/monitoring-agent/) | Promtail, node-exporter, cAdvisor | 9080 (cadvisor) |
| [docker/vaultwarden/](docker/vaultwarden/) | VaultWarden | 8082 → 80 |
| [docker/mealie/](docker/mealie/) | Mealie recipe manager | 9000 |
| [docker/immich/](docker/immich/) | Immich server, machine-learning, PostgreSQL, Redis | 2283 |
| [docker/paperless/](docker/paperless/) | Paperless-ngx, PostgreSQL, Redis broker, Gotenberg, Tika, Paperless-AI, Paperless-GPT | 8000 (ngx), 8080 (gpt), 3000 (ai) |
| [docker/vikunja/](docker/vikunja/) | Vikunja, PostgreSQL | 3456 |
| ~~[docker/nextcloud/](docker/nextcloud/)~~ | ~~NextCloud, MariaDB, Redis, Collabora~~ | **decommissioned 2026-08-16** |

> **Nextcloud was decommissioned on 2026-08-16** and is no longer deployed. A usage audit found
> ~23 MB of live user data, mostly Nextcloud's own sample files — Immich and Paperless-ngx had
> absorbed the real work. Its Deck (kanban) content, the only substantive data, was migrated into
> Vikunja first. `docker/nextcloud/` stays in the repo as reference-only; a full
> backup is at `~/nextcloud-decom-20260816/` on this CT and `/mnt/nfs/nextcloud` is untouched.
> See [docker/nextcloud/README.md](docker/nextcloud/README.md).

Traefik on 199 routes traffic via file provider — see `199-raspi5/docker/traefik/data/config.yml`.

## NFS Mounts

```
192.168.1.201:/mnt/Vault/Immich     /mnt/nfs/immich     nfs  defaults  0  0
192.168.1.201:/mnt/Vault/Paperless  /mnt/nfs/paperless  nfs  defaults  0  0
192.168.1.201:/mnt/Vault/Nextcloud  /mnt/nfs/nextcloud  nfs  defaults  0  0   # retained, unused
```

NFS access requires enabling the `mount` feature in LXC Options → Features in the Proxmox UI.

> The `Nextcloud` mount is kept after that stack was decommissioned so its data stays reachable.
> Removing the dataset is a separate, deliberate decision.

## TrueNAS — NFS dataset setup

One dataset per bulk-data app. **Databases never live on NFS** — the PostgreSQL instances all use
local bind mounts (`./db`) on the NVMe rootfs, for speed and to avoid file-locking problems over NFS.

```bash
# In TrueNAS Shell — set ownership to uid=1000 (matches cloud user and PUID in compose)
chown -R 1000:1000 /mnt/<pool>/<Dataset>
chmod -R 750 /mnt/<pool>/<Dataset>
```

## VaultWarden — post-install

1. Temporarily set `SIGNUPS_ALLOWED=true`, restart, create your account.
2. Set `SIGNUPS_ALLOWED=false` and restart:
   ```bash
   docker compose up -d
   ```
3. Use any Bitwarden-compatible client (iOS, Android, browser extension) — point server to `https://vaultwarden.local.wilfredtuscano.com`.
