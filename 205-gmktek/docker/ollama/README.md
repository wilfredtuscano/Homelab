# Ollama

Local LLM inference server running natively on Jarvis (not in Docker). Uses the AMD Radeon 8060S iGPU (gfx1151, Strix Halo) via ROCm 7.2.4 for hardware-accelerated inference.

## Hardware

| Component | Details |
|-----------|---------|
| GPU | AMD Radeon 8060S (gfx1151, Strix Halo iGPU) |
| GPU memory | 96 GiB UMA carve-out; Ollama reports `total="96.0 GiB"`, `available` about 95.8 GiB (needs the local carve-out patch, see below) |
| System ROCm | 7.2.4 (from `repo.radeon.com/rocm/apt/7.2.4`) |
| Kernel | `7.0.x` HWE (ships amdgpu in-tree, no DKMS module); see [Kernel track](../../README.md#kernel-track) |
| Ollama | `v0.40.15` plus the carve-out patch, built 2026-11-11 |

## Access

| Interface | URL |
|-----------|-----|
| API | `http://192.168.1.205:11434` |

## Installation

Ollama is a systemd service, **built from source** against the system ROCm. The full build, test
and install procedure, including the local patch, lives in
[`205-gmktek/README.md`, "Building / upgrading Ollama from source"](../../README.md#building--upgrading-ollama-from-source).
In short:

- Build each version in its own git worktree (`~/ollama-v<VERSION>`) and apply
  [`patches/ollama-igpu-carveout.patch`](../../patches/ollama-igpu-carveout.patch). Without it
  Ollama caps the iGPU at free system RAM and sees about 27 GiB instead of 96.
- Configure with `-DOLLAMA_LLAMA_BACKENDS=rocm_v7_2 -DCMAKE_HIP_ARCHITECTURES=gfx1151`. The
  `cmake --preset 'ROCm 7'` interface was removed in 0.32.
- The build copies the ROCm runtime from `/opt/rocm` into `lib/ollama/rocm_v7_2/` (the installed
  `libamdhip64.so.7.2.70204` is byte-identical to the system 7.2.4 one). A system ROCm upgrade
  only reaches Ollama after a rebuild.
- Install by stopping the service, then replacing **both** `/usr/local/bin/ollama` and the whole
  `/usr/local/lib/ollama/` directory. Keep the previous pair as `*.bak-<OLD>` for rollback.

### Systemd override

`/etc/systemd/system/ollama.service.d/override.conf` sets only tuning, no `HSA_OVERRIDE_GFX_VERSION`
and no `LD_LIBRARY_PATH`:

```ini
[Service]
Environment="OLLAMA_FLASH_ATTENTION=1"
Environment="OLLAMA_CONTEXT_LENGTH=32768"
```

## Upgrading ollama

**Never run `curl -fsSL https://ollama.com/install.sh | sh`**: it overwrites `/usr/local/bin/ollama` *and* `/usr/local/lib/ollama/` with the stock build, which drops the carve-out patch and does not match the system ROCm. Ollama can then fall back to CPU without any error.

Upgrade only by rebuilding from source, as above.

## Verification

After install or restart, confirm GPU detection:

```bash
journalctl -u ollama -b --no-pager | grep "inference compute"
```

Good: `library=ROCm compute=gfx1151 libdirs=ollama,rocm_v7_2 ... total="96.0 GiB" available="95.8 GiB"`.
`library=cpu`, or `available` near 27 GiB (patch missing), means the GPU path is broken. Then run a
model and check `ollama ps` shows `100% GPU`. Service status and API health prove nothing here.
If the ROCm backend is missing, start with `ldd /usr/local/lib/ollama/rocm_v7_2/libggml-hip.so`.

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
- The 96 GiB is a dedicated UMA carve-out set in BIOS (Advanced → GFX Configuration); the OS sees the remaining ~30 GiB as system RAM.
- The empty `docker-compose.yml` next to this README is intentional: ollama runs natively. The file is kept as a marker so the directory shows up in tooling that lists docker stacks.
