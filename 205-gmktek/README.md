# 205 — GMKTec Evo-X2

**Hostname:** `jarvis`
**IP:** 192.168.1.205
**OS:** Ubuntu Server 24.04

## Hardware

| Component | Details |
|---|---|
| Device | [GMKTec EVO-X2](https://www.gmktec.com/products/evo-x2-ai-mini-pc) |
| Board | [Sixunited AXB35-02](https://strixhalo.wiki/Hardware/Boards/Sixunited_AXB35) |
| SoC | [AMD Ryzen AI MAX+ 395](https://www.amd.com/en/products/processors/laptop/ryzen/ai-max.html) (Strix Halo) |
| RAM | 128 GB LPDDR5 unified (96 GB UMA allocated to GPU, 32 GB OS) |
| Storage | ADATA Legend 900 2 TB NVMe |
| BIOS | 1.05 — see [BIOS update procedure](bios-update.md) |
| EC | 1.01.03 |

## Role

Local AI inference server running Ollama with OpenWebUI as a frontend. Strix Halo's unified memory lets the iGPU address up to ~112 GB of system RAM with no PCIe transfer overhead — ideal for large local LLMs.

## Setup

1. [Enable SSH server](../guides/ssh.md)
2. [Set a static IP](../guides/static-ip.md)
3. [Install Docker](../guides/docker-install.md)
4. Deploy stacks:
   1. `docker/portainer/` — see [Portainer Edge Agent guide](../guides/portainer-edge-agent.md)
   2. `docker/ollama/`
   3. `docker/openwebui/`

## Maintenance

- [BIOS update procedure](bios-update.md) — how to flash AMI BIOS via Hiren's BootCD PE WinPE

## Docker Stacks

| Folder | Services |
|---|---|
| [docker/portainer/](docker/portainer/) | Portainer Edge Agent |
| [docker/ollama/](docker/ollama/) | Ollama |
| [docker/openwebui/](docker/openwebui/) | OpenWebUI |
