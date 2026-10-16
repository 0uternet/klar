# Licences and third-party notices

## This project

| Material | Licence |
|---|---|
| Source code | Apache License 2.0, see [`LICENSE`](../../LICENSE) |
| Documentation, technical report, design assets | Creative Commons Attribution 4.0 (CC-BY-4.0) |
| Datasets we publish (generated test cases, model responses, metadata) | Community Data License Agreement – Permissive 2.0 (CDLA-Permissive-2.0), see [`data/testset/LICENSE-CDLA-Permissive-2.0.txt`](../data/testset/LICENSE-CDLA-Permissive-2.0.txt) |
| Demo website `data/demo-site/` (fictional municipality, text and images) | CC-BY-4.0; its generator in `scripts/` is Apache-2.0 |

The name "Klar." and its logo are not licensed under Apache-2.0 (Apache-2.0 §6 grants no trademark rights).

## Models (not redistributed in this repository)

| Component | Licence | Notes |
|---|---|---|
| Apertus v1.5 8B / 70B (`swiss-ai/Apertus-v1.5-8B`, `swiss-ai/Apertus-v1.5-70B`) | Apache-2.0 | Downloaded or called at runtime. The weights are never committed. |
| Apertus v1.5 8B text-only GGUF (`Colby/apertus-v1.5-8b-text-Q4_K_M-GGUF`, converted from `andreasmartin/apertus-v1.5-8b-text`) | Apache-2.0 (inherited) | Optional CPU-only fallback. |

## Shipped unmodified inside the source tree

| Component | Version | Licence | Location |
|---|---|---|---|
| axe-core (Deque Systems, Inc.) | 4.13.0 | MPL-2.0 | `src/klar/capture/vendor/` (licence, third-party notices and provenance in `SOURCE.txt`) |
| W3C ACT Rules test cases | see `data/testset/act/` | W3C Software and Document Notice and License | `data/testset/act/` (notice in `LICENSE-W3C.md`) |
| Natural Earth admin-0 boundaries, 1:50m (outline of Switzerland) | 5.1.2 | Public domain | `docs/report/assets/fig_people.svg` |
| Material Symbols icons (Google): blind, eyeglasses, keyboard, psychology | — | Apache-2.0 | `docs/report/assets/fig_people.svg` |

## Python runtime dependencies

Pinned in [`pyproject.toml`](../pyproject.toml); the transitive set below is what the app container installs.

| Package | Version | Licence |
|---|---|---|
| annotated-doc | 0.0.5 | MIT |
| annotated-types | 0.8.0 | MIT |
| anyio | 4.15.1 | MIT |
| certifi | 2026.7.22 | MPL-2.0 |
| click | 8.5.0 | BSD-3-Clause |
| fastapi | 0.143.0 | MIT |
| greenlet | 3.5.6 | MIT AND PSF-2.0 |
| h11 | 0.16.0 | MIT |
| httpcore / httpcore2 | 1.0.9 / 2.13.1 | BSD-3-Clause |
| httpx / httpx2 | 0.28.1 / 2.13.1 | BSD-3-Clause |
| idna | 3.20 | BSD-3-Clause |
| jiter | 0.17.0 | MIT |
| lingua-language-detector | 2.2.0 | Apache-2.0 |
| openai (client library only; no OpenAI service is called by default) | 3.29.0 | Apache-2.0 |
| opentelemetry-api | 1.45.1 | Apache-2.0 |
| playwright | 1.63.0 | Apache-2.0 |
| pydantic / pydantic_core | 2.14.1 / 2.50.1 | MIT |
| pyee | 13.0.1 | MIT |
| python-multipart | 0.0.32 | Apache-2.0 |
| sniffio | 1.3.1 | MIT OR Apache-2.0 |
| starlette | 1.8.0 | BSD-3-Clause |
| truststore | 0.10.5 | MIT |
| typing_extensions | 4.16.0 | PSF-2.0 |
| typing-inspection | 0.4.4 | MIT |
| uvicorn | 0.54.0 | BSD-3-Clause |

## Web UI (bundled into the static build)

Pinned in [`src/web/package-lock.json`](../src/web/package-lock.json).

| Package | Version | Licence |
|---|---|---|
| vue, @vue/* runtime | 3.5.44 | MIT |
| vue-router | 4.6.4 | MIT |
| @vue/devtools-api | 6.6.4 | MIT |
| lucide-vue-next (icons) | 1.0.0 | ISC |
| Inter (font, via @fontsource-variable/inter) | 5.3.0 | SIL Open Font License 1.1, text in `src/web/public/licenses/Inter-OFL.txt` |
| JetBrains Mono (font, via @fontsource/jetbrains-mono) | 5.3.0 | SIL Open Font License 1.1, text in `src/web/public/licenses/JetBrainsMono-OFL.txt` |

Build-time and test-time only, not shipped: Vite, @vitejs/plugin-vue, TypeScript, vue-tsc, playwright-core
and their dependencies (MIT, ISC, BSD-2-Clause, BSD-3-Clause, Apache-2.0), and axe-core 4.11.0 (MPL-2.0),
used only to test the accessibility of the web UI itself.

## Container images (pulled at build or run time, not redistributed)

| Image | Licence | Use |
|---|---|---|
| `mcr.microsoft.com/playwright/python:v1.63.0-noble` (pinned by digest) | Apache-2.0; bundles Chromium (BSD-3-Clause and others) and Ubuntu packages under their own licences | App runtime base |
| `node:22.23.3-alpine3.23` (pinned by digest) | MIT (Node.js) | Web UI build stage only |
| `ghcr.io/swiss-ai/vllm_apertus_1.5_release` (pinned by digest) | Apache-2.0 (vLLM) | Optional on-premise GPU model server |
| `ghcr.io/ggml-org/llama.cpp:server-b11243` (pinned by digest) | MIT | Optional CPU model server |
