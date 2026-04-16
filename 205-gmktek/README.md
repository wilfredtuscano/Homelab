# 205 — GMKTec Evo-X2

**IP:** 192.168.1.205
**OS:** Ubuntu Server

## Hardware

| Component | Details |
|---|---|
| Device | GMKTec Evo-X2 |
| SoC | AMD Strix Halo |
| RAM | 128 GB (64 GB UMA allocated to GPU) |

## Role

Local AI inference server running Ollama with OpenWebUI as a frontend.

## Setup

1. [Enable SSH server](../guides/ssh.md)
2. [Set a static IP](../guides/static-ip.md)
3. [Install Docker](../guides/docker-install.md)
4. Deploy stacks:
   1. `docker/portainer/` — see [Portainer Edge Agent guide](../guides/portainer-edge-agent.md)
   2. `docker/ollama/`
   3. `docker/openwebui/`

## Docker Stacks

| Folder | Services |
|---|---|
| [docker/portainer/](docker/portainer/) | Portainer Edge Agent |
| [docker/ollama/](docker/ollama/) | Ollama |
| [docker/openwebui/](docker/openwebui/) | OpenWebUI |
