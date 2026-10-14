"""EARL 1.0 (W3C Evaluation and Report Language) as JSON-LD.

One earl:Assertion per finding. earl:mode is earl:semiAuto for Apertus findings
(a model pre-judged, a human validates) and for any finding a human reviewed;
earl:automatic for axe-core rules and code heuristics. Findings REJECTED by the
reviewer are left out: the human said the assertion is wrong.
"""

from __future__ import annotations

import json

from klar import __version__
from klar.checks import registry
from klar.models import Finding, Scan

CONTEXT = {
    "earl": "http://www.w3.org/ns/earl#",
    "dct": "http://purl.org/dc/terms/",
    "foaf": "http://xmlns.com/foaf/0.1/",
    "ptr": "http://www.w3.org/2009/pointers#",
    "sch": "https://schema.org/",
    "WCAG21": "https://www.w3.org/TR/WCAG21/#",
    "ACT": "https://act-rules.github.io/rules/",
}


def _mode(f: Finding) -> str:
    return "earl:semiAuto" if f.source == "apertus" or f.status != "to_review" else "earl:automatic"


def assertion(f: Finding, scan: Scan) -> dict:
    crit = registry.get(f.criterion)
    result: dict = {
        "@type": "earl:TestResult",
        "earl:outcome": {"@id": f"earl:{f.outcome}"},
        "dct:description": f.explanation,
        "dct:date": scan.created_at.isoformat(),
        "earl:pointer": {"@type": "ptr:CSSSelectorPointer", "ptr:expression": f.selector},
        "earl:info": f.user_impact,
    }
    test: dict = {"@id": f"WCAG21:{crit.slug}", "@type": "earl:TestRequirement",
                  "dct:title": f"{crit.number} {crit.name}", "dct:isPartOf": "EN 301 549 " + (f.en301549 or "")}
    if f.act_rule:
        test["dct:relation"] = {"@id": f"ACT:{f.act_rule}"}
    if f.axe_rule:
        result["dct:source"] = f"axe-core rule {f.axe_rule}"
    return {
        "@type": "earl:Assertion",
        "@id": f"_:finding-{f.id}",
        "earl:assertedBy": {"@id": "_:klar"},
        "earl:subject": {"@id": "_:subject"},
        "earl:test": test,
        "earl:mode": {"@id": _mode(f)},
        "earl:result": result,
        "dct:source": {"source": f.source, "confidence": f.confidence, "model": f.model, "status": f.status,
                       "reason_code": f.reason_code},
    }


def to_earl(scan: Scan) -> str:
    from klar.report import disclaimer

    graph = [
        {"@id": "_:klar", "@type": ["earl:Assertor", "earl:Software"], "dct:title": "Klar.",
         "dct:hasVersion": __version__, "dct:description": disclaimer(scan)},
        {"@id": "_:subject", "@type": ["earl:TestSubject", "sch:WebPage"], "dct:source": scan.url,
         "dct:date": scan.created_at.isoformat()},
    ]
    graph += [assertion(f, scan) for f in scan.findings if f.status != "rejected"]
    return json.dumps({"@context": CONTEXT, "@graph": graph}, ensure_ascii=False, indent=2)
