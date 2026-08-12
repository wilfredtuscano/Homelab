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
4. Install Ollama natively (built from source against system ROCm — see note below)
5. Deploy stacks:
   1. `docker/portainer/` — see [Portainer Edge Agent guide](../guides/portainer-edge-agent.md)
   2. `docker/openwebui/`

## Maintenance

- [BIOS update procedure](bios-update.md) — how to flash AMI BIOS via Hiren's BootCD PE WinPE

## Docker Stacks

| Folder | Services |
|---|---|
| [docker/portainer/](docker/portainer/) | Portainer Edge Agent |
| [docker/openwebui/](docker/openwebui/) | OpenWebUI (port 3000) |
| [docker/immich-ml/](docker/immich-ml/) | Immich machine-learning, ROCm (port 3003) — serves Immich on cloud-ct |
| [monitoring-agent/](../monitoring-agent/) | Promtail, node-exporter, cAdvisor (shared stack) |

### Immich ML offload

Immich's machine-learning container runs here rather than on cloud-ct (214), where it used to
saturate every core during bulk import. Measured on CLIP ViT-B-32 at 8-way concurrency:

| Where | Throughput |
|---|---|
| cloud-ct, 6 cores, shared with 22 containers | 24.0 img/s |
| jarvis, CPU image | 38.5 img/s |
| **jarvis, ROCm image** | **61.9 img/s** |

Single-image latency is ~0.12s everywhere — the gain is throughput under concurrency, which is the
case that actually caused trouble. GPU use verified at 64% during a sustained run.

The ROCm image is **23.6 GB** unpacked, against 1.29 GB for the CPU variant. That is the price of
the 2.6x.

### Model library

Pruned 2026-08-12 from 15 models / ~290 GB down to 4 / ~59 GB, freeing **220 GB**. Disk went from
21% to 9%.

| Model | Size | Why it is kept |
|---|---|---|
| `qwen2.5vl:32b` | 21 GB | **Load-bearing** — paperless-gpt uses it for both `LLM_MODEL` and `VISION_LLM_MODEL`. Do not remove. |
| `mistral-small3.2:24b` | 15 GB | General-purpose |
| `qwen3-coder:30b` | 18 GB | Coding |
| `qwen2.5-coder:7b` | 4.7 GB | Small/fast coding |

Removed: eleven models pulled 11–12 months earlier (`llama3.3:70b`, `deepseek-r1:70b`,
`gpt-oss:120b`, `gpt-oss:20b`, `qwen3:30b`, `codellama:34b`, `codellama:7b`, `codegemma:7b`,
`deepseek-coder-v2:16b`, `deepseek-r1:1.5b`) plus `mistral-small3.1:24b`, which was strictly
superseded by the `3.2` already present.

Before removing anything, check what references it. As of the prune the only traceable consumer of
Ollama was paperless-gpt; paperless-ai has no LLM configured, and Open WebUI's database held zero
chats. Anything removed can be re-pulled on demand — `ollama pull` is cheap, 220 GB of stale
weights is not.

### Ollama is **not** a Docker stack

Ollama runs as a **native systemd service** on port `11434`, built from source against the
system ROCm install so it uses the gfx1151 iGPU directly. `docker/ollama/` holds an intentionally
empty `docker-compose.yml` as a directory marker only — do not deploy it.

Never install or upgrade Ollama with `curl … install.sh | sh`: the stock build ships its own ROCm
libraries that do not match the system ROCm, and it silently falls back to CPU. Upgrade only by
rebuilding from source.
