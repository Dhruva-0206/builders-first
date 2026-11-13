"""Published prose follows src/builders_first/style_rules.py: no em dashes, no banned words."""
import json
import re
from html.parser import HTMLParser

import pytest

from builders_first.paths import ROOT, SITE
from builders_first.style_rules import ALLOWLIST, BANNED, EM_DASH, VERBATIM_END, VERBATIM_START


class _Text(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts, self.skip = [], 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.skip += 1
        for k, v in attrs:  # aria-label, alt, title and meta content are read by people too
            if k in ("aria-label", "alt", "title", "content") and v:
                self.parts.append(v)

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self.skip -= 1

    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)


def _site_text() -> str:
    raw = (SITE / "index.html").read_text(encoding="utf-8")
    p = _Text()
    p.feed(raw)
    # Chart titles and annotations live inside the Plotly JSON in <script>; check their strings too.
    js = " ".join(json.loads(f'"{s}"') for s in re.findall(r'"text":"((?:[^"\\]|\\.)*)"', raw))
    return "".join(p.parts) + "\n" + js


def _strip_verbatim(text: str) -> str:
    if VERBATIM_START in text:
        a, rest = text.split(VERBATIM_START, 1)
        return a + rest.split(VERBATIM_END, 1)[1]
    return text


def _docs():
    out = {"README.md": (ROOT / "README.md").read_text(encoding="utf-8"),
           "THESIS.md": _strip_verbatim((ROOT / "THESIS.md").read_text(encoding="utf-8")),
           "site/index.html": _site_text()}
    for p in sorted((ROOT / "docs").glob("*.md")):
        out[f"docs/{p.name}"] = p.read_text(encoding="utf-8")
    return out


DOCS = _docs()


@pytest.mark.parametrize("name", sorted(DOCS))
def test_no_em_dash(name):
    text = DOCS[name]
    for ok in ALLOWLIST:
        text = text.replace(ok, "")
    bad = [line.strip()[:80] for line in text.splitlines() if EM_DASH in line]
    assert not bad, f"{name}: em dash in {bad[:3]}"


@pytest.mark.parametrize("name", sorted(DOCS))
def test_no_banned_words(name):
    text = DOCS[name].lower().replace("’", "'")
    hits = [w for w in BANNED if re.search(r"(?<![\w-])" + re.escape(w) + r"(?![\w-])", text)]
    assert not hits, f"{name}: banned words {hits}"


def test_verbatim_block_matches_preregistration():
    import subprocess

    try:
        orig = subprocess.run(["git", "show", "333ea0c:THESIS.md"], cwd=ROOT, capture_output=True, text=True,
                              check=True, encoding="utf-8").stdout
    except Exception:
        pytest.skip("commit 333ea0c not available (shallow clone)")
    cur = (ROOT / "THESIS.md").read_text(encoding="utf-8")
    block = cur.split(VERBATIM_START, 1)[1].split(VERBATIM_END, 1)[0].strip("\n")
    assert block in orig, "pre-registered claims in THESIS.md differ from commit 333ea0c"
