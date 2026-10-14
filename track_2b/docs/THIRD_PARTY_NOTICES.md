# Licences and third-party notices

## This project

| Material | Licence |
|---|---|
| Source code | Apache License 2.0, see [`LICENSE`](../../LICENSE) |
| Documentation, technical report, design assets | Creative Commons Attribution 4.0 (CC-BY-4.0) |
| Datasets we publish (generated test cases, model responses, metadata) | Community Data License Agreement – Permissive 2.0 (CDLA-Permissive-2.0) |


## Models (not redistributed in this repository)

| Component | Licence | Notes |
|---|---|---|
| Apertus v1.5 8B / 70B (`swiss-ai/Apertus-v1.5-8B`, `swiss-ai/Apertus-v1.5-70B`) | Apache-2.0 | Downloaded or called at runtime. The weights are never committed. |
| Apertus v1.5 8B text-only GGUF (`Colby/apertus-v1.5-8b-text-Q4_K_M-GGUF`, converted from `andreasmartin/apertus-v1.5-8b-text`) | Apache-2.0 (inherited) | Optional CPU-only fallback. |

## Software and data

The entries marked *planned* are listed in advance. Versions are pinned in the lock files once the components are added.

| Component | Licence | Status |
|---|---|---|
| axe-core (Deque Systems) | MPL-2.0 | planned: deterministic WCAG checks; the file is shipped unmodified |
| Playwright | Apache-2.0 | planned |
| FastAPI, Pydantic, Uvicorn | MIT / BSD-3-Clause | planned |
| Vue.js, Vite | MIT | planned |
| llama.cpp server image | MIT | planned, optional |
| vLLM | Apache-2.0 | planned, optional |
| Inter (font) | SIL Open Font License 1.1 | planned |
| Atkinson Hyperlegible Next (font, Braille Institute) | SIL Open Font License 1.1 | planned |
| W3C ACT Rules test cases (<https://act-rules.github.io/testcases.json>) | W3C Software and Document Notice and License | planned: part of the evaluation set. The full notice will be reproduced in `data/` and any changes (translations) marked. |
