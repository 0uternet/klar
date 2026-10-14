# Klar. deployment

Klar. is one web application (FastAPI API + Vue UI + headless Chromium) plus, optionally, an
inference server for Apertus. It runs in the three target architectures: **(a) on-premise**, **(b) air-gapped**, **(c) sovereign Swiss cloud**.

## 0. Two ways to run it, with the same three variables

| Who | How | What it needs |
|---|---|---|
| **Judges, evaluators, anyone with Docker** | `make run` from `track_2b/` | Docker (Engine 24+ or Desktop) with Compose v2.24+, and GNU make. Nothing else. CI checks this path end to end (section 9). |
| **Operators who do not run containers** | a native install (section 3d) | Python 3.12+, Node.js 22 to build the UI, and llama.cpp or vLLM for local inference |

Both read the **same configuration**: `LLM_BASE_URL`, `LLM_NAME`, `LLM_API_KEY` (imposed by the
template), plus `KLAR_REPLAY=1` to force replay mode. They can be exported in the shell or written
in `track_2b/.env` (copy `.env.example`). Precedence: `make` command line > shell environment >
`.env` > the target's default. A variable exported in the shell wins even when it is **empty**:
`export LLM_BASE_URL=` overrides an `LLM_BASE_URL` in `.env` and means replay mode (the banner
says so). With **no non-empty `LLM_BASE_URL` anywhere** (or `KLAR_REPLAY=1`), Klar. runs in
**replay mode**: it answers from the recorded Apertus responses in `data/replay/`, with no key,
no model and no download. Every start prints where inference runs and which setting chose it:

```
==> Klar. | make run
    Mode         : replay  - recorded Apertus answers from data/replay; no model call, no key, no download
    LLM endpoint : none (replay)
    Configured by: nothing set: replay mode
    Your data    : scans, screenshots, reports and SQLite stay in ./var on this machine
```

The mode (`replay`, `local`, `swiss_cloud`, `external`) is computed from the host of `LLM_BASE_URL`
by `src/klar/config.py` and reported by `GET /api/health`. URLs are printed without credentials or
query strings.

## 1. Command reference (from `track_2b/`)

| Command | Effect |
|---|---|
| `make run` | Build the image, start the app on <http://localhost:8080>, scan the bundled demo site (`klar demo`) and print the report path (`./var/reports/demo-latest.html`). |
| `make run-gpu` | Same, plus the official Apertus 1.5 vLLM image on the local NVIDIA GPU (`--profile gpu`). |
| `make run-cpu` | Same, plus llama.cpp with the text-only GGUF on CPU (`--profile cpu`). Downloads and sha256-verifies the GGUF once. |
| `make eval` | `klar eval` on `data/testset`, results in `eval/results/`. The test split is checked against the git tag `labels-v1`, so it needs a clone with tags: run `git fetch --tags` first in a shallow clone. |
| `make test` | pytest and the web type-check, inside the Docker `test` stage. |
| `make airgap-check [AIRGAP_LLM=replay\|cpu\|gpu]` | Proof of offline operation (section 3b). |
| `make bundle [BUNDLE=cpu\|gpu\|all]` | Offline bundle for an air-gapped site (section 3b). |
| `make download-model` | Fetch and verify the GGUF used by `run-cpu`. |
| `make stop`, `make logs [SERVICE=app]`, `make clean`, `make help` | Stop, follow logs, remove containers + app image + `./var` (`clean` keeps `./models` and `./eval/results`). |

Knobs: `KLAR_PORT=8090` (host port; the container port stays 8080), `KLAR_BIND=0.0.0.0` (expose on
the LAN; the default `127.0.0.1` keeps the scanner private to this machine). With a specific address,
e.g. `KLAR_BIND=192.168.1.20`, the Makefile waits for the app on that address and adds it to
`KLAR_ALLOWED_HOSTS`, the Host names the app accepts. Also: `BUILD=0` (reuse the
existing image), `DEMO=0` (start without the demo scan), `KLAR_MEM_LIMIT`, `KLAR_PIDS_LIMIT`,
`VLLM_MAX_MODEL_LEN`, `VLLM_GPU_MEMORY_UTILIZATION`, `HF_CACHE_DIR`, `LLAMA_THREADS`.

## 2. What runs where

```
 browser ──HTTP──> app container "klar:local"  (127.0.0.1:8080)                  ./var  (bind mount)
                   FastAPI + built Vue UI + headless Chromium (Playwright)        SQLite, scans,
                   data/demo-site (served at /demo/), data/replay                 screenshots, reports
                        │  OpenAI-compatible HTTP, only when not in replay mode
                        ├──> llm-gpu  vLLM, swiss-ai/Apertus-v1.5-8B, BF16   (profile gpu, :8000 internal)
                        ├──> llm-cpu  llama.cpp, 8B text-only Q4_K_M GGUF    (profile cpu, :8080 internal)
                        └──> Swiss cloud endpoint (Phoeniqs / CSCS), HTTPS   (only if configured)
 Chromium ──HTTP(S)──> the site being audited
```

| Component | Image / binary | Runs on | Network it needs at runtime |
|---|---|---|---|
| Klar. app | `klar:local`, built from `Dockerfile` (base `mcr.microsoft.com/playwright/python:v1.63.0-noble`) | your server or workstation | the audited site; the LLM endpoint unless in replay mode |
| Inference, GPU | `ghcr.io/swiss-ai/vllm_apertus_1.5_release:latest@sha256:6349…ea9` (official Apertus 1.5 image, CUDA 13.0) | same machine, NVIDIA GPU | none once the weights are cached (`HF_HUB_OFFLINE=1`) |
| Inference, CPU | `ghcr.io/ggml-org/llama.cpp:server-b11243@sha256:f911…283` | same machine | none |
| Inference, Swiss cloud | Phoeniqs (`maas.phoeniqs.com`) or CSCS (`api.inference.cscs.ch`) | the provider, in Switzerland per its documentation | outbound HTTPS from the app to that host only |

The app makes no other third-party requests: the UI and its fonts are compiled into the image,
and vLLM usage statistics and Hugging Face telemetry are switched off in `docker-compose.yml`.

## 3. Target architectures

### 3a. On-premise: GPU workstation (reference: one RTX 5090, 32 GB)

1. Linux (or Windows with Docker Desktop and WSL2 GPU support), NVIDIA driver **≥ 580** (the vLLM
   image is built on CUDA 13.0) and the
   [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)
   (`sudo nvidia-ctk runtime configure --runtime=docker && sudo systemctl restart docker`).
2. Accept the licence of [`swiss-ai/Apertus-v1.5-8B`](https://huggingface.co/swiss-ai/Apertus-v1.5-8B)
   (gated repository) and put `HF_TOKEN=hf_...` in `.env`. The token is needed **once**, for the
   download, and only the model server receives it. The weights then live in `./models/huggingface`;
   add `HF_HUB_OFFLINE=1` to `.env` and the token can be removed.
3. `make run-gpu`. The first start pulls the image (about 9 GB) and the weights (about 18 GB);
   the target waits for `GET /v1/models` before it starts the app.

vLLM command (the model card's arguments, adapted to one 32 GB GPU, with no function-calling flags
because Klar. never uses them):
`vllm serve swiss-ai/Apertus-v1.5-8B --served-model-name swiss-ai/Apertus-v1.5-8B --max-model-len 32768
--gpu-memory-utilization 0.85 --chat-template-content-format string --seed 0`.
Thinking mode stays off: Klar. asks closed questions with a JSON schema.

Memory budget (RTX 5090, 32 GB): the 8B model has 8.61 B BF16 + 0.29 B F32 parameters, i.e.
**≈ 18.4 GB of weights**. `0.85 × 32 GB ≈ 27 GB` leaves about 8.5 GB for activations, CUDA graphs
and the KV cache. Assuming the Apertus-8B backbone (32 layers, 8 KV heads × 128 dims), the KV cache
costs about 128 KiB per token, so one full 32 768-token context is about 4 GiB. vLLM prints the real
KV capacity at start-up ("GPU KV cache size"). On a 24 GB card use `VLLM_MAX_MODEL_LEN=8192
VLLM_GPU_MEMORY_UTILIZATION=0.92`. If the GPU also drives the desktop, lower the utilisation.

**CPU only** (`make run-cpu`): llama.cpp serves the text-only Q4_K_M GGUF with `--jinja -c 8192
--parallel 1 --threads $LLAMA_THREADS` (about one thread per physical core). Criteria that need
vision are reported as "can't tell". See section 5 for measured speed.

### 3b. Air-gapped (no external network at runtime)

Everything Klar. needs at runtime is local: the image contains the UI, Chromium and the demo site,
and the weights live in `./models`. Network is needed only **before**, to build and download.

1. On a connected staging machine (same CPU architecture as the target):
   `make bundle BUNDLE=cpu` (or `gpu`, `all`). It builds `klar:local`, pulls the inference image,
   downloads and verifies the weights into `./models`, and writes `dist/klar-images-<what>.tar` and
   `dist/klar-offline.env` (`HF_HUB_OFFLINE=1`, plus image names re-tagged as `klar-offline/...`,
   because a `docker load`ed image is not always resolvable by its registry digest).
2. Transfer the repository checkout, `dist/` and `models/` (USB disk, data diode, ...).
3. On the air-gapped machine: `sh deploy/airgap_bundle.sh load`, `cat dist/klar-offline.env >> .env`,
   then `make run-cpu BUILD=0` or `make run-gpu BUILD=0` (`BUILD=0` never rebuilds, which would need
   the internet).
4. Prove it: `make airgap-check BUILD=0 AIRGAP_LLM=cpu`.

**`make airgap-check`** (`deploy/airgap_check.sh` with the overlay `deploy/compose.airgap.yml`)
starts the stack as project `klar-airgap` on a Docker network declared `internal: true` (no gateway,
no NAT). It passes only if (1) a probe *inside* the app container (and inside the model container)
fails to connect to `1.1.1.1:443`, `9.9.9.9:53`, `huggingface.co:443` and `github.com:443`,
(2) `klar demo` still completes the scan of the bundled site, and (3) `/api/health` answers from
inside the network. `AIRGAP_LLM=replay` (default) works on any machine and runs in CI; `cpu` and
`gpu` add real offline inference. An internal network cannot publish ports, so the check drives
the app with `docker compose exec`; for a real offline site, put a reverse proxy on both networks.

### 3c. Sovereign Swiss cloud (Phoeniqs / CSCS)

Set the three variables (shell or `.env`, never committed) and run `make run`:

```dotenv
# Phoeniqs (kvant)
LLM_NAME=inference-apertus-v15-70b
LLM_BASE_URL=https://maas.phoeniqs.com/v1
LLM_API_KEY=...

# or CSCS
# LLM_NAME=swiss-ai/Apertus-v1.5-70B
# LLM_BASE_URL=https://api.inference.cscs.ch/v1
# LLM_API_KEY=...
```

Only inference leaves the machine. Klar. still renders and stores every page locally. For each
question it sends one closed question with the minimal context of one element (its HTML snippet,
the programmatic context that WCAG defines and, for vision criteria, a cropped screenshot), never a
whole page. Where and how the provider processes the data is stated in the provider's own
documentation. `/api/health` reports `mode: swiss_cloud`. For strict egress control, allow outbound
HTTPS from the app only to that host and to the sites you audit. The 70B model is practical only
here (section 5).

### 3d. Without containers (native install)

For operators who do not run Docker. The same variables apply; nothing else changes.

1. **App.** In `track_2b/`: `python3 -m venv .venv`, activate it, `pip install -e .`, then
   `python -m playwright install chromium` (on Linux also `python -m playwright install-deps chromium`
   as root). Build the UI once: `cd src/web && npm ci && npm run build` (it writes
   `src/klar/api/static`). Start with `klar serve --host 127.0.0.1 --port 8080`, and run the demo
   with `klar demo` in a second shell. Runtime data goes to `./var` (`KLAR_DATA_DIR`).
2. **CPU or GPU with llama.cpp** (text only). Take an official build from
   <https://github.com/ggml-org/llama.cpp/releases> (the CPU build, or the CUDA 13 build plus its
   `cudart` archive for an NVIDIA GPU; on macOS `brew install llama.cpp` uses Metal). The container
   uses b11243; newer builds work too (b11609 was used for the measurements in section 5). Fetch and
   verify the GGUF with `sh deploy/download_model.sh` (or download
   `apertus-v1.5-8b-text-q4_k_m.gguf`, sha256 `a037df8d…f299`, by hand), then
   `llama-server -m models/apertus-v1.5-8b-text-q4_k_m.gguf --alias swiss-ai/Apertus-v1.5-8B --jinja
   -c 8192 --parallel 1 --host 127.0.0.1 --port 8081` (add `-ngl 99` on a GPU), and set
   `LLM_BASE_URL=http://127.0.0.1:8081/v1`, `LLM_NAME=swiss-ai/Apertus-v1.5-8B`, `LLM_API_KEY=local`,
   `KLAR_VISION=0`.
3. **GPU with vLLM (text + images), e.g. an RTX 5090 under Windows via WSL2.** This reproduces the
   official image's build; the commits come from its build history.
   - Windows: NVIDIA driver ≥ 580 (it provides CUDA inside WSL2; do not install a Linux driver in
     WSL). `wsl --install -d Ubuntu-24.04`, give WSL enough memory in `.wslconfig` (`[wsl2]`
     `memory=32GB`), `wsl --shutdown`. Inside WSL, `nvidia-smi` must list the GPU.
   - In WSL:
     ```bash
     sudo apt update && sudo apt install -y python3.12-venv python3.12-dev build-essential git curl
     mkdir -p ~/apertus-vllm && cd ~/apertus-vllm
     python3.12 -m venv .venv && . .venv/bin/activate && pip install "uv==0.11.30"
     uv pip install --extra-index-url https://download.pytorch.org/whl/cu130 \
       torch==2.11.0 torchvision==0.26.0 torchaudio==2.11.0 \
       "setuptools>=77.0.3,<81.0.0" "setuptools-scm>=8" wheel ninja "packaging>=24.2" "cmake>=3.26.1" setuptools_rust
     git clone --branch feature/apertus_1p5_pipeline https://github.com/swiss-ai/transformers.git
     git -C transformers checkout 3797303dda74844e3d1f8977ff5518bb91f818b4
     (cd transformers && uv pip install --no-deps .)
     git clone --branch apertus-1-5 https://github.com/swiss-ai/vllm.git
     git -C vllm checkout a601a9d998ddeb488f0c17e8512874b116aa7658
     cd vllm
     export VLLM_USE_PRECOMPILED=1 VLLM_MAIN_CUDA_VERSION=13.0 \
       VLLM_PRECOMPILED_WHEEL_COMMIT=ae6170f874a7c66512bd24aa714b3a02f8a61838 \
       VLLM_PRECOMPILED_WHEEL_LOCATION="https://wheels.vllm.ai/ae6170f874a7c66512bd24aa714b3a02f8a61838/vllm-0.23.1rc1.dev977%2Bgae6170f87-cp38-abi3-manylinux_2_28_x86_64.whl"
     uv pip install --reinstall-package vllm --no-build-isolation ".[audio]" --torch-backend=auto
     ```
   - Serve (keep the Hugging Face cache on the WSL file system, not under `/mnt/c`; set `HF_TOKEN`
     for the first download only, then `HF_HUB_OFFLINE=1`):
     ```bash
     HF_HUB_DISABLE_TELEMETRY=1 VLLM_NO_USAGE_STATS=1 DO_NOT_TRACK=1 \
     vllm serve swiss-ai/Apertus-v1.5-8B --served-model-name swiss-ai/Apertus-v1.5-8B \
       --host 0.0.0.0 --port 8000 --max-model-len 32768 --gpu-memory-utilization 0.85 \
       --chat-template-content-format string --seed 0
     ```
     With WSL's default NAT networking, port 8000 is forwarded to Windows `localhost` only. Point
     Klar. at it with `LLM_BASE_URL=http://127.0.0.1:8000/v1`.
4. **Offline native install.** On a connected machine with the same OS and Python version:
   `pip download -d wheelhouse . "setuptools>=77" wheel`, build the UI, and copy the Playwright
   browser cache folder (`ms-playwright`), the llama.cpp archive and the GGUF. Offline:
   `pip install --no-index --find-links wheelhouse -e .`.

## 4. Threat model and security controls

Klar. renders untrusted web pages in a headless browser and sends small excerpts to a model.

| Risk | Control | Where |
|---|---|---|
| Secrets leaking into the browser process | The app container receives only an allow-list of variables (`LLM_*`, `KLAR_*`); it has no `env_file`. `HF_TOKEN` goes only to the model server and the GGUF download. `.env` never enters an image (`.dockerignore`). URLs are printed without userinfo or query. | `docker-compose.yml`, `deploy/endpoint.sh` |
| Unauthenticated API reachable by others | The API has no login: it is published on `127.0.0.1` only. Expose it (`KLAR_BIND=0.0.0.0`) only behind an authenticating reverse proxy, and list the public host name in `KLAR_ALLOWED_HOSTS` (Host-header check against DNS rebinding). | compose, app |
| Server-side request forgery through the scanner | The app's URL policy: http(s) only; link-local and cloud-metadata addresses always blocked; loopback blocked except the bundled demo; private ranges (RFC 1918, fc00::/7, 100.64/10) blocked unless `KLAR_ALLOW_PRIVATE_NETWORKS=1` (default `0`) for intranet audits. The configured model endpoint, including the Compose service names `llm-gpu` and `llm-cpu`, is the model client's own destination and is not opened up by that switch. | app (`src/klar`) |
| Side effects on audited sites | The form probe submits forms only on the demo site bundled with Klar.; on any other site, no form is submitted. | app |
| Prompt injection from page text | Page content goes to the model as JSON-encoded data that the system prompt declares untrusted; verdicts come from enum fields only; no request carries tools, and the vLLM server has no function-calling flags. | app, compose |
| Resource exhaustion by a hostile page | `mem_limit` 4 GB, `pids_limit` 1024 and a 1 GB `/dev/shm` on the app container (`KLAR_MEM_LIMIT`, `KLAR_PIDS_LIMIT`); scan timeout and request-size limits in the app. | compose, app |
| Network egress in an air-gapped site | `internal: true` Docker network, verified by `make airgap-check` (section 3b). | `deploy/` |

Residual risks, stated plainly:
- Chromium runs **without its own sandbox** inside the container (Playwright's default in
  containers). The container is the boundary: non-root user, no added capabilities, memory and
  process limits. A read-only root file system (`read_only: true` plus tmpfs for `/tmp` and the
  home directory) is a further hardening step that is not enabled by default.
- A page can serve misleading DOM to the extractor, as with any automated checker (axe-core too).
  Klar. pre-checks; a person validates every finding.
- The mode is classified from the endpoint **host name**. A LAN host or proxy can forward requests
  elsewhere; the operator is responsible for what sits behind `LLM_BASE_URL`.

## 5. Hardware requirements and measured speed

| Set-up | Model | Minimum | Notes |
|---|---|---|---|
| Replay (`make run`) | none (recorded) | 2 CPU cores, 4 GB RAM, about 6 GB disk | the default |
| CPU (`make run-cpu`) | 8B text-only Q4_K_M (5.06 GB) | 4+ cores with AVX2, 16 GB RAM, about 12 GB disk | text criteria only, slow (below) |
| GPU (`make run-gpu`) | 8B multimodal BF16 (≈ 18.4 GB) | NVIDIA ≥ 24 GB VRAM, **32 GB recommended (RTX 5090)**, driver ≥ 580, 32 GB RAM, about 50 GB disk | text + images |
| 70B | Apertus-v1.5-70B | ≥ about 80 GB VRAM even in FP8 (≈ 70 GB of weights + KV cache); about 140 GB in BF16 (the model card uses 4 GPUs) | use the Swiss cloud (3c) |

**Measured, CPU** (14 Oct 2026): Intel Core i7-8550U laptop (4 cores / 8 threads, 16 GB RAM),
llama.cpp b11609 Windows CPU build, `-t 4`, Q4_K_M GGUF, one request of Klar.'s size
(672 prompt tokens, about 50 output tokens), two runs: prompt processing 11.1–12.8 tokens/s,
generation 2.9–3.5 tokens/s, **67–77 s per model question**. CPU mode is therefore for small,
offline checks; deterministic rules and heuristics decide most candidates without the model.
GPU timings are reported in the technical report.

## 6. Ports

| Port | Who | Exposure |
|---|---|---|
| 8080 | Klar. (Docker: host `${KLAR_BIND:-127.0.0.1}:${KLAR_PORT:-8080}` → container 8080) | localhost by default |
| 8000 | `llm-gpu` (vLLM) | internal Docker network only |
| 8080 | `llm-cpu` (llama.cpp), inside its own container | internal Docker network only |
| 8080 / 8081 / 8000 | native install: Klar. / llama-server / vLLM | `127.0.0.1` |

## 7. Where the data lives

| Path (host) | Container | Content |
|---|---|---|
| `./var` | `/app/var` (`KLAR_DATA_DIR`) | SQLite `klar.db`, `scans/`, `reports/` (`demo-latest.html`, `.json`) |
| `./eval/results` | `/app/eval/results` | `make eval` output |
| `./models` | `/models` (cpu); `./models/huggingface` → `/root/.cache/huggingface` (gpu) | GGUF (+ `.verified`), Hugging Face cache |
| `data/replay`, `data/demo-site` | `/app/data/...` (in the image) | recorded answers; the demo site served at `/demo/`. Live answers appended inside a container are lost with it; mount `./data/replay` to keep them. |
| `dist/` | - | air-gap bundle |

The app container runs as your user (`KLAR_UID`/`KLAR_GID`, set by the Makefile), so files in
`./var` belong to you. With rootless Docker or Podman use `KLAR_UID=0 KLAR_GID=0 make run`. Bind
mounts carry the SELinux `:z` label (a no-op without SELinux).

## 8. Build-time vs runtime dependencies

| Dependency | When | Used for | Air-gapped alternative |
|---|---|---|---|
| Docker Hub `node:22.23.3-alpine3.23` | build | compiling the Vue UI | ships inside `klar:local` |
| MCR `playwright/python:v1.63.0-noble` | build | runtime base (Python 3.12, Chromium) | ships inside `klar:local` |
| npm registry (`package-lock.json`), PyPI (pinned `==`) | build | UI and Python dependencies | ships inside `klar:local` |
| GHCR `swiss-ai/vllm_apertus_1.5_release` / `ggml-org/llama.cpp` | install (gpu / cpu) | inference server | `make bundle` + `docker load` |
| Hugging Face (`HF_TOKEN` for the gated 8B) | install (gpu: about 18 GB; cpu: 5.06 GB GGUF) | weights | copy `./models` |
| **Runtime, replay or local mode** | run | the audited site only | - |
| **Runtime, Swiss cloud mode** | run | the audited site and the Phoeniqs or CSCS HTTPS endpoint | - |

## 9. Reproducibility and CI

- Base and inference images are pinned by tag **and** multi-arch digest (`linux/amd64`, `linux/arm64`).
- Python and npm dependencies are pinned exactly (`pyproject.toml`, `package-lock.json`, `npm ci`).
- The Playwright pip version equals the base image tag (`PLAYWRIGHT_VERSION` in the `Dockerfile`);
  the build checks it.
- The GGUF is verified by size and sha256 (`deploy/download_model.sh`).
- vLLM runs with `--seed 0`; Klar. requests use temperature 0 and a fixed seed.
- CI (`.github/workflows/ci.yml`, no secrets) runs on every push to `main` and every pull request,
  from a clean checkout:
  - `unit`: pytest, web type-check and build.
  - `e2e-replay`: `make run` with a cold build; `/api/health` mode; `klar replay-check`; a demo
    report with no unrecorded answer and no model error. A `.env` holding a dummy `HF_TOKEN` is
    written first: the token must be absent from the app container, while the app does receive the
    other `.env` setting and the model server does receive the token (positive controls).
    Shell-exported `LLM_*` must give mode `local`. `make eval` runs non-blocking until the label
    tag `labels-v1` exists; the Makefile passes the tag's manifest sha256 and the commit to the
    container, which has no git.
  - `airgap`: `make airgap-check`.
  - `a11y`: axe-core on Klar.'s own pages and on the demo report, light and dark, English and German.
  - `docker-test`: `make test`.
  - `hygiene`: `deploy/hygiene.sh` (local paths, co-author lines, placeholders, likely secrets,
    oversized files, forbidden artefacts).
  - `leakage`: `scripts/check_leakage.py`.
  - `make-381`: the Makefile under macOS's GNU make 3.81 (dry run).
  - `e2e-arm64` (public repositories only): `make run` on linux/arm64.

## 10. Troubleshooting

| Symptom | Fix |
|---|---|
| `port is already allocated` | `KLAR_PORT=8090 make run` |
| `Docker Compose ... is too old` | update Docker (Compose v2.24+) |
| `permission denied` in `./var` | `sudo chown -R $(id -u):$(id -g) var`, or `KLAR_UID=0 KLAR_GID=0 make run` with rootless Docker |
| `make run` ignores my endpoint | check the banner line `Configured by`; `KLAR_REPLAY=1` in the shell or `.env` forces replay |
| `llm-gpu` exits, `401` / `gated repo` | accept the licence on Hugging Face and set `HF_TOKEN` in `.env` |
| `llm-gpu`: `CUDA out of memory` | lower `VLLM_MAX_MODEL_LEN` or `VLLM_GPU_MEMORY_UTILIZATION`; close other GPU programs |
| `llm-gpu`: `could not select device driver` | install the NVIDIA Container Toolkit and restart Docker |
| An LLM server on the host is unreachable from Docker | use `LLM_BASE_URL=http://host.docker.internal:<port>/v1` (works on Linux too) |
| Native install, Linux: Chromium does not start | `python -m playwright install-deps chromium` as root |
