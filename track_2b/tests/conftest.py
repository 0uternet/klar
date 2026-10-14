from __future__ import annotations

from pathlib import Path

import pytest

from fake_llm import FakeLLM, klar_responder
from klar.config import Settings


def _chromium_ok() -> bool:
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            p.chromium.launch().close()
        return True
    except Exception:
        return False


_CHROMIUM: bool | None = None


@pytest.fixture(scope="session")
def chromium() -> bool:
    global _CHROMIUM
    if _CHROMIUM is None:
        _CHROMIUM = _chromium_ok()
    if not _CHROMIUM:
        pytest.skip("Playwright Chromium not installed (python -m playwright install chromium)")
    return True


@pytest.fixture
def fake_llm():
    with FakeLLM(klar_responder) as fake:
        yield fake


@pytest.fixture
def make_settings(tmp_path: Path):
    """Isolated settings: nothing is written outside tmp_path."""

    def make(**kw) -> Settings:
        base = dict(
            data_dir=tmp_path / "var",
            replay_dir=tmp_path / "replay",
            demo_dir=tmp_path / "no-demo",
            static_dir=tmp_path / "no-static",
            project_root=tmp_path,
            llm_timeout=20,
            vision_override=False,
            llm_concurrency=2,
            allowed_hosts=("localhost", "127.0.0.1", "::1", "testserver"),
        )
        base.update(kw)
        return Settings(**base)

    return make


@pytest.fixture
def browser(chromium):
    from klar.capture.browser import Browser

    with Browser() as b:
        yield b


@pytest.fixture
def render_html(browser, tmp_path: Path):
    """render_html(html) → CapturedPage with extraction done (live page)."""
    from klar.capture.browser import CaptureOptions, extract, render

    pages = []

    def go(html: str, **opts):
        page = render(browser, html=html, scan_dir=tmp_path / f"scan{len(pages)}", opts=CaptureOptions(**opts))
        extract(page)
        pages.append(page)
        return page

    yield go
    for p in pages:
        p.close()
