"""Store: scan list for the home page (page title + findings still to review)."""

from datetime import datetime, timezone

from klar.models import Finding, Scan
from klar.store import Store


def _finding(fid: str) -> Finding:
    return Finding(id=fid, criterion="2.4.4", criterion_name="Link Purpose (In Context)", level="A", act_rule=None,
                   en301549="9.2.4.4", outcome="failed", source="heuristic", confidence="high",
                   page_url="https://x.test/", selector="a", excerpt="Mehr", context_shown={}, explanation="e",
                   user_impact="u", fix_diff=None, fix_hint=None, screenshot=None, model=None,
                   reason_code="generic_no_context")


def test_list_scans_has_title_and_to_review(tmp_path):
    store = Store(tmp_path / "klar.db")
    scan = Scan(id="abcdef0123", url="https://x.test/", created_at=datetime.now(timezone.utc), mode="replay",
                model="m", ui_lang="en", state="done", progress=[], coverage={},
                findings=[_finding("abcdef0123-a"), _finding("abcdef0123-b")],
                stats={"page_title": "Startseite Rebenau", "max_llm_calls": 150})
    store.save_scan(scan)
    [row] = store.list_scans()
    assert row["page_title"] == "Startseite Rebenau" and row["to_review"] == 2
    store.write_review("abcdef0123-a", "abcdef0123", "accepted")
    assert store.list_scans()[0]["to_review"] == 1
    assert store.get_scan("abcdef0123").stats["to_review"] == 1
    store.close()
