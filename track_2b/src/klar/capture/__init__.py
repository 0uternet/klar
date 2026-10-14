"""Capture: Playwright rendering, DOM snapshot, element extraction, axe-core, probes."""

from klar.capture.browser import Browser, CaptureOptions, extract, render
from klar.capture.page import CapturedPage, candidate_id

__all__ = ["Browser", "CaptureOptions", "CapturedPage", "candidate_id", "extract", "render"]
