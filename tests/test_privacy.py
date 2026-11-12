"""No raw GitHub logins or email addresses in committed data or the site.

Repository identifiers (owner/repo of public hackathon submissions and Open Dev Data repos) are
project identifiers and are allowed; person-level columns must be hashed (see ids.dev_hash).
"""
import json
import re
from pathlib import Path

import pandas as pd
import pytest

from builders_first.paths import CACHE, RAW, SITE

EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
REPO_COLS = {"ai_tool", "tracks", "repo", "repository_url", "gh_owner", "gh_repo", "branch", "name", "project_name", "id", "official_id"}
FORBIDDEN_COLS = {"login", "author_login", "email", "author_email", "prior_repos"}


def _published_files():
    files = [p for p in CACHE.iterdir() if p.suffix in (".csv", ".json", ".gz")]
    files += [p for p in SITE.glob("*") if p.suffix in (".html", ".json", ".js")]
    return files


def _text(p: Path) -> str:
    if p.suffix == ".gz":
        return pd.read_csv(p, dtype=str).to_csv(index=False)
    return p.read_text(encoding="utf-8")


def test_no_emails_or_login_columns():
    for p in _published_files():
        txt = _text(p)
        assert not EMAIL.search(txt), f"email-like string in {p.name}"
        if p.suffix in (".csv", ".gz"):
            cols = set(pd.read_csv(p, nrows=0).columns)
            assert not cols & FORBIDDEN_COLS, f"{p.name} has person-level columns {cols & FORBIDDEN_COLS}"


def test_no_raw_hackathon_logins_outside_repo_columns():
    users = RAW / "github" / "users"
    if not users.exists():
        pytest.skip("raw GitHub cache not present (runs only where `make data` was run)")
    logins = {json.loads(f.read_text(encoding="utf-8"))["login"].lower() for f in users.glob("*.json")}
    for p in _published_files():
        if p.suffix == ".html":
            continue  # checked by build_site, which only embeds aggregates
        df = pd.read_csv(p, dtype=str, keep_default_na=False) if p.suffix in (".csv", ".gz") else None
        if df is None:
            continue
        for col in set(df.columns) - REPO_COLS:
            hits = set(df[col].str.lower()) & logins
            assert not hits, f"{p.name}:{col} contains raw logins"
