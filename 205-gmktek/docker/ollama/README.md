# Ollama

Local LLM inference server running natively on Jarvis (not in Docker). Uses the AMD Radeon 8060S iGPU (gfx1151, Strix Halo) via ROCm 7.2 for hardware-accelerated inference.

## Hardware

| Component | Details |
|-----------|---------|
| GPU | AMD Radeon 8060S (gfx1151, Strix Halo iGPU) |
| GPU memory | 96 GiB UMA + GTT spillover → ~111.5 GiB visible to ollama |
| System ROCm | 7.2.0 (from `repo.radeon.com/rocm/apt/7.2`) |
| Kernel | `6.17.0-oem` (ships amdgpu in-tree, no DKMS module) |

## Access

| Interface | URL |
|-----------|-----|
| API | `http://192.168.1.205:11434` |

## Installation

Ollama is installed as a systemd service, **built from source** against system ROCm 7.2. The stock binary from `https://ollama.com/install.sh` ships older bundled ROCm libs whose SONAMEs don't match system ROCm 7.2 — the from-source build links against system `/opt/rocm` with native gfx1151 support, so no compatibility shims are needed.

### Build deps (one-time)

```bash
sudo apt install -y golang-go cmake ninja-build build-essential tmux
```

### Build from source

```bash
# Pull source and pin to a stable tag
git clone https://github.com/ollama/ollama ~/ollama-src
cd ~/ollama-src
git checkout v0.30.10   # bump to the latest stable when rebuilding

# Configure for ROCm 7 with system /opt/rocm
cmake --preset 'ROCm 7' -B build -DCMAKE_PREFIX_PATH=/opt/rocm

# Compile HIP runners + CPU variants (~10–15 min on Strix Halo).
# Use tmux so SSH drops don't kill the build.
tmux new -s ollama-build
cmake --build build --parallel
go build -o ollama .
# Ctrl+B then D to detach; `tmux attach -t ollama-build` to come back.
```

### Install built artifacts

```bash
sudo systemctl stop ollama
sudo rm -rf /usr/local/lib/ollama
sudo cp -a ~/ollama-src/dist/lib/ollama /usr/local/lib/ollama
sudo cp ~/ollama-src/ollama /usr/local/bin/ollama
```

The new layout is `/usr/local/lib/ollama/rocm/` containing all `libggml-*.so` runners, the bundled ROCm 7 sibling libs, and `rocblas/library/` tensile kernels for every supported gfx target including `gfx1151`.

### Systemd override

Override at `/etc/systemd/system/ollama.service.d/override.conf` should be **empty** (just the `[Service]` header) — no `HSA_OVERRIDE_GFX_VERSION`, no `LD_LIBRARY_PATH`. The runner resolves all deps via system `/opt/rocm` plus its own RUNPATH.

```bash
sudo tee /etc/systemd/system/ollama.service.d/override.conf <<'EOF'
[Service]
EOF
sudo systemctl daemon-reload
sudo systemctl start ollama
```

## Upgrading ollama

**Never run `curl -fsSL https://ollama.com/install.sh | sh`** — it overwrites `/usr/local/bin/ollama` *and* `/usr/local/lib/ollama/` with the stock build whose bundled ROCm libs don't match system 7.2. Ollama then silently falls back to CPU.

To upgrade, always rebuild from source:

```bash
cd ~/ollama-src
git fetch
git checkout <new-stable-tag>
cmake --preset 'ROCm 7' -B build -DCMAKE_PREFIX_PATH=/opt/rocm
cmake --build build --parallel
go build -o ollama .

sudo systemctl stop ollama
sudo rm -rf /usr/local/lib/ollama
sudo cp -a ~/ollama-src/dist/lib/ollama /usr/local/lib/ollama
sudo cp ~/ollama-src/ollama /usr/local/bin/ollama
sudo systemctl start ollama
```

## Verification

After install or restart, confirm GPU detection:

```bash
sudo journalctl -u ollama --since "30 seconds ago" --no-pager | grep -iE 'library|vram|inference'
```

Look for `library=ROCm`, `compute=gfx1151`, `type=iGPU`, and `total_vram` around 111 GiB. If you see `library=cpu` or `total_vram="0 B"`, the GPU path is broken — start with `ldd /usr/local/lib/ollama/rocm/libggml-hip.so` to find unresolved deps.

Watch GPU utilization during inference:

```bash
watch -n 1 /opt/rocm/bin/rocm-smi
```

## Models

Models live at `/usr/share/ollama/.ollama/models` (service user).

```bash
ollama list           # list installed models
ollama pull <model>   # download a model
ollama run <model>    # run interactively
```

## Service management

```bash
sudo systemctl status ollama
sudo systemctl restart ollama
journalctl -u ollama -n 50 --no-pager
```

## Notes

- Open WebUI (separate stack at `docker/openwebui/`) connects via `host.docker.internal:11434`.
- 111.5 GiB total VRAM = 96 GiB dedicated UMA (set in BIOS Advanced → GFX Configuration) + ~15 GiB GTT spillover (system RAM the GPU can borrow on demand).
- The empty `docker-compose.yml` next to this README is intentional — ollama runs natively. The file is kept as a marker so the directory shows up in tooling that lists docker stacks.
