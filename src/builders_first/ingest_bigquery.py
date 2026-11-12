"""D2 + D3 via BigQuery. Every query is dry-run first and logged to sql/COSTS.md (see bq.py).

  load-repos   load data/cache/repos_*.csv into <GCP_PROJECT>.builders_first.repos (free load job)
  dryrun       dry-run every chunk and print bytes (no data read)
  gha          GH Archive: (ecosystem, month, login) per yearly chunk -> data/raw/gha/*.csv.gz
  near         NEAR deploys + unique deployers per month (yearly chunks) -> data/cache/near_deploys_monthly.csv

Usage: python -m builders_first.ingest_bigquery [load-repos|dryrun|gha|near|all] [--approved-gb N]
"""
from __future__ import annotations

import argparse
import io
from datetime import date

import pandas as pd

from . import bq
from .ingest_ecosystems import ECOSYSTEMS, slug
from .paths import CACHE, RAW

DATASET = "builders_first"
GHA_START_YEAR = 2021
NEAR_START_YEAR = 2021


def _today() -> date:
    return date.today()


def gha_chunks() -> list[tuple[str, str]]:
    end = _today()
    return [(f"{y}01", f"{y}12" if y < end.year else f"{end.year}{end.month:02d}") for y in range(GHA_START_YEAR, end.year + 1)]


def near_chunks() -> list[tuple[str, str]]:
    end = _today()
    return [(f"{y}-01-01", f"{y}-12-31" if y < end.year else end.isoformat()) for y in range(NEAR_START_YEAR, end.year + 1)]


def load_repos() -> None:
    from google.cloud import bigquery

    c = bq.client()
    ds = bigquery.Dataset(f"{bq.project()}.{DATASET}")
    ds.location = "US"
    c.create_dataset(ds, exists_ok=True)
    frames = [pd.read_csv(CACHE / f"repos_{slug(e)}.csv", usecols=["repo"]).assign(ecosystem=e) for e in ECOSYSTEMS]
    df = pd.concat(frames)[["ecosystem", "repo"]]
    df["repo"] = df.repo.str.lower()
    buf = io.BytesIO(df.to_csv(index=False).encode("utf-8"))
    cfg = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.CSV, skip_leading_rows=1, write_disposition="WRITE_TRUNCATE",
        schema=[bigquery.SchemaField("ecosystem", "STRING"), bigquery.SchemaField("repo", "STRING")],
    )
    job = c.load_table_from_file(buf, f"{bq.project()}.{DATASET}.repos", job_config=cfg)
    job.result()
    print(f"loaded {job.output_rows} rows into {DATASET}.repos")


def gha_sql(start: str, end: str) -> str:
    return bq.sql_text("gha_active_devs", project=bq.project(), dataset=DATASET, start=start, end=end)


def near_sql(start: str, end: str) -> str:
    return bq.sql_text("near_deploys", start=start, end=end)


def dryrun() -> float:
    total = 0.0
    for s, e in gha_chunks():
        total += bq.dry_run(gha_sql(s, e), f"gha_active_devs {s}-{e}") / 1e9
    for s, e in near_chunks():
        total += bq.dry_run(near_sql(s, e), f"near_deploys {s}..{e}") / 1e9
    print(f"total planned: {total:.1f} GB")
    return total


def _check_overrun(name: str, est: int, billed: int) -> None:
    if est and billed > est * bq.OVERRUN and billed - est > 50e6:
        raise SystemExit(f"STOP: {name} billed {billed/1e9:.2f} GB vs estimate {est/1e9:.2f} GB (>10% over)")


def gha(approved_gb: float) -> None:
    """Each chunk runs once; a chunk whose output file exists is never re-run."""
    out = RAW / "gha"
    out.mkdir(parents=True, exist_ok=True)
    for s, e in gha_chunks():
        path = out / f"active_{s}_{e}.csv.gz"
        if path.exists():
            print(f"skip cached {path.name}")
            continue
        name = f"gha_active_devs {s}-{e}"
        df, est, billed = bq.run(gha_sql(s, e), name, approved_gb)
        df.to_csv(path, index=False, compression="gzip")
        print(f"{path.name}: {len(df)} rows", flush=True)
        _check_overrun(name, est, billed)


def near(approved_gb: float) -> None:
    """Each chunk runs once (smallest dry-run estimate first); cached chunks are never re-run."""
    out = RAW / "near"
    out.mkdir(parents=True, exist_ok=True)
    todo = [(s, e) for s, e in near_chunks() if not (out / f"deploys_{s}_{e}.csv").exists()]
    if todo:
        sizes = {(s, e): bq.dry_run(near_sql(s, e), f"near_deploys {s}..{e}", "dry run (ordering)") for s, e in todo}
        for s, e in sorted(todo, key=sizes.get):
            name = f"near_deploys {s}..{e}"
            df, est, billed = bq.run(near_sql(s, e), name, approved_gb)
            df.to_csv(out / f"deploys_{s}_{e}.csv", index=False)
            _check_overrun(name, est, billed)
    frames = [pd.read_csv(out / f"deploys_{s}_{e}.csv") for s, e in near_chunks()]
    m = pd.concat(frames)
    m["month"] = pd.to_datetime(m["month"]).dt.strftime("%Y-%m")
    m.sort_values("month").to_csv(CACHE / "near_deploys_monthly.csv", index=False)
    print(f"near_deploys_monthly.csv: {len(m)} months")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("step", nargs="?", default="all", choices=["load-repos", "dryrun", "gha", "near", "all"])
    ap.add_argument("--approved-gb", type=float, default=bq.ASK_LIMIT_GB)
    a = ap.parse_args()
    if a.step in ("load-repos", "all"):
        load_repos()
    if a.step == "dryrun":
        dryrun()
    if a.step in ("gha", "all"):
        gha(a.approved_gb)
    if a.step in ("near", "all"):
        near(a.approved_gb)


if __name__ == "__main__":
    main()
