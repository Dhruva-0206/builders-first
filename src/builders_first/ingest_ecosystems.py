"""D1: Open Dev Data (Electric Capital) repo lists per ecosystem, sub-ecosystems included.

Source: Open Dev Data by Electric Capital — https://github.com/electric-capital/open-dev-data (CC BY 4.0)

We shallow-clone the taxonomy repo into data/raw/open-dev-data and load its migrations with
the `open_dev_data.taxonomy` module (same code path as `open-dev-data export -e <Eco>`; we
call it directly because the CLI eagerly imports an optional TUI).

Writes data/cache/repos_<eco>.csv (repo, branch) and data/cache/ecosystems_meta.json.
"""
from __future__ import annotations

import json
import re
import subprocess

import pandas as pd

from .paths import CACHE, RAW

ECOSYSTEMS = ["NEAR", "Solana", "Sui", "Aptos", "Base"]
PEERS = ["Solana", "Sui", "Aptos", "Base"]
ODD_URL = "https://github.com/electric-capital/open-dev-data.git"
ODD_DIR = RAW / "open-dev-data"
GH = re.compile(r"^https?://github\.com/([^/]+)/([^/#?]+)", re.I)


def slug(eco: str) -> str:
    return eco.lower().replace(" ", "_")


def ensure_clone() -> str:
    if not ODD_DIR.exists():
        subprocess.run(["git", "clone", "--depth", "1", ODD_URL, str(ODD_DIR)], check=True)
    sha = subprocess.run(["git", "-C", str(ODD_DIR), "rev-parse", "HEAD"], capture_output=True, text=True, check=True)
    return sha.stdout.strip()


def repo_key(url: str) -> str | None:
    """'https://github.com/Owner/Repo' -> 'owner/repo' (lower-case, GH Archive repo.name form)."""
    m = GH.match(url.strip())
    if not m:
        return None
    return f"{m.group(1)}/{re.sub(r'\.git$', '', m.group(2))}".lower()


def export(tax, eco: str) -> pd.DataFrame:
    out = RAW / f"odd_{slug(eco)}.jsonl"
    tax.export_json(str(out), eco)
    rows = [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines() if line.strip()]
    df = pd.DataFrame(
        [{"repo": repo_key(r["repo_url"]), "branch": "/".join(r["branch"])} for r in rows]
    )
    df = df.dropna(subset=["repo"]).drop_duplicates("repo").sort_values("repo").reset_index(drop=True)
    return df


def main() -> None:
    from open_dev_data import taxonomy

    sha = ensure_clone()
    tax = taxonomy.Taxonomy()
    tax.load(str(ODD_DIR / "migrations"))
    meta = {"source": "Open Dev Data by Electric Capital", "url": "https://github.com/electric-capital/open-dev-data",
            "license": "CC BY 4.0", "commit": sha, "ecosystems": {}}
    for eco in ECOSYSTEMS:
        df = export(tax, eco)
        df.to_csv(CACHE / f"repos_{slug(eco)}.csv", index=False)
        meta["ecosystems"][eco] = {"repos": len(df), "sub_ecosystems": int(df.branch.replace("", pd.NA).dropna().str.split("/").str[0].nunique())}
        print(eco, meta["ecosystems"][eco])
    (CACHE / "ecosystems_meta.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
