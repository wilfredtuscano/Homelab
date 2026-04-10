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

## Dependencies

Each VM must be running the monitoring agent stack from `monitoring-agent/`. See [monitoring-agent README](../../../monitoring-agent/README.md).
