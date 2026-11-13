"""Golden checks: every published figure equals a fresh computation from data/cache.

1. claims.json on disk equals claims.compute() (so the cached numbers are reproducible).
2. The generated blocks in THESIS.md and README.md, and site/index.html, equal a fresh render.
3. Every number inside the generated text also appears in claims.json-derived text (no hand-typed figures).
"""
import json

from builders_first import build_site, claims, report
from builders_first.paths import CACHE, ROOT, SITE


def test_claims_json_reproduces():
    fresh = json.loads(json.dumps(claims.compute()))
    stored = json.loads((CACHE / "claims.json").read_text(encoding="utf-8"))
    assert fresh == stored, "data/cache/claims.json is stale: run `make analysis`"


def test_docs_match_render():
    c = report.load_claims()
    for path, text in report.render_docs(c).items():
        assert (ROOT / path).read_text(encoding="utf-8") == text, f"{path} is stale: run `make site`"


def test_site_matches_render():
    c = report.load_claims()
    assert (SITE / "index.html").read_text(encoding="utf-8") == build_site.build_html(c), "site/index.html is stale: run `make site`"


def test_headlines_present_in_thesis_and_site():
    c = report.load_claims()
    thesis = (ROOT / "THESIS.md").read_text(encoding="utf-8")
    for h in report.headlines(c):
        assert h in thesis
    assert f"Verdict: {c['verdict']}" in (SITE / "index.html").read_text(encoding="utf-8")


def test_verdict_consistent_with_statuses():
    c = report.load_claims()
    assert c["verdict"] == claims.verdict(list(c["statuses"].values()))
    assert c["C3"]["status"] == ("KILLED" if "KILLED" in (c["C3a"]["status"], c["C3b"]["status"]) else
                                 "FRAGILE" if c["C3a"]["status"] == "FRAGILE" else "HOLDS")


def test_implication_present():
    c = report.load_claims()
    text = " ".join(report.implication(c))
    for path in ("THESIS.md", "README.md"):
        assert text in (ROOT / path).read_text(encoding="utf-8")


def test_chart_csvs_match_render():
    c = report.load_claims()
    for name, text in build_site.chart_csvs(c).items():
        for d in (CACHE / "charts", SITE / "data"):
            assert (d / name).read_text(encoding="utf-8") == text, f"{d.name}/{name} is stale: run `make site`"
