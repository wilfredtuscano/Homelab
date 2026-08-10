# Monitoring (Central Stack)

Central observability stack running on RasPi5. Collects logs and metrics from all VMs, provides a single web UI for dashboards and alerts.

Accessible at: `https://grafana.local.wilfredtuscano.com`

## What's inside

### Loki
Log aggregation database — the destination for all logs shipped by Promtail agents. Stores logs indexed by labels (host, container name) rather than full-text, keeping storage very small (~50–300 MB/month for this homelab).

- Logs retained for 30 days
- Queried in Grafana using LogQL (e.g. `{host="cloud", container="nextcloud"}`)
- Listens on port `3100` (also exposed on host so Promtail agents on other VMs can reach it)

### Prometheus
Metrics database — scrapes Node Exporter and cAdvisor on all 5 VMs every 15 seconds and stores the time-series data locally.

- Metrics retained for 30 days
- Queried in Grafana using PromQL
- Listens on port `9090`
- Scrape targets defined in `prometheus/prometheus.yml`

### Grafana
The web UI. Connects to both Loki (logs) and Prometheus (metrics) and provides:
- Dashboards for system metrics and container stats
- Log explorer for searching across all VMs
- Alerting with Discord/email notifications

- Listens on port `3001`, routed via Traefik at `grafana.local.wilfredtuscano.com`
- Loki and Prometheus datasources are auto-provisioned on first boot

## Setup

1. Start the stack:
   ```bash
   docker compose up -d
   ```

2. Open Grafana at `https://grafana.local.wilfredtuscano.com`
   - Default credentials: `admin` / `admin` (change on first login)

3. Fix bind mount permissions before starting (Grafana runs as UID 472, Loki as 10001, Prometheus as 65534):
   ```bash
   mkdir -p grafana/data loki/data prometheus/data
   sudo chown -R 472:472 grafana/data
   sudo chown -R 10001:10001 loki/data
   sudo chown -R 65534:65534 prometheus/data
   ```

4. Import community dashboards (Dashboards → Import → enter ID):
   | Dashboard | ID |
   |-----------|-----|
   | Node Exporter Full (system metrics) | `1860` |
   | cAdvisor (container metrics) | `14282` |

   For each imported dashboard, go to Settings → Variables and add any missing datasource variables:
   - Name: `DS_PROMETHEUS`, Type: `Data source`, Data source type: `Prometheus`

   For logs, use **Explore** (compass icon) with Loki datasource and LogQL queries:
   - All logs from a host: `{host="starr"}`
   - Specific container: `{container="sonarr"}`

5. Set up Discord alerting: Alerting → Contact points → Add Discord webhook

## Storage

All data is stored in local bind mounts on RasPi5:

| Path | Contents |
|------|----------|
| `./loki/data` | Loki log chunks and index |
| `./prometheus/data` | Prometheus metrics |
| `./grafana/data` | Grafana config, dashboards, alert rules |

## Scrape coverage

| Job | Source | Covers |
|---|---|---|
| `node` | Node Exporter | 199, **200 (native pkg)**, 202, 203, 204, 205 |
| `cadvisor` | cAdvisor | 202, 203, 204, 205 (no Docker on 200) |
| `pve` | pve-exporter | Every Proxmox guest — VM 201 and LXC 212/213/214 |
| `snmp-truenas` | snmp-exporter | 201 in-guest — ZFS ARC, memory, CPU, pools, interfaces |

### snmp-exporter — TrueNAS

TrueNAS Core cannot run a node exporter (read-only FreeBSD base), so it is scraped over SNMP.
This is the only source that separates **ZFS ARC from real memory use** — the `pve` job cannot,
because ARC expands to fill the VM's allocation and so reports ~95% forever.

Config is deliberately split so no secret is committed:

| File | In git? | Holds |
|---|---|---|
| `snmp/snmp.yml` | yes | Module definitions — OIDs, metric names, lookups |
| `snmp/auth.yml` | **no** | The community string. See `snmp/auth.yml.example` |

`snmp_exporter` merges repeated `--config.file` arguments, which is what makes the split work.

> `--config.expand-environment-variables` is **broken in snmp_exporter 0.30.1** — a `${VAR}`
> placeholder is sent to the wire verbatim as the community, and the only symptom is a scrape
> timeout. Confirmed with `tcpdump` on the TrueNAS side. Don't try to reintroduce the env-var
> approach without re-testing it.

Useful queries:

```promql
truenas_zfs_arc_size_kib / 1024 / 1024                     # ARC size in GiB
truenas_zfs_arc_hit_ratio_percent                          # cache effectiveness
(truenas_memory_total_real_kib
   - truenas_memory_avail_real_kib
   - truenas_zfs_arc_size_kib) / 1024 / 1024               # real (non-ARC) usage in GiB
truenas_zpool_used_units * truenas_zpool_alloc_unit_bytes   # pool bytes used, by pool
```

### pve-exporter

Queries the Proxmox API directly and reports per-guest CPU, memory and disk for every VM and
container. It is the **only** source covering TrueNAS (VM 201), which runs no in-guest exporter.

Auth is a read-only API token (`prometheus@pve!monitoring`, role `PVEAuditor`) created with:

```bash
pveum user add prometheus@pve
pveum acl modify / --user prometheus@pve --role PVEAuditor
pveum user token add prometheus@pve monitoring --privsep 0
```

The token value goes in `.env` as `PVE_TOKEN_VALUE` (gitignored). The container is not published
on a host port — Prometheus reaches it over the compose network at `pve-exporter:9221`.

> **Reading the TrueNAS memory figure correctly.** VM 201 has ballooning disabled, so
> `pve_memory_usage_bytes` reports what the host has *committed*, not what the guest needs — it
> sits around 95% permanently because ZFS ARC inside TrueNAS expands to fill whatever it is given.
> Right-sizing TrueNAS requires in-guest metrics (SNMP), not this number.

## Dependencies

Each monitored host must be running the monitoring agent stack from `monitoring-agent/`. See
[monitoring-agent README](../../../monitoring-agent/README.md). The Proxmox host is the exception —
it runs the Debian `prometheus-node-exporter` package instead, and pve-exporter needs nothing
installed on the guests at all.
