# Ollama

Local LLM inference server running natively on Jarvis (not in Docker). Uses the AMD Radeon 8060S iGPU (gfx1151) via ROCm for hardware-accelerated inference.

## Hardware

| Component | Details |
|-----------|---------|
| GPU | AMD Radeon 8060S (gfx1151, Strix Halo) |
| VRAM | 64 GiB UMA (allocated from 128 GiB system RAM) |
| ROCm | 7.2.0 |

## Access

| Interface | URL |
|-----------|-----|
| API | `http://192.168.1.205:11434` |

## Installation

Ollama is installed as a systemd service via the official install script, then **rebuilt from source** against the system ROCm 7.2.0. The stock Ollama binary bundles ROCm 6.3 internally which causes a SIGSEGV crash on gfx1151 with ROCm 7.2. Building from source compiles against the system ROCm and fixes this.

### Build from source

```bash
# Install dependencies
sudo apt install -y golang-go cmake build-essential git

# Clone and build
git clone https://github.com/ollama/ollama ~/ollama-src
cd ~/ollama-src
export ROCM_PATH=/opt/rocm
export PATH=$PATH:/opt/rocm/bin
go generate ./...   # compiles GPU backends — takes 10-20 min
go build -o ollama .

# Replace binary
sudo pkill -f ollama
sudo cp ~/ollama-src/ollama /usr/local/bin/ollama
sudo systemctl start ollama
```

### HSA override

The systemd service has an override to skip the ROCm GFX compatibility check:

```bash
cat /etc/systemd/system/ollama.service.d/override.conf
```

```ini
[Service]
Environment="HSA_OVERRIDE_GFX_VERSION=11.0.0"
```

## Important: upgrading Ollama

**Do not use `curl -fsSL https://ollama.com/install.sh | sh` to upgrade** — this overwrites the binary with the stock build (bundled ROCm 6.3) which will crash on this machine. Always rebuild from source after pulling the latest:

```bash
cd ~/ollama-src
git pull
go generate ./...
go build -o ollama .
sudo pkill -f ollama
sudo cp ~/ollama-src/ollama /usr/local/bin/ollama
sudo systemctl start ollama
```

## Models

Models are stored at `/usr/share/ollama/.ollama/models` (service user) or `~/.ollama/models` (jarvis user).

```bash
ollama list        # list installed models
ollama pull <model>  # download a model
ollama run <model>   # run interactively
```

## Service management

```bash
sudo systemctl status ollama
sudo systemctl restart ollama
journalctl -u ollama -n 50 --no-pager
```

## Notes

- Open WebUI (separate stack at `docker/openwebui/`) connects to Ollama via `host.docker.internal:11434`
- Monitor GPU usage during inference: `watch -n 1 /opt/rocm/bin/rocm-smi`
