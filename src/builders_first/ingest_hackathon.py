"""D4 + D5: NEAR HACKATHON submissions.

D4 nearhunt.xyz /api/projects (cursor pagination) -> repo URLs, tracks.
D5 nearhackathon.com /api/projects?page=N        -> official count + track counts.

Writes:
  data/cache/hackathon_projects.csv   one row per nearhunt project
  data/cache/hackathon_official.csv   one row per official submission
  data/cache/hackathon_meta.json      totals, fetch time
"""
from __future__ import annotations

import json
import re
import time
from datetime import datetime, timezone

import pandas as pd
import requests

from .paths import CACHE, RAW

UA = {"User-Agent": "builders-first-research/0.1"}
GH_RE = re.compile(r"https?://(?:www\.)?github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)", re.I)


def parse_github(url: str | None) -> tuple[str, str] | None:
    """Return (owner, repo) from a GitHub URL, or None."""
    if not url:
        return None
    m = GH_RE.search(url)
    if not m:
        return None
    owner, repo = m.group(1), m.group(2)
    repo = re.sub(r"\.git$", "", repo)
    if owner.lower() in {"orgs", "settings", "features", "topics", "sponsors"}:
        return None
    return owner, repo


def _get(url: str, params=None, tries: int = 4) -> dict:
    for i in range(tries):
        try:
            r = requests.get(url, params=params, headers=UA, timeout=60)
            if r.status_code == 200:
                return r.json()
        except requests.RequestException:
            pass
        time.sleep(2 * (i + 1))
    raise RuntimeError(f"failed: {url} {params}")


def fetch_nearhunt() -> tuple[list[dict], dict]:
    items, cursor, meta = [], None, {}
    while True:
        d = _get("https://nearhunt.xyz/api/projects", {"cursor": cursor} if cursor else None)
        items.extend(d.get("items", []))
        meta = d.get("meta", meta)
        cursor = d.get("next_cursor")
        if not cursor:
            break
        time.sleep(0.3)
    return items, meta


def fetch_official() -> tuple[list[dict], int]:
    out, page, total = [], 1, None
    while True:
        d = _get("https://nearhackathon.com/api/projects", {"page": page})
        total = d.get("total", total)
        rows = d.get("projects", [])
        if not rows:
            break
        out.extend(rows)
        if total is not None and len(out) >= total:
            break
        page += 1
        time.sleep(0.2)
    return out, total


def _repo_url(p: dict) -> str | None:
    if p.get("repository_url"):
        return p["repository_url"]
    for link in p.get("links") or []:
        if link.get("kind") in ("repository", "repo", "code") and link.get("url"):
            return link["url"]
    return None


def nearhunt_frame(items: list[dict]) -> pd.DataFrame:
    rows = []
    for p in items:
        url = _repo_url(p)
        gh = parse_github(url)
        pid = str(p.get("id", ""))
        rows.append(
            {
                "id": pid,
                "official_id": pid.split(":", 1)[1] if ":" in pid else "",
                "name": p.get("name") or p.get("project_name") or "",
                "tracks": ";".join(p.get("tracks") or []),
                "repository_url": url or "",
                "gh_owner": gh[0] if gh else "",
                "gh_repo": gh[1] if gh else "",
            }
        )
    df = pd.DataFrame(rows).drop_duplicates("id")
    return df.sort_values("id").reset_index(drop=True)


def main() -> None:
    items, meta = fetch_nearhunt()
    (RAW / "nearhunt_projects.json").write_text(json.dumps(items, ensure_ascii=False), encoding="utf-8")
    hunt = nearhunt_frame(items)
    hunt.to_csv(CACHE / "hackathon_projects.csv", index=False)

    official, total = fetch_official()
    off = pd.DataFrame(
        [{"id": p["id"], "project_name": p.get("project_name", ""), "tracks": ";".join(p.get("tracks") or [])} for p in official]
    ).drop_duplicates("id").sort_values("id")
    off.to_csv(CACHE / "hackathon_official.csv", index=False)

    out = {
        "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "nearhunt_total_reported": meta.get("total"),
        "nearhunt_rows": len(hunt),
        "nearhunt_with_github_repo": int((hunt.gh_owner != "").sum()),
        "nearhunt_without_github_repo": int((hunt.gh_owner == "").sum()),
        "official_total_reported": total,
        "official_rows": len(off),
    }
    (CACHE / "hackathon_meta.json").write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
