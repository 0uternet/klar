# Klar. container image (multi-stage). Built by `make run` / docker compose.
#
#   web-build   node 22 (alpine)   builds the Vue 3 UI (src/web) into src/klar/api/static
#   web-check   from web-build     vue-tsc type-check (only for `make test`)
#   data        node 22 (alpine)   picks the runtime data: data/demo-site and data/replay
#   base        Playwright Python  Python 3.12 + Chromium + the klar package + the built UI
#   test        from base          dev dependencies + the full source tree (only for `make test`)
#   runtime     from base          the image that `make run` starts (non-root, port 8080)
#
# Reproducibility
#   * Base images are pinned by tag AND by multi-arch digest (linux/amd64 + linux/arm64).
#   * PLAYWRIGHT_VERSION must equal the `playwright==` pin in pyproject.toml: the base image
#     ships exactly the browser builds that this Python package version drives. The build
#     checks it; on a mismatch it prints a warning and downloads the matching Chromium
#     (needs network at build time) so the image still works.
#   * No `# syntax=` directive on purpose: the built-in BuildKit frontend is used, so no
#     extra frontend image is pulled at build time.

ARG NODE_IMAGE=node:22.23.3-alpine3.23@sha256:baf676f7d0e552f3231945c2f979055ca121bce128c152f7a34e6bd1728b1c5a
ARG PLAYWRIGHT_IMAGE=mcr.microsoft.com/playwright/python:v1.63.0-noble@sha256:72bd171a9ffc2b4b59532aaa6210e21014d07093120dc25528870c0b840da1f0

# ---------------------------------------------------------------------------- web UI
FROM ${NODE_IMAGE} AS web-build
ENV npm_config_audit=false \
    npm_config_fund=false \
    npm_config_update_notifier=false
# Same layout as the repository: vite writes to ../klar/api/static.
WORKDIR /build/src/web
COPY src/web/package.json src/web/package-lock.json ./
RUN npm ci
COPY src/web/ ./
RUN npm run build \
 && { test -f /build/src/klar/api/static/index.html \
      || { echo "ERROR: the web build did not produce src/klar/api/static/index.html" >&2; exit 1; }; }

FROM web-build AS web-check
RUN npm run typecheck && touch /tmp/web-typecheck.ok

# ---------------------------------------------------------------------------- runtime data
FROM ${NODE_IMAGE} AS data
COPY data/ /tmp/data/
RUN mkdir -p /out \
 && for d in demo-site replay; do \
      if [ -d "/tmp/data/$d" ]; then cp -a "/tmp/data/$d" /out/; \
      else echo "WARNING: data/$d is missing: the demo scan / replay mode will not work" >&2; fi; \
    done

# ---------------------------------------------------------------------------- python base
FROM ${PLAYWRIGHT_IMAGE} AS base
ARG PLAYWRIGHT_VERSION=1.63.0
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_ROOT_USER_ACTION=ignore \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
WORKDIR /app

# 1) Third-party dependencies only: this layer stays cached until pyproject.toml changes.
COPY deploy/pyproject_deps.py /opt/klar-build/pyproject_deps.py
COPY pyproject.toml ./
RUN python3 /opt/klar-build/pyproject_deps.py runtime > /opt/klar-build/requirements.txt \
 && pip install -r /opt/klar-build/requirements.txt

# 2) The browser must match the Playwright Python package (see header).
RUN v="$(python3 -c 'import importlib.metadata as m; print(m.version("playwright"))' 2>/dev/null || echo none)"; \
    if [ "$v" = "none" ]; then \
      echo "ERROR: pyproject.toml must depend on playwright==${PLAYWRIGHT_VERSION}" >&2; exit 1; \
    elif [ "$v" != "${PLAYWRIGHT_VERSION}" ]; then \
      echo "WARNING: pyproject.toml pins playwright==$v but the base image ships browsers for ${PLAYWRIGHT_VERSION}." >&2; \
      echo "WARNING: downloading the matching Chromium now (build-time network). Align the two pins." >&2; \
      python3 -m playwright install --with-deps chromium && rm -rf /var/lib/apt/lists/* && chmod -R a+rX /ms-playwright; \
    fi

# 3) The klar package (non-editable install into site-packages). The source copy and the
#    in-tree build directories are removed: only the installed package remains.
COPY README.md ./
COPY src/klar ./src/klar
RUN pip install . \
 && rm -rf /app/src /app/build \
 && command -v klar >/dev/null

# 4) The built UI, copied into the installed package (klar/api/static).
COPY --from=web-build /build/src/klar/api/static /opt/klar-build/static
RUN pkg="$(python3 -c 'import importlib.util as u; print(u.find_spec("klar").submodule_search_locations[0])')" \
 && rm -rf "$pkg/api/static" \
 && mkdir -p "$pkg/api" \
 && cp -a /opt/klar-build/static "$pkg/api/static" \
 && rm -rf /opt/klar-build/static \
 && test -f "$pkg/api/static/index.html"

# ---------------------------------------------------------------------------- tests (make test)
FROM base AS test
# Pulls the web type-check into this target: `docker build --target test` runs both.
COPY --from=web-check /tmp/web-typecheck.ok /tmp/web-typecheck.ok
WORKDIR /work
COPY . /work
COPY --from=web-build /build/src/klar/api/static /work/src/klar/api/static
RUN python3 /opt/klar-build/pyproject_deps.py dev /work/pyproject.toml > /opt/klar-build/requirements-dev.txt \
 && pip install -r /opt/klar-build/requirements-dev.txt \
 && { python3 -m pytest --version >/dev/null 2>&1 || pip install pytest; }
ENV HOME=/tmp
CMD ["python3", "-m", "pytest", "-q"]

# ---------------------------------------------------------------------------- runtime (default)
FROM base AS runtime
LABEL org.opencontainers.image.title="Klar." \
      org.opencontainers.image.description="Meaning checks for an accessible Swiss web, powered by Apertus" \
      org.opencontainers.image.licenses="Apache-2.0" \
      org.opencontainers.image.source="https://github.com/0uternet/klar"

# Non-root user. docker-compose.yml may run the container as the host user instead
# (KLAR_UID/KLAR_GID) so files written to the ./var bind mount stay yours, hence the
# world-writable (sticky) runtime directories and HOME.
RUN groupadd --gid 10001 klar \
 && useradd --uid 10001 --gid 10001 --home-dir /home/klar --create-home --shell /usr/sbin/nologin klar \
 && mkdir -p /app/var /app/eval/results \
 && chown -R 10001:10001 /app/var /app/eval /home/klar \
 && chmod 1777 /app/var /app/eval/results /home/klar

COPY --from=data /out/ /app/data/
# Live modes append new model answers to the replay store (klar/llm/cache.py). Inside the
# container that store is writable but ephemeral; mount ./data/replay to keep recordings.
RUN mkdir -p /app/data/replay && chmod -R a+rwX /app/data/replay && chmod 1777 /app/data/replay

# KLAR_DATA_DIR = runtime data (SQLite DB, scans, screenshots, reports), bind-mounted to ./var.
# KLAR_PROJECT_ROOT = where data/replay and data/demo-site are found (see klar/config.py).
ENV HOME=/home/klar \
    KLAR_PROJECT_ROOT=/app \
    KLAR_DATA_DIR=/app/var \
    DO_NOT_TRACK=1

USER 10001:10001
WORKDIR /app
EXPOSE 8080
HEALTHCHECK --interval=10s --timeout=5s --start-period=60s --retries=6 \
  CMD curl -fsS http://127.0.0.1:8080/api/health >/dev/null || exit 1
CMD ["klar", "serve", "--host", "0.0.0.0", "--port", "8080"]
