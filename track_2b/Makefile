# Klar. - run every target from track_2b/.
#
# Judges / quick start: `make run`. It needs only Docker (Engine or Desktop) with Compose
# v2.24+, and starts the app on http://localhost:8080 in replay mode when there is no .env:
# no key, no model download. Then it scans the bundled demo site and prints the report path.
#
#   make run            app only (.env if present, otherwise replay mode) + demo scan
#   make run-gpu        + Apertus 1.5 8B on the local NVIDIA GPU (official swiss-ai vLLM image)
#   make run-cpu        + Apertus 1.5 8B text-only GGUF on CPU (llama.cpp), downloaded + verified
#   make eval           evaluation on data/testset -> eval/results/ (test split: git fetch --tags first)
#   make test           pytest + web type-check, inside Docker
#   make airgap-check   proof of offline operation (internal-only Docker network)
#   make bundle         offline bundle (images + weights) for an air-gapped site
#   make stop | logs | clean | help
#
# Model endpoint: the template's variables LLM_BASE_URL, LLM_NAME, LLM_API_KEY, exported in the
# shell or written in .env (the shell wins). With no LLM_BASE_URL at all, Klar. runs in replay mode.
# Knobs: KLAR_PORT=8090 make run, BUILD=0 (use the existing image), see `make help`.
# Deployment details, including a container-free install: docs/DEPLOYMENT.md.
# Compatible with GNU make 3.81 (macOS default).

SHELL := /bin/sh
.DEFAULT_GOAL := run

# Optional .env, read here only to choose defaults and print where inference runs.
# docker compose reads .env itself (variable interpolation). The key is never printed.
DOTENV := $(wildcard .env)
dotenv  = $(if $(DOTENV),$(shell sh deploy/dotenv_get.sh .env $(1)))

COMPOSE     ?= docker compose
# Host port / bind address: command line or shell > .env > default.
ifeq ($(origin KLAR_PORT),undefined)
KLAR_PORT := $(or $(call dotenv,KLAR_PORT),8080)
endif
ifeq ($(origin KLAR_BIND),undefined)
KLAR_BIND := $(or $(call dotenv,KLAR_BIND),127.0.0.1)
endif
KLAR_IMAGE  ?= klar:local
BUILD       ?= 1
DEMO        ?= 1
APP_WAIT    ?= 300
LLM_WAIT    ?= 3600
AIRGAP_LLM  ?= replay
BUNDLE      ?= cpu
MODEL       := swiss-ai/Apertus-v1.5-8B
# URL used by the host to reach the app: follows KLAR_BIND (a wildcard or loopback bind -> localhost).
# IPv6 literals are accepted with or without brackets; compose and URLs get the bracketed form.
BIND_BARE    = $(subst ],,$(subst [,,$(KLAR_BIND)))
ifneq ($(findstring :,$(KLAR_BIND)),)
override KLAR_BIND := [$(BIND_BARE)]
endif
APP_HOST     = $(if $(filter 127.0.0.1 0.0.0.0 :: ::1 localhost,$(BIND_BARE)),localhost,$(BIND_BARE))
APP_URL      = http://$(if $(findstring :,$(APP_HOST)),[$(APP_HOST)],$(APP_HOST)):$(KLAR_PORT)
# Bound to a specific address: the app must also accept that Host header (its DNS-rebinding
# allow-list only knows localhost by default). Values from the shell or .env are kept.
comma := ,
ifneq ($(APP_HOST),localhost)
ifeq ($(origin KLAR_ALLOWED_HOSTS),undefined)
KLAR_ALLOWED_HOSTS := $(call dotenv,KLAR_ALLOWED_HOSTS)
endif
override KLAR_ALLOWED_HOSTS := $(if $(strip $(KLAR_ALLOWED_HOSTS)),$(KLAR_ALLOWED_HOSTS)$(comma))$(APP_HOST)
export KLAR_ALLOWED_HOSTS
endif
DC           = $(COMPOSE)

# The app container runs as the host user, so files in ./var stay yours.
# As root (or without `id`) it keeps the image's own non-root user (10001).
HOST_UID := $(shell id -u 2>/dev/null)
HOST_GID := $(shell id -g 2>/dev/null)
ifeq ($(filter-out 0,$(HOST_UID)),)
KLAR_UID ?= 10001
KLAR_GID ?= 10001
else
KLAR_UID ?= $(HOST_UID)
KLAR_GID ?= $(HOST_GID)
endif

# llama.cpp threads for run-cpu: about one per physical core (half the logical CPUs).
ifeq ($(origin LLAMA_THREADS),undefined)
LLAMA_THREADS := $(shell n=$$(getconf _NPROCESSORS_ONLN 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo 2); \
                   if [ "$$n" -gt 1 ] 2>/dev/null; then echo $$((n / 2)); else echo 1; fi)
endif

ENV_LLM_BASE_URL := $(call dotenv,LLM_BASE_URL)
ENV_LLM_NAME     := $(call dotenv,LLM_NAME)
ENV_LLM_API_KEY  := $(call dotenv,LLM_API_KEY)
ENV_KLAR_REPLAY  := $(call dotenv,KLAR_REPLAY)
HAVE_HF_TOKEN    := $(if $(or $(HF_TOKEN),$(call dotenv,HF_TOKEN)),1)
# A .env endpoint on one of the bundled servers (llm, llm-gpu, llm-cpu) is a mode choice that
# `make run-gpu` / `make run-cpu` replace; any other .env endpoint (e.g. Swiss cloud) is kept.
BUNDLED          := //llm: //llm/ //llm-gpu: //llm-gpu/ //llm-cpu: //llm-cpu/
ENV_EXT_URL      := $(if $(strip $(foreach h,$(BUNDLED),$(findstring $(h),$(ENV_LLM_BASE_URL)))),,$(ENV_LLM_BASE_URL))

# Which source set LLM_BASE_URL, for the banner: make command line, shell environment or .env.
URL_ORIGIN := $(origin LLM_BASE_URL)
SRC_CLI    := $(filter command%,$(URL_ORIGIN))
SRC_SHELL  := $(filter environment%,$(URL_ORIGIN))
SRC_ANY    := $(if $(SRC_CLI),make command line,$(if $(SRC_SHELL),shell environment))

export KLAR_UID KLAR_GID KLAR_PORT KLAR_BIND KLAR_IMAGE LLAMA_THREADS

# Per-target endpoint, exported to docker compose (target-specific export: GNU make >= 3.81).
# Precedence: make command line > shell environment > .env > the target's default below.
# An exported but EMPTY LLM_BASE_URL= also wins over .env (it means: replay mode).
# make run, make eval: replay mode only when no non-empty LLM_BASE_URL is set anywhere.
run eval: export LLM_BASE_URL ?= $(ENV_LLM_BASE_URL)
run eval: export KLAR_REPLAY  ?= $(or $(ENV_KLAR_REPLAY),$(if $(strip $(LLM_BASE_URL)),0,1))
run eval: export LLM_NAME     ?= $(or $(ENV_LLM_NAME),$(MODEL))
run eval: export LLM_API_KEY  ?= $(or $(ENV_LLM_API_KEY),local)
run eval: CFG_SRC = $(or $(SRC_ANY),$(if $(ENV_LLM_BASE_URL),.env,nothing set: replay mode))

run-gpu: DC = $(COMPOSE) --profile gpu
run-gpu: export KLAR_REPLAY  ?= $(or $(ENV_KLAR_REPLAY),0)
run-gpu: export LLM_BASE_URL ?= $(or $(ENV_EXT_URL),http://llm-gpu:8000/v1)
run-gpu: export LLM_NAME     ?= $(if $(ENV_EXT_URL),$(or $(ENV_LLM_NAME),$(MODEL)),$(MODEL))
run-gpu: export LLM_API_KEY  ?= $(if $(ENV_EXT_URL),$(or $(ENV_LLM_API_KEY),local),local)
run-gpu: CFG_SRC = $(or $(SRC_ANY),$(if $(ENV_EXT_URL),.env,make run-gpu default (bundled vLLM service)))

run-cpu: DC = $(COMPOSE) --profile cpu
run-cpu: export KLAR_REPLAY  ?= $(or $(ENV_KLAR_REPLAY),0)
run-cpu: export LLM_BASE_URL ?= $(or $(ENV_EXT_URL),http://llm-cpu:8080/v1)
run-cpu: export LLM_NAME     ?= $(if $(ENV_EXT_URL),$(or $(ENV_LLM_NAME),$(MODEL)),$(MODEL))
run-cpu: export LLM_API_KEY  ?= $(if $(ENV_EXT_URL),$(or $(ENV_LLM_API_KEY),local),local)
run-cpu: CFG_SRC = $(or $(SRC_ANY),$(if $(ENV_EXT_URL),.env,make run-cpu default (bundled llama.cpp service)))

.PHONY: help run run-gpu run-cpu eval test airgap-check download-model bundle \
        stop logs clean preflight preflight-gpu dirs

help:
	@echo "Klar. - make targets (run from track_2b/)"
	@echo "  make run            build + start on $(APP_URL) and scan the bundled demo site"
	@echo "                      (LLM_BASE_URL from the shell or .env; none set = replay mode: no key, no download)"
	@echo "  make run-gpu        + Apertus 1.5 8B on the local NVIDIA GPU (vLLM, driver >= 580, HF_TOKEN once)"
	@echo "  make run-cpu        + Apertus 1.5 8B text-only GGUF on CPU (llama.cpp, 5 GB download once)"
	@echo "  make eval           evaluation on data/testset -> eval/results/ (test split: needs the tag labels-v1, git fetch --tags)"
	@echo "  make test           pytest + web type-check in Docker"
	@echo "  make airgap-check   prove offline operation [AIRGAP_LLM=replay|cpu|gpu]"
	@echo "  make bundle         offline bundle for an air-gapped site [BUNDLE=cpu|gpu|all]"
	@echo "  make download-model fetch + verify the GGUF used by run-cpu"
	@echo "  make stop | logs [SERVICE=app] | clean"
	@echo "Options: KLAR_PORT=8090 (host port), KLAR_BIND=0.0.0.0 (expose on the LAN), BUILD=0 (no rebuild),"
	@echo "         DEMO=0 (start without the demo scan). Endpoint: LLM_BASE_URL / LLM_NAME / LLM_API_KEY (shell or .env)."

preflight:
	@sh deploy/preflight.sh

preflight-gpu:
	@sh deploy/preflight.sh gpu

# Create the bind-mount sources ourselves: if Docker creates them they belong to root.
dirs:
	@mkdir -p var eval/results models/huggingface
	@if [ "$(HOST_UID)" = 0 ]; then chmod 0777 var eval/results; fi

run: preflight dirs
	@sh deploy/endpoint.sh run "$(KLAR_REPLAY)" "$(LLM_BASE_URL)" "$(LLM_NAME)" ./var "$(CFG_SRC)"
	$(if $(filter 1,$(BUILD)),$(DC) build app)
	$(DC) up -d app
	@sh deploy/wait_for.sh "$$($(DC) ps -q app)" $(APP_WAIT) "Klar. app" "$(APP_URL)/api/health"
	@DEMO="$(DEMO)" DC="$(DC)" sh deploy/demo.sh "$(APP_URL)"

run-gpu: preflight-gpu dirs
	@sh deploy/endpoint.sh run-gpu "$(KLAR_REPLAY)" "$(LLM_BASE_URL)" "$(LLM_NAME)" ./var "$(CFG_SRC)"
	@if [ -z "$(HAVE_HF_TOKEN)" ] && [ ! -d models/huggingface/hub/models--swiss-ai--Apertus-v1.5-8B ]; then \
	  echo "WARNING: HF_TOKEN is not set and the weights are not cached in ./models/huggingface yet."; \
	  echo "         swiss-ai/Apertus-v1.5-8B is gated: accept its licence on huggingface.co, then put HF_TOKEN=... in .env"; \
	fi
	$(DC) up -d llm-gpu
	$(if $(filter 1,$(BUILD)),$(DC) build app)
	@sh deploy/wait_for.sh "$$($(DC) ps -q llm-gpu)" $(LLM_WAIT) "llm-gpu (vLLM; first start downloads ~18 GB of weights)"
	$(DC) up -d app
	@sh deploy/wait_for.sh "$$($(DC) ps -q app)" $(APP_WAIT) "Klar. app" "$(APP_URL)/api/health"
	@DEMO="$(DEMO)" DC="$(DC)" sh deploy/demo.sh "$(APP_URL)"

run-cpu: preflight dirs download-model
	@sh deploy/endpoint.sh run-cpu "$(KLAR_REPLAY)" "$(LLM_BASE_URL)" "$(LLM_NAME)" ./var "$(CFG_SRC)"
	$(DC) up -d llm-cpu
	$(if $(filter 1,$(BUILD)),$(DC) build app)
	@sh deploy/wait_for.sh "$$($(DC) ps -q llm-cpu)" $(LLM_WAIT) "llm-cpu (llama.cpp)"
	$(DC) up -d app
	@sh deploy/wait_for.sh "$$($(DC) ps -q app)" $(APP_WAIT) "Klar. app" "$(APP_URL)/api/health"
	@DEMO="$(DEMO)" DC="$(DC)" sh deploy/demo.sh "$(APP_URL)"

# Host curl + sha256 tool if available, otherwise the one-shot model-download container.
download-model: dirs
	@sh deploy/download_model.sh; rc=$$?; \
	if [ $$rc -eq 3 ]; then \
	  echo "    -> no curl/sha256 tool on this host: downloading inside a container instead"; \
	  $(COMPOSE) --profile download run --rm model-download; \
	else exit $$rc; fi

# Uses the same endpoint as `make run` (shell, .env, otherwise replay). With an endpoint on
# llm-gpu / llm-cpu, start that server first (make run-gpu / run-cpu).
# The container has no .git: the host passes the provenance the evaluation needs, i.e. the sha256
# of data/testset/manifest.jsonl at tag labels-v1 (empty if the tag is missing) and the commit.
eval: preflight dirs
	@sh deploy/endpoint.sh eval "$(KLAR_REPLAY)" "$(LLM_BASE_URL)" "$(LLM_NAME)" ./var "$(CFG_SRC)"
	$(if $(filter 1,$(BUILD)),$(DC) build app)
	@if command -v sha256sum >/dev/null 2>&1; then hash="sha256sum"; else hash="shasum -a 256"; fi; \
	sha=""; if git cat-file -e labels-v1:track_2b/data/testset/manifest.jsonl 2>/dev/null; then \
	  sha=$$(git show labels-v1:track_2b/data/testset/manifest.jsonl | $$hash | cut -d" " -f1); fi; \
	commit=$$(git rev-parse HEAD 2>/dev/null || true); \
	echo "    labels-v1 manifest sha256: $${sha:-none (tag labels-v1 not found)}   commit: $${commit:-unknown}"; \
	if [ -z "$$sha" ]; then \
	  echo "    NOTE: the test split needs the git tag labels-v1. In a shallow clone or a download without"; \
	  echo "          tags run: git fetch --tags   (then make eval again). Without it the test split is refused."; \
	fi; \
	echo "$(DC) run --rm --no-deps -e KLAR_LABELS_MANIFEST_SHA256 -e KLAR_GIT_COMMIT -v .../data/testset:/app/data/testset:ro,z app klar eval"; \
	KLAR_LABELS_MANIFEST_SHA256="$$sha" KLAR_GIT_COMMIT="$$commit" \
	  $(DC) run --rm --no-deps -e KLAR_LABELS_MANIFEST_SHA256 -e KLAR_GIT_COMMIT \
	  -v "$(CURDIR)/data/testset:/app/data/testset:ro,z" app klar eval
	@echo; echo "==> Evaluation results: ./eval/results/"; ls -1 eval/results 2>/dev/null || true

test: preflight
	docker build --target test -t klar-test:local .
	docker run --rm --shm-size=1g klar-test:local

airgap-check: preflight dirs
	@AIRGAP_LLM="$(AIRGAP_LLM)" BUILD="$(BUILD)" APP_WAIT="$(APP_WAIT)" LLM_WAIT="$(LLM_WAIT)" \
	  sh deploy/airgap_check.sh

bundle: preflight dirs
	@sh deploy/airgap_bundle.sh save $(BUNDLE)

stop:
	$(COMPOSE) --profile gpu --profile cpu --profile download down --remove-orphans
	@docker compose -p klar-airgap -f docker-compose.yml -f deploy/compose.airgap.yml \
	  --profile gpu --profile cpu down --remove-orphans >/dev/null 2>&1 || true

logs:
	$(COMPOSE) --profile gpu --profile cpu logs -f --tail=200 $(SERVICE)

# Keeps ./models (downloaded weights) and ./eval/results (may be committed).
clean: stop
	-docker image rm $(KLAR_IMAGE) klar-test:local
	rm -rf var dist
	@echo "Kept ./models (weights) and ./eval/results; delete them by hand if needed."
