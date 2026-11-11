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

### Routine maintenance

`scripts/stack-update` is the standard routine: `apt-get update`, `apt-get --with-new-pkgs upgrade`,
then `docker compose pull && up -d` across every stack (`.yml` and `.yaml` alike), then an image
prune. It reports a pending reboot but never takes one.

Note `--with-new-pkgs`: it makes `apt-get` behave like `apt upgrade`. Plain `apt-get upgrade`
refuses to pull in new dependencies and silently holds those packages back instead.

Things this host must **not** do unattended:

- **Upgrade the GPU stack.** About 65 ROCm/HIP/amdgpu packages are installed. Nothing is
  `apt-mark hold`, so instead `stack-update` simulates the upgrade first and, if any of those
  packages is pending, skips the apt step for that run and reports it. Run that upgrade by hand,
  supervised. Two things limit the risk anyway: ROCm comes from a version-pinned
  `repo.radeon.com/rocm/apt/<version>` source (currently `7.2.4`), which never moves to a newer
  release on its own, and Ollama ships its own ROCm runtime under `/usr/local/lib/ollama/`.
  Each `rocm/apt/<x.y.z>` path is frozen at that release. Note that `rocm/apt/7.2` means 7.2.0, not
  "latest 7.2": point releases need the source edited to the new path by hand.
- **`apt full-upgrade` / `dist-upgrade`** - may remove or replace packages.
- **`apt autoremove`** - currently proposes removing `amdgpu-dkms-firmware`.

### Kernel track

jarvis boots the **OEM kernel** (`linux-oem-24.04`, 6.17.x), which is what carries Strix Halo
support; `amdgpu` is in-tree there, not DKMS. The generic track (`linux-generic`, 6.8.x) is
installed but never booted: it predates usable gfx1151 support, so it is not a real fallback. It
should be removed, because it pulls kernel updates that are never used and raises spurious
`/var/run/reboot-required` flags, which matters for any automation that acts on that flag.

## Agent access

Automation reaches this host as `homelab-ops` (uid 3101), not as the `jarvis` login user, and gets
a pinned command list rather than blanket sudo. Files live in [`scripts/`](scripts/); the reasoning
and the general pattern are in [guides/agent-access.md](../guides/agent-access.md).

| File | Installs to |
|---|---|
| [`scripts/stack-update`](scripts/stack-update) | `/usr/local/sbin/stack-update`, `root:root 0755` |
| [`scripts/sudoers.d-homelab-ops`](scripts/sudoers.d-homelab-ops) | `/etc/sudoers.d/homelab-ops`, `root:root 0440` |

To install or update, copy `scripts/` plus the agent's public key (as `homelab-ops.pub`) to a
staging directory on the host and run `sudo ./install-agent-access` there. It validates the
sudoers file before installing it, keeps an existing account and key, and prints the effective
grant at the end.

The grant is `stack-update`, start/stop/restart of `ollama.service` plus `daemon-reload`, and
`systemctl reboot`. Deliberately **not** granted: the docker group (the socket is root-equivalent),
and any command taking a free-form argument vector.

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
| `gpt-oss:120b` | 65 GB | Added 2026-11-08: large reasoning model |
| `gpt-oss:20b` | 13 GB | Added 2026-11-08: fast reasoning model |
| `qwen3.5:35b-a3b` | 22 GB | Added 2026-11-08: MoE, text and image input, structured JSON output |
| `qwen3.5:122b` | 81 GB | Added 2026-11-08: large MoE, kept for a model comparison |

Throughput on v0.40.15 + the carve-out patch, ROCm 7.2.4, 2026-11-11 (tokens/s, prompt processing /
generation; "4k" is a ~2.3k-token prompt, "32k" ~21k). All 100% GPU at default placement:

| Model | 4k | 32k |
|---|---|---|
| `gpt-oss:120b` | 931 / 34.4 | 651 / 29.5 |
| `qwen3.5:122b` | 518 / 26.5 | 418 / 23.9 |
| `gpt-oss:20b` | 1730 / 46.8 | 1362 / 40.8 |
| `qwen3.5:35b-a3b` | 1547 / 53.8 | 1282 / 47.7 |
| `qwen3-coder:30b` | 1588 / 59.9 | 838 / 39.8 |

On 0.32.13 without the patch, `gpt-oss:120b` managed only 116 / 35 and 151 / 30 even when forced fully onto
the GPU, so most of the prompt-processing gain is from the newer llama.cpp.

Two things fixed by 0.40.15 that are worth knowing if this is ever rolled back: on 0.32.13,
`/api/generate` with `format: "json"` returned empty output on thinking models (gpt-oss, qwen3.5;
`/api/chat` worked), and `qwen2.5vl:32b` fully on the GPU answered image prompts with stale
or invented text.

Removed: eleven models pulled 11–12 months earlier (`llama3.3:70b`, `deepseek-r1:70b`,
`gpt-oss:120b`, `gpt-oss:20b`, `qwen3:30b`, `codellama:34b`, `codellama:7b`, `codegemma:7b`,
`deepseek-coder-v2:16b`, `deepseek-r1:1.5b`) plus `mistral-small3.1:24b`, which was strictly
superseded by the `3.2` already present.

Before removing anything, check what references it. As of the prune the only traceable consumer of
Ollama was paperless-gpt; paperless-ai has no LLM configured, and Open WebUI's database held zero
chats. Anything removed can be re-pulled on demand — `ollama pull` is cheap, 220 GB of stale
weights is not.

### Building / upgrading Ollama from source

Ollama is built from source against the system ROCm so it uses the gfx1151 iGPU natively, with one
local patch (below). Last built **2026-11-11 at `v0.40.15`**, ROCm **7.2.4**.

Build in a separate git worktree, so the installed build's source tree stays untouched until the new
one is tested:

```bash
cd ~/ollama-src
git fetch --tags origin
git worktree add --detach ~/ollama-v<VERSION> v<VERSION>
cd ~/ollama-v<VERSION>
git apply <repo>/205-gmktek/patches/ollama-igpu-carveout.patch

# Configure. There is a backend matching each ROCm release; pick the one that
# matches /opt/rocm/.info/version. gfx1151 is Strix Halo.
export PATH=/opt/rocm/bin:$PATH
cmake -B build . -DOLLAMA_LLAMA_BACKENDS=rocm_v7_2 -DCMAKE_HIP_ARCHITECTURES=gfx1151 \
      -DCMAKE_PREFIX_PATH=/opt/rocm

cmake --build build --parallel
go build -ldflags "-X=github.com/ollama/ollama/version.Version=<VERSION>" -o ollama .
go test ./server/
```

Run the build inside `tmux`: it takes several minutes, and a dropped SSH session would otherwise
kill it.

Verify before configuring further: `grep OLLAMA_LLAMA_BACKENDS build/CMakeCache.txt` should show
`rocm_v7_2`, and `cmake --build build --target help | grep rocm` should list
`ollama-llama-server-rocm_v7_2`. A configure that silently omits the ROCm backend produces a
CPU-only build. (Do not test that with `grep -q` under `set -o pipefail`: grep exits early, the
pipe breaks, and the check fails on a good build.)

Without the `-ldflags` version stamp, `/api/version` reports `0.0.0`.

Go version is handled automatically — `go.mod` requires a newer Go than the system package, and
`GOTOOLCHAIN=auto` fetches it into `$GOPATH`. No system Go change is needed.

**The build bundles the ROCm runtime** (`libamdhip64`, `rocblas`, ...) into
`build/lib/ollama/rocm_v7_2/`, copied from `/opt/rocm` at build time. A system ROCm upgrade
therefore reaches Ollama only after a rebuild. Upgrade ROCm first, then build.

#### Local patch: integrated GPU memory cap

[`patches/ollama-igpu-carveout.patch`](patches/ollama-igpu-carveout.patch) changes
`server/sched.go`. Upstream caps an integrated GPU's free memory at free *system* RAM
(`availableMemoryForGPU`, `availableMemoryForLoad`). That is right for an APU that borrows system
RAM, but here 96 GB is a BIOS UMA carve-out the OS never sees, so Ollama saw about 27 GB of a
96 GB GPU. Large models were split onto the CPU, and a default `gpt-oss:120b` load got the runner
OOM-killed. The patch skips the cap only when the iGPU's total memory exceeds total system memory,
which only a firmware carve-out produces, so ordinary APUs behave as upstream.

- Unpatched startup line: `type=iGPU total="96.0 GiB" available="27.2 GiB"`.
- Patched: `available="95.8 GiB"`, and every model in the library loads `100% GPU`.
- Before the patch the workaround was `PARAMETER num_gpu 999` baked into local tags. An
  `ollama pull` of the tag removes it; with the patch it is no longer needed.

If `git apply` fails on a new version, the functions have moved: re-apply by hand and refresh the
patch file. Drop it once upstream handles carve-outs.

**Test before installing.** Stop the service (the GPU memory is needed), then run the new binary on
a spare port. Point it at a **shadow model directory**, not the live store: since 0.40 the server
creates `manifests-v2/` in the store at startup, which fails without write access, and a shadow
directory keeps a test build from writing to the real store at all:

```bash
sudo systemctl stop ollama
mkdir -p ~/test-models
ln -sfn /usr/share/ollama/.ollama/models/blobs ~/test-models/blobs
cp -r /usr/share/ollama/.ollama/models/manifests ~/test-models/
cd ~/ollama-v<VERSION>
OLLAMA_HOST=127.0.0.1:11435 OLLAMA_NOPRUNE=1 OLLAMA_MODELS=$HOME/test-models \
OLLAMA_LIBRARY_PATH=$PWD/build/lib/ollama \
OLLAMA_FLASH_ATTENTION=1 OLLAMA_CONTEXT_LENGTH=32768 ./ollama serve
# in another shell:
OLLAMA_HOST=127.0.0.1:11435 ./ollama run qwen2.5-coder:7b "hi"
OLLAMA_HOST=127.0.0.1:11435 ./ollama ps    # PROCESSOR must read 100% GPU
```

Test a large model (`gpt-oss:120b`), not only a small one: a model under ~27 GB fit even with the
memory cap. Also run the `qwen2.5vl:32b` image test (paperless-gpt depends on it): several text
prompts, each followed by an image prompt, and check that the image answers describe the image.
Remove `~/test-models` and start the service again afterwards.

**Install — stop the service first**, or copying the binary fails with `Text file busy` because the
running process holds it open. Keep the old pair as the rollback:

```bash
sudo systemctl stop ollama
sudo cp -a /usr/local/bin/ollama /usr/local/bin/ollama.bak-<OLD>
sudo mv /usr/local/lib/ollama /usr/local/lib/ollama.bak-<OLD>
sudo cp -a ~/ollama-v<VERSION>/build/lib/ollama /usr/local/lib/ollama
sudo cp ~/ollama-v<VERSION>/ollama /usr/local/bin/ollama
sudo chown -R root:root /usr/local/lib/ollama /usr/local/bin/ollama
sudo systemctl start ollama
journalctl -u ollama -n 50 --no-pager | grep "inference compute"
```

Rollback restores both halves together: stop, put `lib/ollama.bak-<OLD>` back in place of
`lib/ollama`, copy `ollama.bak-<OLD>` over the binary, start.

The library layout changed in 0.32: 0.30 installed `lib/ollama/rocm/`, 0.32 and later install
`lib/ollama/` plus a `rocm_v7_2/` subdirectory. Replace the whole directory rather than copying
over it.

> **Mismatched binary and libraries fall back to CPU silently.** This happened during the 0.32.13
> upgrade: the library copy succeeded, the binary copy failed with `Text file busy`, and the
> service restarted clean — `systemctl is-active` said `active` and the API returned HTTP 200
> while every request ran on CPU. The only signal was the startup log:
> ```
> msg="inference compute" id=cpu library=cpu      # BAD - CPU only
> msg="inference compute" id=0 library=ROCm compute=gfx1151 libdirs=ollama,rocm_v7_2   # GOOD
> ```
> After any upgrade, check that line (it should also show `available` close to 96 GiB) and run an
> inference confirming `100% GPU`. Service status and API health prove nothing here.

**Model store format.** 0.40 adds a `manifests-v2/` directory beside `manifests/`. The migration
into it is not wired up yet in 0.40.15: models are still read from, and pulls still write to, the
legacy `manifests/`, so rolling back to 0.32 keeps every model visible. Recheck this on the next
upgrade before relying on rollback.

### Ollama is **not** a Docker stack

Ollama runs as a **native systemd service** on port `11434`, built from source against the
system ROCm install so it uses the gfx1151 iGPU directly. `docker/ollama/` holds an intentionally
empty `docker-compose.yml` as a directory marker only — do not deploy it.

Never install or upgrade Ollama with `curl … install.sh | sh`: the stock build ships its own ROCm
libraries that do not match the system ROCm, and it silently falls back to CPU. Upgrade only by
rebuilding from source.
