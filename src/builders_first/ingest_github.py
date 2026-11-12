"""D6: GitHub REST API pull for the NEAR HACKATHON cohort (C3b).

For every hackathon repo on GitHub (data/cache/hackathon_projects.csv):
  GET /repos/{o}/{r}/commits?since=2026-10-19T00:00:00Z&per_page=100   (default branch, all pages)
For every distinct commit-author login:
  GET /users/{login}                                                    (account created_at)

Every response is cached under data/raw/github/ (resumable: cached pages are never refetched).
Respects X-RateLimit-Remaining / X-RateLimit-Reset and Retry-After.

Writes:
  data/cache/hackathon_commits.csv   repo, sha, author_dev, is_bot, author_date, ai_tool, ai_trailer
  data/cache/hackathon_repos.csv     repo, status, commits
  data/cache/hackathon_authors.csv   dev, created_at, feed_* (summary of GET /users/{login}/events/public:
     last 90 days / max 300 events; feed_prior_near = a Push/PR event on a NEAR-ecosystem repo before
     2026-10-19, used to correct the GH Archive coverage drop when classifying authors as new vs returning)
Logins are stored only as dev_hash(login); raw responses stay in gitignored data/raw/github/.
Commit messages are not copied into the cache; only the trailer flag and matched tool are kept.
"""
from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv

from .ids import dev_hash
from .paths import CACHE, RAW, ROOT

SINCE = "2026-10-19T00:00:00Z"
FEED_CAP = 300  # GitHub serves at most 300 public events per user
API = "https://api.github.com"
OUT = RAW / "github"

AI_TRAILER = re.compile(
    r"co-authored-by:.*?(claude|anthropic|codex|openai|copilot|cursor|devin|gemini|aider)", re.I
)
AI_GENERATED = re.compile(r"generated with \[?claude code", re.I)
BOT = re.compile(r"(\[bot\]$|-bot$|^dependabot|^github-actions|^renovate)", re.I)


def ai_match(message: str) -> str:
    """Return the matched AI tool name (lower-case), or '' if no AI trailer."""
    m = AI_TRAILER.search(message or "")
    if m:
        return m.group(1).lower()
    if AI_GENERATED.search(message or ""):
        return "claude"
    return ""


def is_bot(login: str) -> bool:
    return bool(BOT.search(login or ""))


class GH:
    def __init__(self, token: str):
        self.s = requests.Session()
        self.s.headers.update({"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json",
                               "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "builders-first-research"})

    def get(self, url: str, params=None) -> requests.Response:
        for attempt in range(6):
            try:
                r = self.s.get(url, params=params, timeout=60)
            except requests.RequestException:
                time.sleep(5 * (attempt + 1))
                continue
            rem = int(r.headers.get("X-RateLimit-Remaining", "100"))
            if r.status_code in (403, 429) and (rem == 0 or "Retry-After" in r.headers):
                wait = int(r.headers.get("Retry-After", "0")) or max(5, int(r.headers.get("X-RateLimit-Reset", time.time() + 60)) - int(time.time()) + 5)
                print(f"  rate limited; sleeping {wait}s", flush=True)
                time.sleep(wait)
                continue
            if r.status_code >= 500:
                time.sleep(5 * (attempt + 1))
                continue
            if rem < 50:
                wait = max(5, int(r.headers.get("X-RateLimit-Reset", time.time() + 60)) - int(time.time()) + 5)
                print(f"  {rem} requests left; sleeping {wait}s", flush=True)
                time.sleep(wait)
            return r
        return r


def _cache_path(*parts: str) -> Path:
    p = OUT.joinpath(*parts)
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def fetch_commits(gh: GH, owner: str, repo: str) -> dict:
    """Fetch all commit pages for one repo; returns {'status': ..., 'pages': [...]}. Cached per repo."""
    key = f"{owner}__{repo}".lower()
    path = _cache_path("commits", f"{key}.json")
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    pages, url, params, status = [], f"{API}/repos/{owner}/{repo}/commits", {"since": SINCE, "per_page": 100}, "ok"
    while url:
        r = gh.get(url, params)
        if r.status_code == 409:   # empty repository
            status = "empty"
            break
        if r.status_code != 200:
            status = f"http_{r.status_code}"
            break
        pages.append(r.json())
        url, params = r.links.get("next", {}).get("url"), None
    out = {"owner": owner, "repo": repo, "status": status, "pages": pages}
    path.write_text(json.dumps(out), encoding="utf-8")
    return out


def fetch_user(gh: GH, login: str) -> dict:
    path = _cache_path("users", f"{login.lower()}.json")
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    r = gh.get(f"{API}/users/{login}")
    d = r.json() if r.status_code == 200 else {}
    out = {"login": login, "status": r.status_code, "created_at": d.get("created_at")}
    path.write_text(json.dumps(out), encoding="utf-8")
    return out


def fetch_events(gh: GH, login: str) -> dict:
    """Public events of a user (GitHub serves at most the last 90 days / 300 events)."""
    path = _cache_path("events", f"{login.lower()}.json")
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    events, url, params, status = [], f"{API}/users/{login}/events/public", {"per_page": 100}, 200
    while url:
        r = gh.get(url, params)
        status = r.status_code
        if status != 200:
            break
        events.extend({"type": e.get("type"), "repo": (e.get("repo") or {}).get("name", ""), "created_at": e.get("created_at")}
                      for e in r.json())
        url, params = r.links.get("next", {}).get("url"), None
    out = {"login": login, "status": status, "events": events}
    path.write_text(json.dumps(out), encoding="utf-8")
    return out


def feed_summary(d: dict, near_repos: set[str]) -> dict:
    """Summarise one author's public event feed without keeping repo names or logins."""
    ev = [e for e in d["events"] if e.get("created_at")]
    prior = [e for e in ev if e["created_at"] < SINCE and e["type"] in ("PushEvent", "PullRequestEvent")]
    oldest = min((e["created_at"] for e in ev), default="")
    return {
        "feed_status": d["status"],
        "feed_events": len(ev),
        "feed_capped": len(ev) >= FEED_CAP,
        "feed_reaches_before": bool(oldest) and oldest < SINCE,
        "feed_prior_events": len(prior),
        "feed_prior_near": any(e["repo"].lower() in near_repos for e in prior),
    }


def build_cache(gh: GH | None, repos: pd.DataFrame) -> None:
    """Build the committed caches from data/raw/github. Logins are replaced by dev_hash()."""
    commits, repo_rows = [], []
    for o, r in zip(repos.gh_owner, repos.gh_repo):
        d = fetch_commits(gh, o, r)
        n = 0
        for page in d["pages"]:
            for c in page:
                n += 1
                login = ((c.get("author") or {}).get("login") or "").lower()
                commits.append({
                    "repo": f"{o}/{r}".lower(),
                    "sha": c.get("sha"),
                    "author_dev": dev_hash(login) if login else "",
                    "is_bot": is_bot(login),
                    "author_date": ((c.get("commit") or {}).get("author") or {}).get("date"),
                    "ai_tool": ai_match((c.get("commit") or {}).get("message") or ""),
                    "_login": login,
                })
        repo_rows.append({"repo": f"{o}/{r}".lower(), "status": d["status"], "commits": n})

    cdf = pd.DataFrame(commits).drop_duplicates(["repo", "sha"])
    cdf["ai_trailer"] = cdf.ai_tool != ""
    logins = sorted(set(cdf.loc[(cdf._login != "") & ~cdf.is_bot, "_login"]))
    cdf.drop(columns="_login").sort_values(["repo", "author_date", "sha"]).to_csv(CACHE / "hackathon_commits.csv", index=False)
    pd.DataFrame(repo_rows).sort_values("repo").to_csv(CACHE / "hackathon_repos.csv", index=False)

    near_repos = set(pd.read_csv(CACHE / "repos_near.csv", usecols=["repo"]).repo.str.lower())
    rows = []
    for lg in logins:
        u = fetch_user(gh, lg)
        rows.append({"dev": dev_hash(lg), "created_at": u.get("created_at"), **feed_summary(fetch_events(gh, lg), near_repos)})
    pd.DataFrame(rows).sort_values("dev").to_csv(CACHE / "hackathon_authors.csv", index=False)
    old = CACHE / "hackathon_author_events.csv"
    if old.exists():
        old.unlink()
    print(f"repos={len(repo_rows)} commits={len(cdf)} authors={len(rows)}")


def main() -> None:
    load_dotenv(ROOT / ".env")
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise SystemExit("GITHUB_TOKEN is not set (see .env.example)")
    proj = pd.read_csv(CACHE / "hackathon_projects.csv", dtype=str).fillna("")
    repos = proj[proj.gh_owner != ""][["gh_owner", "gh_repo"]].drop_duplicates()
    repos = repos.assign(k=(repos.gh_owner + "/" + repos.gh_repo).str.lower()).drop_duplicates("k")
    build_cache(GH(token), repos)


if __name__ == "__main__":
    main()
