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

### Building / upgrading Ollama from source

Ollama is built from source against the system ROCm so it uses the gfx1151 iGPU natively. Last
built **2026-08-15 at `v0.32.13`**.

The build interface changed between 0.30 and 0.32 — the old `cmake --preset 'ROCm 7'` no longer
exists. Current process:

```bash
cd ~/ollama-src
git fetch --tags origin && git checkout v<VERSION>

# Configure. There is a backend matching each ROCm release; pick the one that
# matches /opt/rocm/.info/version. gfx1151 is Strix Halo.
export PATH=/opt/rocm/bin:$PATH
cmake -B build . -DOLLAMA_LLAMA_BACKENDS=rocm_v7_2 -DCMAKE_HIP_ARCHITECTURES=gfx1151 \
      -DCMAKE_PREFIX_PATH=/opt/rocm

cmake --build build --parallel
go build -o ollama .
```

Verify before configuring further: `grep OLLAMA_LLAMA_BACKENDS build/CMakeCache.txt` should show
`rocm_v7_2`, and `cmake --build build --target help | grep rocm` should list
`ollama-llama-server-rocm_v7_2`. A configure that silently omits the ROCm backend produces a
CPU-only build.

Go version is handled automatically — `go.mod` requires a newer Go than the system package, and
`GOTOOLCHAIN=auto` fetches it into `$GOPATH`. No system Go change is needed.

**Test before installing.** Run the new binary on a spare port against the real model store:

```bash
cd ~/ollama-src
OLLAMA_HOST=127.0.0.1:11435 \
OLLAMA_MODELS=/usr/share/ollama/.ollama/models \
OLLAMA_LIBRARY_PATH=$HOME/ollama-src/build/lib/ollama ./ollama serve
# in another shell:
OLLAMA_HOST=127.0.0.1:11435 ./ollama run qwen2.5-coder:7b "hi"
OLLAMA_HOST=127.0.0.1:11435 ./ollama ps    # PROCESSOR must read 100% GPU
```

**Install — stop the service first**, or copying the binary fails with `Text file busy` because the
running process holds it open:

```bash
sudo systemctl stop ollama
sudo rm -rf /usr/local/lib/ollama
sudo cp -a ~/ollama-src/build/lib/ollama /usr/local/lib/ollama
sudo cp ~/ollama-src/ollama /usr/local/bin/ollama
sudo systemctl start ollama
```

The library layout changed too: 0.30 installed `lib/ollama/rocm/`, 0.32 installs `lib/ollama/`
plus a `rocm_v7_2/` subdirectory. Replace the whole directory rather than copying over it.

> **Mismatched binary and libraries fall back to CPU silently.** This happened during the 0.32.13
> upgrade: the library copy succeeded, the binary copy failed with `Text file busy`, and the
> service restarted clean — `systemctl is-active` said `active` and the API returned HTTP 200
> while every request ran on CPU. The only signal was the startup log:
> ```
> msg="inference compute" id=cpu library=cpu      # BAD - CPU only
> msg="inference compute" id=0 library=ROCm compute=gfx1151 libdirs=ollama,rocm_v7_2   # GOOD
> ```
> After any upgrade, check that line and run an inference confirming `100% GPU`. Service status
> and API health prove nothing here.

Keep a rollback before upgrading — `cp` the current binary and `/usr/local/lib/ollama` aside first.

### Ollama is **not** a Docker stack

Ollama runs as a **native systemd service** on port `11434`, built from source against the
system ROCm install so it uses the gfx1151 iGPU directly. `docker/ollama/` holds an intentionally
empty `docker-compose.yml` as a directory marker only — do not deploy it.

Never install or upgrade Ollama with `curl … install.sh | sh`: the stock build ships its own ROCm
libraries that do not match the system ROCm, and it silently falls back to CPU. Upgrade only by
rebuilding from source.
