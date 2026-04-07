# Monitoring Agent

A lightweight agent stack deployed on **every VM** to collect logs and metrics. Data is shipped to the central monitoring stack on RasPi5 (192.168.1.199).

## What's inside

### Promtail
A log shipping agent. It reads the Docker container logs on the host and forwards them to Loki on RasPi5. Each log line is tagged with the container name and the host VM so you can search and filter in Grafana (e.g. "show me all nextcloud logs from the cloud VM").

- Reads logs via Docker socket — no changes needed to any app containers
- Pushes to Loki at `http://192.168.1.199:3100`
- Uses `AGENT_HOST` env var to tag logs with the VM name

### Node Exporter
Exposes OS-level system metrics for Prometheus to scrape. Think of it as a system stats exporter — everything you'd see in `htop` or `df`, but as queryable metrics.

Metrics include: CPU usage, memory usage, disk I/O, filesystem space, network throughput, system load.

- Listens on port `9100`
- Prometheus on RasPi5 scrapes this every 15s

### cAdvisor (Container Advisor)
Exposes per-container resource metrics. While Node Exporter tells you "the VM is using 2GB RAM", cAdvisor tells you "nextcloud is using 300MB, mariadb is using 400MB, redis is using 50MB".

- Made by Google, designed for Docker/Kubernetes environments
- Listens on port `9080` (container runs on 8080, mapped to host 9080)
- Prometheus on RasPi5 scrapes this every 15s

## Deploying on a VM

1. Copy this folder to `~/docker/monitoring-agent/` on the VM

2. Create a `.env` file (gitignored):
   ```
   AGENT_HOST=<hostname>
   ```

   | VM | AGENT_HOST |
   |----|------------|
   | RasPi5 (192.168.1.199) | `raspi5` |
   | Starr (192.168.1.202) | `starr` |
   | Plex (192.168.1.203) | `plex` |
   | Cloud (192.168.1.204) | `cloud` |
   | Jarvis (192.168.1.205) | `jarvis` |

3. Start the stack:
   ```bash
   docker compose up -d
   ```

Node Exporter and cAdvisor are immediately active. Promtail will retry connecting to Loki until the central monitoring stack on RasPi5 is running.

## Ports

| Service | Host Port | Purpose |
|---------|-----------|---------|
| Node Exporter | 9100 | Scraped by Prometheus |
| cAdvisor | 9080 | Scraped by Prometheus |
| Promtail | — | Pushes to Loki (no inbound port) |
