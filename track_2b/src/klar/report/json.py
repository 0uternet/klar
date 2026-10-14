"""JSON export: the Scan object (klar/models.py) plus the disclaimer and generator."""

from __future__ import annotations

import json

from klar import __version__
from klar.models import Scan


def to_json(scan: Scan) -> str:
    from klar.report import disclaimer

    data = {"disclaimer": disclaimer(scan), "generator": {"name": "Klar.", "version": __version__}}
    data.update(scan.model_dump(mode="json"))
    return json.dumps(data, ensure_ascii=False, indent=2)
