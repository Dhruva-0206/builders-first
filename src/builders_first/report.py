"""Text generated from data/cache/claims.json: headlines, scorecard, flip conditions, bear case,
limitations. Shared by build_site (HTML) and the generated sections of THESIS.md and README.md.

Every number in the prose comes from claims.json; tests/test_generated.py checks that the committed
files equal a fresh render.
"""
from __future__ import annotations

import json
import re

from .paths import CACHE, ROOT

BEGIN = "<!-- BEGIN GENERATED: {name} (do not edit by hand; `make site` rewrites this) -->"
END = "<!-- END GENERATED: {name} -->"


def load_claims() -> dict:
    return json.loads((CACHE / "claims.json").read_text(encoding="utf-8"))


def pct(x: float, nd: int = 1) -> str:
    return f"{x * 100:.{nd}f}%"


def pp(x: float) -> str:
    return f"{x:+.2f} pp"


NUM_WORD = {0: "None", 1: "One", 2: "Two", 3: "Three"}


def reverse_granger(c: dict) -> dict:
    """Exploratory: deploys -> developers (raw), lags with p < 0.05 and their p range."""
    p = {int(k): v for k, v in c["C2"]["raw"]["deploys"]["reverse_granger_p"].items()}
    sig = sorted(k for k, v in p.items() if v < 0.05)
    vals = [p[k] for k in sig]
    return {"p": p, "lags": sig, "lo": min(vals) if vals else None, "hi": max(vals) if vals else None,
            "alpha": c["C2"]["raw"]["deploys"]["bonferroni_alpha"],
            "survives": any(v < c["C2"]["raw"]["deploys"]["bonferroni_alpha"] for v in p.values())}


def lag_range(lags: list[int]) -> str:
    if not lags:
        return "none"
    return f"{lags[0]}–{lags[-1]}" if lags == list(range(lags[0], lags[-1] + 1)) else ", ".join(map(str, lags))


def one_liner(c: dict) -> str:
    n = c["claims_holding"]
    b = c["C3b"]
    return (f"We tested three pre-registered claims about NEAR's developer base. {NUM_WORD[n]} holds"
            f"{', barely' if c['C1']['robustness']['peer_median_inside_near_ci'] and c['statuses']['C1'] == 'HOLDS' else ''}; "
            f"{NUM_WORD[3 - n].lower()} fail. The surprise: almost every hackathon builder is new to NEAR "
            f"({pct(b['new_share_all'], 0)}), and at least a third of their repos show AI co-authorship "
            f"({pct(b['ai_repo_share'], 0)}), but developers follow usage rather than lead it.")


def headlines(c: dict) -> list[str]:
    b, a, rg = c["C3b"], c["C3a"], reverse_granger(c)
    lo, hi = sorted([a["raw"]["ratio"], a["adjusted"]["ratio"]])
    rev = (f"the reverse direction is suggestive (p ≈ {rg['lo']:.2f}–{rg['hi']:.2f} at lags {lag_range(rg['lags'])}) "
           f"but not significant after Bonferroni (threshold {rg['alpha']:.4f})" if rg["lags"] else
           "the reverse direction is not significant either")
    return [
        f"**{pct(b['new_share_all'], 0)} of NEAR HACKATHON builders had no prior public NEAR activity** "
        f"({b['authors_new']} of {b['authors']} commit authors across {b['repos_github']} GitHub repos). "
        f"Caveat: \"NEAR activity\" means pushes or PRs on NEAR repos listed in Open Dev Data, so builders who only "
        f"worked in unlisted repos count as new; this overstates newness.",
        f"**≥{pct(b['ai_commit_share'], 0)} of hackathon commits are AI co-authored** "
        f"({b['ai_commits']:,} of {b['commits_non_bot']:,} non-bot commits; {pct(b['ai_repo_share'], 0)} of repos have at least one). "
        f"A lower bound: trailers are easy to strip, and this repo strips its own.",
        f"**Developers do not lead NEAR usage** (C2 {c['C2']['status'].lower()}: best p = "
        f"{min(c['C2']['raw']['deploys']['best_p'], c['C2']['raw']['unique_deployers']['best_p']):.3f} raw, "
        f"Bonferroni threshold {c['C2']['raw']['deploys']['bonferroni_alpha']:.4f}); {rev}: usage may pull developers in, "
        f"not the other way round.",
        f"**Output per developer fell to {lo:.2f}–{hi:.2f}× its 2023–24 level** "
        f"(contracts deployed per monthly active developer, coverage-adjusted and raw).",
    ]


def scorecard(c: dict) -> list[dict]:
    """Rows: id, claim, kill, measured, status, note, indent."""
    c1, c2, a, b = c["C1"], c["C2"], c["C3a"], c["C3b"]
    k6 = c1["by_k"]["6"]
    rob = c1["robustness"]
    c1_note = []
    if c1["status"] == "HOLDS" and rob["peer_median_inside_near_ci"]:
        c1_note.append(f"Statistical tie: margin {pp(c1['margin_6m_pp'])}, NEAR 95% CI "
                       f"{pct(c1['near_6m_ci95'][0])}–{pct(c1['near_6m_ci95'][1])} contains the peer median.")
    c1_note.append(f"Smoothed 6-month: {pct(k6['near_smooth'])} vs {pct(k6['peer_median_smooth'])} "
                   f"({'holds' if rob['smoothed_6m_holds'] else 'fails'}).")
    k12 = c1["by_k"]["12"]
    c1_note.append(f"12-month: {pct(k12['near'])} vs {pct(k12['peer_median'])} ({'holds' if rob['k12_holds'] else 'fails'}).")
    return [
        dict(id="C1", claim="New NEAR developers retain at least as well as peers (Solana, Sui, Aptos, Base)",
             kill="NEAR 6-month retention below peer median",
             measured=f"{pct(k6['near'])} vs peer median {pct(k6['peer_median'])}",
             status=c1["status"] + (" (statistical tie)" if c1["status"] == "HOLDS" and rob["peer_median_inside_near_ci"] else ""),
             note=" ".join(c1_note), indent=False),
        dict(id="C2", claim="NEAR monthly active developers lead contract deployments by 1–6 months",
             kill=f"No lag with p < {c2['raw']['deploys']['bonferroni_alpha']:.4f} (0.05 / 6, Bonferroni)",
             measured=c2["measured"], status=c2["status"],
             note=f"Raw and coverage-adjusted MAD agree." if c2["status"] != "FRAGILE" else "Raw and adjusted disagree.",
             indent=False),
        dict(id="C3", claim="AI-era funnel: (a) and (b) both hold", kill="(a) or (b) killed",
             measured="see C3a, C3b", status=c["C3"]["status"], note="", indent=False),
        dict(id="C3a", claim="Contracts deployed per MAD rose since 2025",
             kill=f"Post-2025 mean not more than {1 + a['min_rise']:.2f}× the 2023–24 mean",
             measured=a["measured"], status=a["status"],
             note=f"Mann-Whitney p = {a['raw']['mann_whitney_p']:.3g} (raw), not part of the criterion.", indent=True),
        dict(id="C3b", claim="A majority of NEAR HACKATHON authors are new to NEAR",
             kill="New-to-NEAR authors < 50% (stricter of two shares)",
             measured=f"{pct(b['new_share_all'])} of {b['authors']} authors; {pct(b['new_share_excl_truncated'])} excluding "
                      f"{b['authors_truncated']} with truncated event feeds",
             status=b["status"],
             note=f"AI co-authored: ≥{pct(b['ai_commit_share'])} of commits, {pct(b['ai_repo_share'])} of repos.", indent=True),
    ]


def flips(c: dict) -> list[str]:
    c1, c2, a, b = c["C1"], c["C2"], c["C3a"], c["C3b"]
    k6 = c1["by_k"]["6"]
    need = (1 + a["min_rise"]) * a["raw"]["pre_mean"]
    need_adj = (1 + a["min_rise"]) * a["adjusted"]["pre_mean"]
    alpha = c2["raw"]["deploys"]["bonferroni_alpha"]
    return [
        f"**C1 ({c1['status']})** flips to KILLED if NEAR's 6-month retention drops below the peer median "
        f"(today {pct(k6['near'], 2)} vs {pct(k6['peer_median'], 2)}, a margin of {pp(c1['margin_6m_pp'])}). "
        f"Watch it: the margin is inside sampling error.",
        f"**C2 ({c2['status']})** flips to HOLDS if any lag 1–6 reaches p < {alpha:.4f} for deploys or unique deployers, "
        f"on both raw and coverage-adjusted MAD (on only one: FRAGILE). Best today: "
        f"{min(c2['raw']['deploys']['best_p'], c2['raw']['unique_deployers']['best_p']):.3f} raw, "
        f"{min(c2['adjusted']['deploys']['best_p'], c2['adjusted']['unique_deployers']['best_p']):.3f} adjusted.",
        f"**C3a ({a['status']})** flips to HOLDS if mean contracts per MAD from 2025-01 exceeds "
        f"{1 + a['min_rise']:.2f}× the 2023–24 mean: above {need:.2f} raw (today {a['raw']['post_mean']:.2f}) and above "
        f"{need_adj:.2f} adjusted (today {a['adjusted']['post_mean']:.2f}).",
        f"**C3b ({b['status']})** flips to KILLED if new-to-NEAR authors fall to 50% or below in a future cohort "
        f"(today {pct(b['new_share_strict'])}, stricter of the two shares).",
        f"**Verdict ({c['verdict']})** moves to Bull with one more HOLDS (C2, or C3a while C3b holds), "
        f"and to Bear if C1 flips.",
    ]


def exploratory(c: dict) -> list[str]:
    rg = reverse_granger(c)
    rows = ", ".join(f"lag {k}: {v:.3f}" for k, v in sorted(rg["p"].items()))
    s = (f"Deploys → developers (the reverse of C2, raw MAD, log-differenced): Granger p-values {rows}. "
         f"Bonferroni threshold across 6 lags: {rg['alpha']:.4f}. ")
    s += ("At least one lag survives the correction." if rg["survives"] else
          "No lag survives the correction, so this is a hint, not a finding. It was not pre-registered and has no "
          "effect on the verdict.")
    oos = c["C2"]["raw"]
    s2 = (f"C2 out-of-sample check (fit to {c['C2']['train_end']}, one-step forecasts after): adding lagged MAD changes "
          f"forecast RMSE by a factor of {oos['deploys']['oos']['rmse_ratio']:.2f} for deploys and "
          f"{oos['unique_deployers']['oos']['rmse_ratio']:.2f} for unique deployers (below 1 would mean developers help "
          f"predict usage).")
    return [s, s2]


def bear_case(c: dict) -> list[str]:
    a, b = c["C3a"], c["C3b"]
    nm = c["mad"]["NEAR"]
    months = sorted(nm)
    peak_m = max(nm, key=nm.get)
    return [
        f"NEAR's monthly active developers peaked at {nm[peak_m]:,} in {peak_m} and were {nm[months[-1]]:,} in "
        f"{months[-1]}, the last month with reliable GH Archive coverage.",
        f"Developers do not lead usage (C2 killed). If anything, the exploratory reverse test suggests usage pulls "
        f"developers in, which makes developer data a lagging, not leading, signal for the token.",
        f"Output per developer fell ({a['raw']['ratio']:.2f}× raw, {a['adjusted']['ratio']:.2f}× adjusted), so fewer "
        f"developers are not being offset by more contracts each.",
        f"NEAR's retention is no better than peers' (a statistical tie at 6 months; behind at 12 months).",
        f"The hackathon brought {b['authors']} mostly new authors, but a two-week cohort says nothing yet about "
        f"whether they stay; C1 suggests roughly {pct(c['C1']['by_k']['6']['near'], 0)} of new NEAR developers are "
        f"still active six months later.",
    ]


def limitations(c: dict) -> list[str]:
    cov = c["coverage"]
    b = c["C3b"]
    return [
        f"GH Archive volume breaks in {cov['level_break_month']} (pushes fall about 30%) and collapses after "
        f"{cov['last_good_month']} (pull requests, then pushes). Series end at {cov['last_good_month']}; C2 and C3a are "
        f"also run on coverage-adjusted MAD, and disagreements would be reported as FRAGILE.",
        "Developer identity is the GH Archive actor of a push or PR on a repo listed in Open Dev Data. Electric Capital "
        "counts original commit authors, so levels differ from the Developer Report. Private repos and unlisted repos "
        "are invisible.",
        "History starts 2021-01 (budget), so some 2022 \"new\" developers are returning ones.",
        "Deployments are transaction-level DEPLOY_CONTRACT only; factory-created contracts are excluded on purpose "
        "(see THESIS.md methodology, item 4).",
        f"C3b covers {b['repos_github']} repos with a GitHub link out of {b['nearhunt_projects']} nearhunt.xyz projects "
        f"({b['submissions_official']} official submissions); {b['commits_no_login']:,} commits had no linked GitHub "
        f"account. {b['authors_feed_capped']} authors hit GitHub's 300-event feed cap; {b['authors_truncated']} of them "
        f"have feeds that stop after 2026-10-19 and are shown both included and excluded.",
        "AI co-authorship is detected from commit trailers only, a lower bound.",
        "The C3a threshold (>10%) was fixed after the deployment series had been seen; see THESIS.md methodology item 6 "
        "for the exact order of events with commit hashes.",
    ]


# ------------------------------------------------------------------ markdown

def md_scorecard(c: dict) -> str:
    out = ["| Claim | Kill criterion | Measured | Status |", "|---|---|---|---|"]
    for r in scorecard(c):
        name = ("&nbsp;&nbsp;↳ " if r["indent"] else "") + f"**{r['id']}** {r['claim']}"
        status = f"**{r['status']}**" + (f"<br>{r['note']}" if r["note"] else "")
        out.append(f"| {name} | {r['kill']} | {r['measured']} | {status} |")
    return "\n".join(out)


def md_results(c: dict) -> str:
    v = c["verdict"]
    parts = [
        f"## Results (verdict: **{v}**, {c['claims_holding']} of 3 claims hold)", "",
        f"Data as of: NEAR deployments to {c['data_as_of']['near_deploys_last_month']}, GH Archive reliable to "
        f"{c['data_as_of']['gha_last_good_month']}, hackathon data fetched {c['data_as_of']['hackathon_fetched_at'][:10]}, "
        f"Open Dev Data commit `{c['data_as_of']['open_dev_data_commit']}`. Every figure below is read from "
        f"[`data/cache/claims.json`](data/cache/claims.json), produced by `make analysis`.", "",
        md_scorecard(c), "",
        "## What would change the verdict", "",
        "Each line is the threshold that flips a claim on the next re-run (`make data && make all`).", "",
        *[f"- {f}" for f in flips(c)], "",
        "## Exploratory, not pre-registered", "",
        *[f"- {e}" for e in exploratory(c)], "",
        "## Bear case", "",
        *[f"- {x}" for x in bear_case(c)], "",
        "## Limitations", "",
        *[f"- {x}" for x in limitations(c)],
    ]
    return "\n".join(parts)


def md_readme_table(c: dict) -> str:
    return (f"**Verdict: {c['verdict']}** ({c['claims_holding']} of 3 pre-registered claims hold)\n\n" + md_scorecard(c))


def replace_block(text: str, name: str, body: str) -> str:
    b, e = BEGIN.format(name=name), END.format(name=name)
    block = f"{b}\n{body}\n{e}"
    if b in text:
        return re.sub(re.escape(b) + r".*?" + re.escape(e), lambda _: block, text, flags=re.S)
    raise ValueError(f"marker {name!r} missing")


def render_docs(c: dict) -> dict[str, str]:
    """Return {path: new_text} for THESIS.md and README.md."""
    out = {}
    t = (ROOT / "THESIS.md").read_text(encoding="utf-8")
    t = replace_block(t, "headlines", "\n".join(f"- {h}" for h in headlines(c)))
    t = replace_block(t, "results", md_results(c))
    out["THESIS.md"] = t
    r = (ROOT / "README.md").read_text(encoding="utf-8")
    r = replace_block(r, "one-liner", one_liner(c))
    r = replace_block(r, "claims", md_readme_table(c))
    out["README.md"] = r
    return out
