"""Shared filesystem paths."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "data" / "cache"
RAW = ROOT / "data" / "raw"
SQL = ROOT / "sql"
SITE = ROOT / "site"

for _p in (CACHE, RAW):
    _p.mkdir(parents=True, exist_ok=True)
