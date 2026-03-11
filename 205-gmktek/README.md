# 205 — GMKTec Evo-X2

**IP:** 192.168.1.205
**OS:** Ubuntu Server

## Role

Local AI inference server running Ollama with OpenWebUI as a frontend.

## Setup

1. [Set a static IP](../guides/static-ip.md)
2. [Install Docker](../guides/docker-install.md)
3. Deploy stacks:
   1. `docker/portainer/`
   2. `docker/ollama/`
   3. `docker/openwebui/`

## Docker Stacks

| Folder | Services |
|---|---|
| [docker/portainer/](docker/portainer/) | Portainer, Watchtower |
| [docker/ollama/](docker/ollama/) | Ollama |
| [docker/openwebui/](docker/openwebui/) | OpenWebUI |
