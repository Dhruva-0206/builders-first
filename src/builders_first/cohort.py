"""Developer activity metrics: monthly active developers, new developers, cohort retention.

Input frame `act`: columns ecosystem, month ('YYYY-MM'), dev (any hashable id), one row per
(ecosystem, month, dev) with >=1 qualifying event.
"""
from __future__ import annotations

import pandas as pd


def month_index(m: pd.Series) -> pd.Series:
    """'YYYY-MM' -> integer months since year 0 (so consecutive months differ by 1)."""
    y = m.str.slice(0, 4).astype(int)
    mo = m.str.slice(5, 7).astype(int)
    return y * 12 + (mo - 1)


def index_month(i: int) -> str:
    return f"{i // 12:04d}-{i % 12 + 1:02d}"


def monthly_active(act: pd.DataFrame) -> pd.DataFrame:
    """ecosystem, month, mad, new_devs."""
    a = act.drop_duplicates(["ecosystem", "month", "dev"])
    mad = a.groupby(["ecosystem", "month"]).dev.nunique().rename("mad")
    first = a.groupby(["ecosystem", "dev"]).month.min().reset_index()
    new = first.groupby(["ecosystem", "month"]).dev.nunique().rename("new_devs")
    out = pd.concat([mad, new], axis=1).fillna(0).astype(int).reset_index()
    return out.sort_values(["ecosystem", "month"]).reset_index(drop=True)


def retention(act: pd.DataFrame, ks=(3, 6, 12), cohort_start: str = "2022-01", last_month: str | None = None) -> pd.DataFrame:
    """Pooled retention per ecosystem and k.

    A developer's cohort is their first active month in the ecosystem. Retained at k if active in
    cohort+k (strict) or in any of cohort+k-1..cohort+k+1 (smoothed). Only cohorts with full
    follow-up (cohort+k+1 <= last_month) are included, so strict and smoothed use the same cohorts.
    Returns ecosystem, k, cohorts, cohort_devs, retained, retention, retained_smooth, retention_smooth.
    """
    a = act.drop_duplicates(["ecosystem", "month", "dev"]).copy()
    a["mi"] = month_index(a.month)
    last = int(month_index(pd.Series([last_month]))[0]) if last_month else int(a.mi.max())
    start = int(month_index(pd.Series([cohort_start]))[0])
    first = a.groupby(["ecosystem", "dev"]).mi.min().rename("ci").reset_index()
    a = a.merge(first, on=["ecosystem", "dev"])
    a["age"] = a.mi - a.ci
    rows = []
    for eco, g in a.groupby("ecosystem"):
        ages = g.groupby("dev").age.apply(set)
        ci = first[first.ecosystem == eco].set_index("dev").ci
        for k in ks:
            eligible = ci[(ci >= start) & (ci + k + 1 <= last)]
            n = len(eligible)
            if n == 0:
                rows.append(dict(ecosystem=eco, k=k, cohorts=0, cohort_devs=0, retained=0, retention=float("nan"),
                                 retained_smooth=0, retention_smooth=float("nan")))
                continue
            s = ages.loc[eligible.index]
            strict = int(s.map(lambda x: k in x).sum())
            smooth = int(s.map(lambda x: bool(x & {k - 1, k, k + 1})).sum())
            rows.append(dict(ecosystem=eco, k=k, cohorts=int(eligible.nunique()), cohort_devs=n, retained=strict,
                             retention=strict / n, retained_smooth=smooth, retention_smooth=smooth / n))
    return pd.DataFrame(rows)


def retention_curve(act: pd.DataFrame, max_k: int = 12, cohort_start: str = "2022-01", last_month: str | None = None) -> pd.DataFrame:
    """Strict pooled retention for every k in 1..max_k (for charts)."""
    return retention(act, ks=range(1, max_k + 1), cohort_start=cohort_start, last_month=last_month)[
        ["ecosystem", "k", "cohort_devs", "retention"]
    ]
