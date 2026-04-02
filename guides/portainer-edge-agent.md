# Portainer Edge Agent Setup

Each non-RasPi machine runs a Portainer Edge Agent that dials out to the Portainer CE instance on RasPi5 (192.168.1.199). No inbound ports need to be opened on the agent machine.

## Step 1 — Generate credentials in Portainer UI

1. Open `https://portainer.local.wilfredtuscano.com`
2. Go to **Environments → Add environment**
3. Select **Edge Agent**
4. Fill in:
   - **Name:** hostname of the machine (e.g. `starr`, `plex`, `cloud`, `gmktek`)
   - **Portainer API server URL:** `https://192.168.1.199:9443`
5. Click **Create environment**
6. Copy the generated **Edge ID** and **Edge key**

## Step 2 — Create .env on the agent machine

```bash
cd ~/docker/portainer
cp .env.example .env
nano .env
```

Fill in:
```
EDGE_ID=<paste Edge ID>
EDGE_KEY=<paste Edge key>
```

## Step 3 — Start the agent

```bash
docker compose up -d
```

## Step 4 — Verify in Portainer UI

Go to **Environments** — the new environment should show a heartbeat within ~30 seconds.

If it shows "not associated", check that the Portainer API server URL used in Step 1 was the direct IP (`https://192.168.1.199:9443`) rather than a hostname.
