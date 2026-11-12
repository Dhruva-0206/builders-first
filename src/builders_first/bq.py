"""BigQuery helpers: every query is dry-run first and its bytes logged to sql/COSTS.md."""
from __future__ import annotations

import os
from datetime import datetime, timezone

from dotenv import load_dotenv

from .paths import ROOT, SQL

load_dotenv(ROOT / ".env")
COSTS = SQL / "COSTS.md"
HARD_LIMIT_GB = 150.0   # abort above this (CLAUDE.md §5)
ASK_LIMIT_GB = 20.0     # human approval needed above this (lead's rule, 2026-11-12)
OVERRUN = 1.10          # stop if billed bytes exceed the dry-run estimate by >10%


def project() -> str:
    p = os.environ.get("GCP_PROJECT")
    if not p:
        raise SystemExit("GCP_PROJECT is not set (see .env.example)")
    return p


def client():
    from google.cloud import bigquery

    return bigquery.Client(project=project())


def sql_text(name: str, **params) -> str:
    text = (SQL / f"{name}.sql").read_text(encoding="utf-8")
    for k, v in params.items():
        text = text.replace("{{" + k + "}}", str(v))
    return text


def _log(name: str, nbytes: int, note: str) -> None:
    if not COSTS.exists():
        COSTS.write_text("# BigQuery dry-run costs\n\n| when (UTC) | query | GB processed | note |\n|---|---|---|---|\n", encoding="utf-8")
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
    with COSTS.open("a", encoding="utf-8") as f:
        f.write(f"| {ts} | `{name}` | {nbytes / 1e9:.2f} | {note} |\n")


def dry_run(sql: str, name: str, note: str = "dry run") -> int:
    from google.cloud import bigquery

    job = client().query(sql, job_config=bigquery.QueryJobConfig(dry_run=True, use_query_cache=False))
    n = int(job.total_bytes_processed or 0)
    _log(name, n, note)
    return n


def run(sql: str, name: str, approved_gb: float = ASK_LIMIT_GB):
    """Dry-run, enforce limits, execute once. Returns (DataFrame, estimated_bytes, billed_bytes).

    The caller saves the result first, then checks billed vs estimate (OVERRUN).
    """
    import pandas as pd

    est = dry_run(sql, name)
    gb = est / 1e9
    if gb > HARD_LIMIT_GB:
        raise SystemExit(f"{name}: {gb:.1f} GB exceeds hard limit {HARD_LIMIT_GB} GB; aborting")
    if gb > approved_gb:
        raise SystemExit(f"{name}: {gb:.1f} GB exceeds approved {approved_gb} GB; ask the human first")
    job = client().query(sql)
    rows = [dict(r.items()) for r in job.result()]
    billed = int(job.total_bytes_billed or 0)
    _log(name, billed, f"ACTUAL billed (estimate {gb:.2f} GB, cache hit {job.cache_hit})")
    print(f"[bq] {name}: estimate {gb:.2f} GB, billed {billed / 1e9:.2f} GB", flush=True)
    return pd.DataFrame(rows), est, billed
