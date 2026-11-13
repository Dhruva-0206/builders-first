"""Compute claims C1-C3 and the verdict from data/cache only (no network). Writes data/cache/claims.json.

Status values: HOLDS, KILLED, FRAGILE (raw and coverage-adjusted results disagree; does not count).
Verdict: Bull if >=2 claims HOLD, Neutral if 1, Bear if 0.
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from . import stats
from .cohort import monthly_active, retention, retention_curve
from .ingest_ecosystems import ECOSYSTEMS, PEERS
from .paths import CACHE

COHORT_START = "2022-01"
C2_START = "2021-01"
C2_MAX_LAG = 6
C2_ALPHA = 0.05
C2_TRAIN_END = "2024-12"
C3A_PRE = ("2023-01", "2024-12")
C3A_POST_START = "2025-01"
C3A_MIN_RISE = 0.10
HACKATHON_START = "2026-10-19"
PRIOR_MONTHLY_END = "2026-09"     # October 2026 is resolved with the daily tables (near_prior_oct.csv)
AI_GROUPS = {"claude": "Claude", "anthropic": "Claude", "codex": "Codex", "openai": "Codex",
             "copilot": "Copilot", "cursor": "Cursor", "devin": "Other", "gemini": "Other", "aider": "Other"}


def _f(x, nd=4):
    return None if x is None or (isinstance(x, float) and np.isnan(x)) else round(float(x), nd)


def _status(raw: bool, adj: bool | None = None) -> str:
    if adj is None or raw == adj:
        return "HOLDS" if raw else "KILLED"
    return "FRAGILE"


def load():
    act = pd.read_csv(CACHE / "activity.csv.gz", dtype=str)
    vol = pd.read_csv(CACHE / "gha_pushpr_volume.csv", dtype={"month": str})
    dep = pd.read_csv(CACHE / "near_deploys_monthly.csv", dtype={"month": str})
    return act, vol, dep


def coverage(vol: pd.DataFrame) -> dict:
    lg = stats.last_good_month(vol)
    t = stats.coverage_table(vol)
    c = stats.coverage_factor(vol, lg)
    return {
        "threshold": stats.COVERAGE_THRESHOLD,
        "window_months": stats.COVERAGE_WINDOW,
        "last_good_month": lg,
        "level_break_month": stats.coverage_break(vol, lg),
        "series": [{"month": r.month, "push_events": int(r.push_events), "pr_events": int(r.pr_events),
                    "push_ratio": _f(r.push_ratio), "pr_ratio": _f(r.pr_ratio), "good": bool(r.good),
                    "factor": _f(c.get(r.month, 1.0))} for r in t.itertuples()],
    }, lg, c


def c1(act: pd.DataFrame, last_good: str) -> dict:
    a = act[act.month <= last_good]
    r = retention(a, ks=(3, 6, 12), cohort_start=COHORT_START, last_month=last_good)
    curve = retention_curve(a, max_k=12, cohort_start=COHORT_START, last_month=last_good)
    out = {"by_k": {}}
    for k in (3, 6, 12):
        rk = r[r.k == k].set_index("ecosystem")
        out["by_k"][str(k)] = {
            "near": _f(rk.loc["NEAR", "retention"]),
            "near_smooth": _f(rk.loc["NEAR", "retention_smooth"]),
            "peer_median": _f(rk.loc[PEERS, "retention"].median()),
            "peer_median_smooth": _f(rk.loc[PEERS, "retention_smooth"].median()),
            "ecosystems": {e: {"retention": _f(rk.loc[e, "retention"]), "retention_smooth": _f(rk.loc[e, "retention_smooth"]),
                               "cohort_devs": int(rk.loc[e, "cohort_devs"])} for e in ECOSYSTEMS},
        }
    k6 = out["by_k"]["6"]
    out["holds"] = bool(k6["near"] >= k6["peer_median"])
    n6 = r[(r.k == 6) & (r.ecosystem == "NEAR")].iloc[0]
    lo, hi = stats.wilson_ci(int(n6.retained), int(n6.cohort_devs))
    out["near_6m_ci95"] = [_f(lo), _f(hi)]
    out["margin_6m_pp"] = _f((k6["near"] - k6["peer_median"]) * 100, 2)
    out["robustness"] = {
        "smoothed_6m_holds": bool(k6["near_smooth"] >= k6["peer_median_smooth"]),
        "k3_holds": bool(out["by_k"]["3"]["near"] >= out["by_k"]["3"]["peer_median"]),
        "k12_holds": bool(out["by_k"]["12"]["near"] >= out["by_k"]["12"]["peer_median"]),
        "peer_median_inside_near_ci": bool(lo <= k6["peer_median"] <= hi),
    }
    out["status"] = _status(out["holds"])
    out["measured"] = f"NEAR 6-month retention {k6['near']:.1%} vs peer median {k6['peer_median']:.1%}"
    out["curve"] = {e: [_f(v) for v in curve[curve.ecosystem == e].sort_values("k").retention] for e in ECOSYSTEMS}
    out["cohort_start"] = COHORT_START
    out["followup_end"] = last_good
    return out


def _c2_one(y: pd.Series, x: pd.Series) -> dict:
    dy, dx = stats.dlog(y), stats.dlog(x)
    p = stats.granger_pvalues(dy, dx, C2_MAX_LAG)
    rev = stats.granger_pvalues(dx, dy, C2_MAX_LAG)
    alpha = C2_ALPHA / C2_MAX_LAG
    best = min(p, key=p.get)
    return {
        "adf_p_y": _f(stats.adf_pvalue(dy)), "adf_p_x": _f(stats.adf_pvalue(dx)),
        "granger_p": {str(k): _f(v, 6) for k, v in p.items()},
        "reverse_granger_p": {str(k): _f(v, 6) for k, v in rev.items()},
        "ccf": {str(k): _f(v) for k, v in stats.cross_correlation(dx, dy, C2_MAX_LAG).items()},
        "bonferroni_alpha": _f(alpha, 6),
        "significant_lags": [k for k, v in p.items() if v < alpha],
        "best_lag": best, "best_p": _f(p[best], 6),
        "oos": {k: _f(v) if isinstance(v, float) else v for k, v in stats.out_of_sample(dy, dx, best, C2_TRAIN_END).items()},
        "n_months": int(len(dy)),
    }


def c2(mad: pd.Series, mad_adj: pd.Series, dep: pd.DataFrame, last_good: str) -> dict:
    d = dep[(dep.month >= C2_START) & (dep.month <= last_good)].set_index("month")
    out = {"window": [C2_START, last_good], "max_lag": C2_MAX_LAG, "alpha": C2_ALPHA, "train_end": C2_TRAIN_END}
    for label, x in (("raw", mad), ("adjusted", mad_adj)):
        xs = x.reindex(d.index)
        out[label] = {s: _c2_one(d[s], xs) for s in ("deploys", "unique_deployers")}
        out[label]["holds"] = any(out[label][s]["significant_lags"] for s in ("deploys", "unique_deployers"))
    out["status"] = _status(out["raw"]["holds"], out["adjusted"]["holds"])
    out["holds"] = out["status"] == "HOLDS"
    r = out["raw"]
    out["measured"] = (f"min Granger p {min(r['deploys']['best_p'], r['unique_deployers']['best_p']):.3g} raw / "
                       f"{min(out['adjusted']['deploys']['best_p'], out['adjusted']['unique_deployers']['best_p']):.3g} adjusted "
                       f"(Bonferroni threshold {C2_ALPHA / C2_MAX_LAG:.4f})")
    return out


def c3a(mad: pd.Series, mad_adj: pd.Series, dep: pd.DataFrame, last_good: str) -> dict:
    d = dep[(dep.month >= C3A_PRE[0]) & (dep.month <= last_good)].set_index("month")
    out = {"pre": list(C3A_PRE), "post": [C3A_POST_START, last_good], "min_rise": C3A_MIN_RISE, "series": {}}
    for label, x in (("raw", mad), ("adjusted", mad_adj)):
        opd = d.deploys / x.reindex(d.index)
        upd = d.unique_deployers / x.reindex(d.index)
        pre, post = opd[opd.index <= C3A_PRE[1]], opd[opd.index >= C3A_POST_START]
        ratio = post.mean() / pre.mean()
        out[label] = {
            "pre_mean": _f(pre.mean()), "post_mean": _f(post.mean()), "ratio": _f(ratio),
            "holds": bool(ratio > 1 + C3A_MIN_RISE),
            "mann_whitney_p": _f(stats.mann_whitney_p(pre, post)),
            "deployers_per_mad_ratio": _f(upd[upd.index >= C3A_POST_START].mean() / upd[upd.index <= C3A_PRE[1]].mean()),
        }
        out["series"][label] = {m: _f(v) for m, v in opd.items()}
    out["status"] = _status(out["raw"]["holds"], out["adjusted"]["holds"])
    out["measured"] = (f"contracts per MAD {out['raw']['ratio']:.2f}x pre-period (raw), "
                       f"{out['adjusted']['ratio']:.2f}x (coverage-adjusted)")
    return out


def c3b(act: pd.DataFrame) -> dict:
    commits = pd.read_csv(CACHE / "hackathon_commits.csv", dtype=str, keep_default_na=False)
    authors = pd.read_csv(CACHE / "hackathon_authors.csv", dtype={"dev": str})
    octp = set(pd.read_csv(CACHE / "near_prior_oct.csv", dtype=str).dev)
    near_prior = set(act[(act.ecosystem == "NEAR") & (act.month <= PRIOR_MONTHLY_END)].dev) | octp

    a = authors.copy()
    a["prior_gha"] = a.dev.isin(near_prior)
    a["prior_feed"] = a.feed_prior_near.astype(bool)
    a["new"] = ~(a.prior_gha | a.prior_feed)
    a["truncated"] = a.feed_capped.astype(bool) & ~a.feed_reaches_before.astype(bool)
    share_all = a.new.mean()
    b = a[~a.truncated]
    share_excl = b.new.mean()
    strict = min(share_all, share_excl)

    nb = commits[commits.is_bot != "True"]
    ai = nb[nb.ai_trailer == "True"]
    groups = ai.ai_tool.map(AI_GROUPS).value_counts()
    repos_any = nb.groupby("repo").ai_trailer.apply(lambda s: (s == "True").any())
    meta = json.loads((CACHE / "hackathon_meta.json").read_text(encoding="utf-8"))
    repos = pd.read_csv(CACHE / "hackathon_repos.csv")
    out = {
        "submissions_official": meta["official_total_reported"],
        "nearhunt_projects": meta["nearhunt_rows"],
        "repos_github": int(len(repos)),
        "repos_without_github": meta["nearhunt_without_github_repo"],
        "commits_total": int(len(commits)),
        "commits_non_bot": int(len(nb)),
        "commits_no_login": int((nb.author_dev == "").sum()),
        "authors": int(len(a)),
        "authors_new": int(a.new.sum()),
        "authors_prior_gha": int(a.prior_gha.sum()),
        "authors_prior_feed_only": int((a.prior_feed & ~a.prior_gha).sum()),
        "authors_feed_capped": int(a.feed_capped.astype(bool).sum()),
        "authors_truncated": int(a.truncated.sum()),
        "new_share_all": _f(share_all),
        "new_share_excl_truncated": _f(share_excl),
        "new_share_strict": _f(strict),
        "ai_commit_share": _f(len(ai) / len(nb)),
        "ai_commits": int(len(ai)),
        "ai_repo_share": _f(repos_any.mean()),
        "ai_repos": int(repos_any.sum()),
        "ai_by_tool": {g: int(groups.get(g, 0)) for g in ("Claude", "Codex", "Copilot", "Cursor", "Other")},
        "holds": bool(strict > 0.5),
    }
    out["status"] = _status(out["holds"])
    return out


def verdict(statuses: list[str]) -> str:
    n = sum(s == "HOLDS" for s in statuses)
    return "Bull" if n >= 2 else ("Neutral" if n == 1 else "Bear")


def compute() -> dict:
    act, vol, dep = load()
    cov, lg, factor = coverage(vol)
    mad_tbl = monthly_active(act)
    near = mad_tbl[mad_tbl.ecosystem == "NEAR"].set_index("month").mad
    near = near[near.index <= lg]
    near_adj = near / factor.reindex(near.index).fillna(1.0)

    r1 = c1(act, lg)
    r2 = c2(near, near_adj, dep, lg)
    r3a = c3a(near, near_adj, dep, lg)
    r3b = c3b(act)
    if r3b["status"] == "KILLED" or r3a["status"] == "KILLED":
        s3 = "KILLED"
    elif r3a["status"] == "FRAGILE":
        s3 = "FRAGILE"
    else:
        s3 = "HOLDS"
    statuses = [r1["status"], r2["status"], s3]

    eco_meta = json.loads((CACHE / "ecosystems_meta.json").read_text(encoding="utf-8"))
    hk = json.loads((CACHE / "hackathon_meta.json").read_text(encoding="utf-8"))
    mad_series = {e: {r.month: int(r.mad) for r in mad_tbl[mad_tbl.ecosystem == e].itertuples() if r.month <= lg}
                  for e in ECOSYSTEMS}
    return {
        "verdict": verdict(statuses),
        "claims_holding": sum(s == "HOLDS" for s in statuses),
        "claims_fragile": sum(s == "FRAGILE" for s in statuses),
        "statuses": {"C1": statuses[0], "C2": statuses[1], "C3": statuses[2]},
        "data_as_of": {"near_deploys_last_month": dep.month.max(), "hackathon_fetched_at": hk["fetched_at"],
                       "open_dev_data_commit": eco_meta["commit"][:7], "gha_last_good_month": lg},
        "ecosystem_repos": {e: v["repos"] for e, v in eco_meta["ecosystems"].items()},
        "coverage": cov,
        "mad": mad_series,
        "near_mad_adjusted": {m: _f(v, 1) for m, v in near_adj.items()},
        "near_deploys": {r.month: {"deploys": int(r.deploys), "unique_deployers": int(r.unique_deployers)}
                         for r in dep[dep.month <= lg].itertuples()},
        "C1": r1, "C2": r2, "C3a": r3a, "C3b": r3b, "C3": {"status": s3},
    }


def main() -> None:
    res = compute()
    (CACHE / "claims.json").write_text(json.dumps(res, indent=1, sort_keys=False) + "\n", encoding="utf-8", newline="\n")
    print(f"verdict={res['verdict']} statuses={res['statuses']}")
    print(" C1:", res["C1"]["measured"])
    print(" C2:", res["C2"]["measured"])
    print(" C3a:", res["C3a"]["measured"])
    b = res["C3b"]
    print(f" C3b: new-to-NEAR {b['new_share_all']:.1%} all / {b['new_share_excl_truncated']:.1%} excl. truncated; "
          f"AI commits {b['ai_commit_share']:.1%}, repos {b['ai_repo_share']:.1%}")


if __name__ == "__main__":
    main()
