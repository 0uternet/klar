# Klar.

**Klar. pre-checks the WCAG 2.1 AA / eCH-0059 criteria that need human judgement, using Apertus.** (eCH-0059 is the Swiss e-government accessibility standard; it adopts WCAG 2.1 AA.) Scanners check that a link text, a label or a language tag *exists*; Klar. checks whether it *makes sense* to someone using a screen reader, in German, French and Italian. Code and axe-core run first and settle the clear cases. Apertus answers one closed question per element that code cannot decide, and each answer must quote the page. A person then accepts or rejects every finding. It runs on-premise, air-gapped, or in a sovereign Swiss cloud.

**Result** (test split, 605 cases, labels frozen before the first test run; [technical report §5](technical_report.md#5-evaluation)): with Apertus 8B on one on-premise GPU, Klar. finds 78 % of real barriers (axe-core: 15 %; the same rules without Apertus: 54 %), with 93 % of its alerts correct, and leaves 12 % of checked elements to a person instead of 45 %. In exchange, 14 % of real barriers are missed (rules alone: 5 %). A page costs about half a centime on-premise; a certification audit costs CHF 3,800–8,500.

```bash
cd track_2b
make run        # Docker: builds, starts http://localhost:8080 and scans the bundled demo site
```

The first run builds the image (about 8 minutes), then scans the 34-page demo site. Open <http://localhost:8080>, choose a demo page under **Recent checks**, open a finding and expand **Context shown to the model**: it shows exactly what Apertus saw and answered. To see real Swiss pages, pick **ebgb.admin.ch** or **biel-bienne.ch** on the home page: their answers were recorded on 16 October 2026, so anything changed since then is left to a person.

With no configuration, `make run` uses **replay mode**: it replays recorded Apertus answers, so you need no key, no GPU and no model download. To use a live Apertus endpoint, set the three LLM_* variables, in your shell or in `track_2b/.env` (see `.env.example`), e.g. Apertus 70B on Phoeniqs, a Swiss cloud:

```bash
export LLM_NAME=inference-apertus-v15-70b
export LLM_BASE_URL=https://maas.phoeniqs.com/v1
export LLM_API_KEY=...
make run
```

| Command | What it does |
|---|---|
| `make run` | App + demo scan (replay, or the endpoint you configured) |
| `make run-gpu` | On-premise: the official Apertus 1.5 vLLM image on a local NVIDIA GPU (8B, text + images) |
| `make run-cpu` | On-premise without a GPU: llama.cpp + 8B text-only GGUF (text criteria only) |
| `make airgap-check` | Runs the demo scan with no route to the internet |
| `make eval` | Recomputes the evaluation (Baseline vs Ours) from `data/testset` |
| `make stop` | Stops everything |

**Where to find the evidence**

| Topic | Evidence |
|---|---|
| Use of Apertus | Apertus answers only what code cannot decide: one closed question per element, with the answer checked against the page ([report §3](technical_report.md#3-use-of-apertus)). The baseline is the same pipeline with every Apertus question left to a person, so the difference is the model's contribution (§5, Table 3). |
| Evaluation | Labelling protocol written before the cases ([`PROTOCOL.md`](data/testset/PROTOCOL.md)); labels frozen by the git tag `labels-v1`; dev/test split by template; leakage check in CI; Wilson intervals, McNemar test, two ablations (§4–5). `make eval` recomputes the results from the committed recordings, without a GPU. |
| Value and cost | Cost per page and per site against a CHF 3,800–8,500 audit; the person's workload is the deferral rate (§5). |
| Deployment | On-premise GPU (`make run-gpu`) or CPU (`make run-cpu`), air-gapped (`make bundle`; `make airgap-check` runs in CI), Swiss cloud (Phoeniqs). Build-time and runtime dependencies are listed in [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md). The interface counts every AI request that leaves the machine. |
| Operations | One command; images pinned by digest; about 900 automated tests in 9 CI jobs; interface in DE/FR/IT/EN; exports in JSON, EARL, CSV and HTML for existing audit workflows. |

- Deployment, target architectures and the threat model: [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md).
- Method, evaluation and limitations: [`technical_report.md`](technical_report.md).
- Klar. assists auditors. **It does not certify conformance.**
