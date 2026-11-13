"""Text generated from data/cache/claims.json: headlines, scorecard, flip conditions, bear case,
limitations. Shared by build_site (HTML) and the generated sections of THESIS.md and README.md.

Every number in the prose comes from claims.json; tests/test_generated.py checks that the committed
files equal a fresh render. Numbers are formatted only through the helpers below, one helper per
kind of quantity, so the same figure reads identically everywhere.
"""
from __future__ import annotations

import json
import re

from .paths import CACHE, ROOT

BEGIN = "<!-- BEGIN GENERATED: {name} (do not edit by hand; `make site` rewrites this) -->"
END = "<!-- END GENERATED: {name} -->"

# Commit hashes that prove the order of pre-registration (git facts, not data).
PREREG = ("I pre-registered the three claims: I wrote each one down with the result that would disprove it and "
          "committed them in `333ea0c` before pulling any data. One threshold came later. I added C3a's >10% rule in "
          "`4d4fc58`, after I had seen the deployment series (THESIS.md, Methodology changes, item 6).")
VERDICT_RULE = ("The verdict counts the three top-level claims C1 to C3: Bull if at least two hold, Neutral if one, "
                "Bear if none. A claim marked FRAGILE (raw and coverage-adjusted results disagree) does not count. C3 "
                "holds only if both C3a and C3b hold, so C3b holding on its own does not add to the count.")


def load_claims() -> dict:
    return json.loads((CACHE / "claims.json").read_text(encoding="utf-8"))


# ------------------------------------------------------------------ formatters

def pct(x: float) -> str:
    """Shares (new-to-NEAR, AI co-authorship, ...): one decimal."""
    return f"{x * 100:.1f}%"


def ret(x: float) -> str:
    """Retention rates (C1): two decimals, because the 6-month margin is 0.01 pp."""
    return f"{x * 100:.2f}%"


def pp(x: float) -> str:
    return f"{x:+.2f} pp"


def times(x: float) -> str:
    return f"{x:.2f}×"


def times_range(a: float, b: float) -> str:
    lo, hi = sorted([a, b])
    return f"{lo:.2f} to {hi:.2f}×"


def pval(x: float) -> str:
    return f"{x:.3f}"


def alpha_(x: float) -> str:
    return f"{x:.4f}"


def frac(n: int, d: int) -> str:
    return f"{n:,}/{d:,}"


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


def c2_best(c: dict, label: str) -> float:
    return min(c["C2"][label]["deploys"]["best_p"], c["C2"][label]["unique_deployers"]["best_p"])


def ai_repos(b: dict) -> str:
    return (f"{pct(b['ai_repo_share'])} of repos ({frac(b['ai_repos'], b['ai_repo_denominator'])} repos with at least "
            f"one non-bot commit)")


def one_liner(c: dict) -> str:
    n = c["claims_holding"]
    b = c["C3b"]
    return (f"I tested three pre-registered claims about NEAR's developer base. {NUM_WORD[n]} holds"
            f"{', barely' if c['C1']['robustness']['peer_median_inside_near_ci'] and c['statuses']['C1'] == 'HOLDS' else ''}; "
            f"{NUM_WORD[3 - n].lower()} fail. The surprise: almost every hackathon builder is new to NEAR "
            f"({pct(b['new_share_all'])}), and at least a third of their repos show AI co-authorship "
            f"({pct(b['ai_repo_share'])}), but developers do not lead onchain usage; the reverse direction is suggestive "
            f"but not significant.")


def headlines(c: dict) -> list[str]:
    b, a, rg = c["C3b"], c["C3a"], reverse_granger(c)
    al = alpha_(c["C2"]["raw"]["deploys"]["bonferroni_alpha"])
    rev = (f"The reverse direction, deployments leading developers, is suggestive (p = {pval(rg['lo'])} to "
           f"{pval(rg['hi'])} at lags {lag_range(rg['lags'])}) but not significant, so I treat it as exploratory."
           if rg["lags"] else "The reverse direction is not significant either.")
    return [
        f"{pct(b['new_share_all'])} ({frac(b['authors_new'], b['authors'])}) of NEAR HACKATHON commit authors had no "
        f"prior public activity in NEAR repos tracked by Open Dev Data, an upper bound on newness. Work in repos the "
        f"taxonomy does not list is invisible to this check.",
        f"At least {pct(b['ai_commit_share'])} of hackathon commits are AI co-authored "
        f"({frac(b['ai_commits'], b['commits_non_bot'])} non-bot commits), and {ai_repos(b)} contain at least one such "
        f"commit. Both are lower bounds: trailers are easy to strip, and this repo strips its own.",
        f"Developers do not lead onchain usage. A Granger test asks whether past developer counts help predict "
        f"deployments; the best result was p = {pval(c2_best(c, 'raw'))}, against a Bonferroni threshold of {al} "
        f"(0.05 split across the 6 lags tested). {rev}",
        f"Output per developer fell to {times_range(a['raw']['ratio'], a['adjusted']['ratio'])} its 2023–24 level, "
        f"measured as contracts deployed per monthly active developer (MAD: a GitHub account that pushed code or opened "
        f"a pull request in an ecosystem repo that month).",
    ]


def implication(c: dict) -> list[str]:
    """Investment implication: reads only claims.json."""
    c1, a, b = c["C1"], c["C3a"], c["C3b"]
    k6 = c1["by_k"]["6"]
    lo, hi = sorted([a["raw"]["ratio"], a["adjusted"]["ratio"]])
    need = (1 + a["min_rise"]) * a["raw"]["pre_mean"]
    return [
        f"Developer data alone does not support a bull case for NEAR today. New developers stay only at par with "
        f"peers (6-month retention {ret(k6['near'])} vs {ret(k6['peer_median'])}), developers do not lead onchain usage "
        f"(C2 {c['C2']['status'].lower()}), and output per developer fell to {times_range(lo, hi)} its 2023–24 level.",
        "A bull case would have to rest on usage-side evidence, such as NEAR Intents volume and fees, which I did not "
        "measure here. Developer momentum does not carry it.",
        f"The one leading indicator worth watching is the AI-assisted newcomer wave: {pct(b['new_share_all'])} of "
        f"hackathon commit authors ({frac(b['authors_new'], b['authors'])}) were new to tracked NEAR repos, and at least "
        f"{pct(b['ai_repo_share'])} of repos ({frac(b['ai_repos'], b['ai_repo_denominator'])}) show AI co-authorship. "
        f"If those builders ship to mainnet and contracts per developer rises above {need:.2f} (the C3a flip threshold; "
        f"{a['raw']['post_mean']:.2f} raw and {a['adjusted']['post_mean']:.2f} adjusted today), the verdict moves toward bullish.",
        "This is not investment advice.",
    ]


def method_brief(c: dict) -> list[str]:
    """Plain-language method summary with each term defined once."""
    cov, al = c["coverage"], alpha_(c["C2"]["raw"]["deploys"]["bonferroni_alpha"])
    return [
        "Pre-registration: I wrote down each claim and the result that would disprove it, and committed them before "
        "pulling any data.",
        "Developer activity comes from GH Archive, a public record of GitHub events. A monthly active developer (MAD) "
        "is a GitHub account that pushed code or opened a pull request in one of an ecosystem's repos that month. The "
        "repo lists come from Open Dev Data by Electric Capital.",
        f"C1 compares the share of new developers still active 3, 6 and 12 months later, NEAR against the median of "
        f"Solana, Sui, Aptos and Base, for monthly cohorts from {c['C1']['cohort_start']}.",
        f"C2 uses Granger tests, which ask whether past values of one series improve forecasts of another, on monthly "
        f"changes in NEAR MAD and contract deployments at lags 1 to 6. With six tests, a Bonferroni correction (dividing "
        f"the 0.05 significance level by the number of tests) sets the bar at p < {al}.",
        "C3a divides monthly contract deployments by MAD. C3b checks every hackathon commit author for earlier NEAR "
        "activity in GH Archive and in their GitHub event feed, and counts commits that carry AI co-author trailers.",
        f"GH Archive's own volume breaks in {cov['level_break_month']} and collapses after {cov['last_good_month']}. A "
        f"coded rule stops the series at {cov['last_good_month']}, and I re-ran C2 and C3a on coverage-adjusted MAD.",
    ]


def chart_titles(c: dict) -> dict[str, tuple[str, str]]:
    """Per chart: (takeaway title stating what the chart shows, neutral description)."""
    c1, a, b, cov = c["C1"], c["C3a"], c["C3b"], c["coverage"]
    k6 = c1["by_k"]["6"]
    nm = c["mad"]["NEAR"]
    months = sorted(nm)
    peak_m = max(nm, key=nm.get)
    if k6["near"] >= k6["peer_median"]:
        how = "about as well as" if c1["robustness"]["peer_median_inside_near_ci"] else "better than"
    else:
        how = "less well than"
    led = "lead" if c["C2"]["status"] == "HOLDS" else "do not lead"
    pre, post = a["raw"]["pre_mean"], a["raw"]["post_mean"]
    collapse = next((r["month"] for r in cov["series"] if r["month"] > cov["last_good_month"] and not r["good"]), None)
    return {
        "mad": (f"NEAR had {nm[months[-1]]:,} monthly active developers in {months[-1]}, "
                f"{'down' if nm[months[-1]] < nm[peak_m] else 'level'} from a peak of {nm[peak_m]:,} in {peak_m}",
                f"Monthly active developers (MAD) by ecosystem, {months[0]} to {months[-1]}"),
        "retention": (f"NEAR keeps new developers {how} its peers (6-month retention {ret(k6['near'])} vs "
                      f"{ret(k6['peer_median'])})",
                      f"Share of each monthly cohort of new developers still active k months later, cohorts from "
                      f"{c1['cohort_start']}, NEAR vs peers and their median"),
        "c2": (f"NEAR developer counts {led} contract deployments (best p = {pval(c2_best(c, 'raw'))}, needed "
               f"p < {alpha_(c['C2']['raw']['deploys']['bonferroni_alpha'])})",
               "NEAR developers (MAD), contracts deployed and unique deployer accounts, each scaled so its 2022 average is 100 (log scale)"),
        "c3a": (f"Contracts deployed per NEAR developer averaged {post:.2f} a month from 2025, "
                f"{'down' if post < pre else 'up'} from {pre:.2f} in 2023–24 (raw MAD)",
                "Contracts deployed per MAD each month; dotted lines are period means, the dashed line is the C3a threshold"),
        "hackathon": (f"{frac(b['authors_new'], b['authors'])} NEAR HACKATHON commit authors were new to tracked NEAR repos",
                      "Commit authors by prior NEAR activity, and commits with an AI co-author trailer by tool"),
        "coverage": (f"GH Archive volume broke in {cov['level_break_month']} and fell away from {collapse}, so the "
                     f"analysis stops at {cov['last_good_month']}",
                     "Monthly push and pull-request events relative to the median of the previous 12 months"),
    }


def data_as_of(c: dict) -> str:
    d, b = c["data_as_of"], c["C3b"]
    return (f"GH Archive (GHA, a public record of GitHub events) usable through {d['gha_last_good_month']} (coverage rule); NEAR contract "
            f"deployments through {d['near_deploys_last_month']} (current month partial; C2 and C3a use months through "
            f"{d['gha_last_good_month']} to match GHA); hackathon cohort fetched {d['hackathon_fetched_at'][:10]}; "
            f"Open Dev Data commit `{d['open_dev_data_commit']}`.")


def scorecard(c: dict) -> list[dict]:
    """Rows: id, claim, kill, measured, status, note, indent."""
    c1, c2, a, b = c["C1"], c["C2"], c["C3a"], c["C3b"]
    k6, k12 = c1["by_k"]["6"], c1["by_k"]["12"]
    rob = c1["robustness"]
    tie = c1["status"] == "HOLDS" and rob["peer_median_inside_near_ci"]
    c1_note = []
    if tie:
        c1_note.append(f"Statistical tie: margin {pp(c1['margin_6m_pp'])}, NEAR 95% CI "
                       f"{ret(c1['near_6m_ci95'][0])}–{ret(c1['near_6m_ci95'][1])} contains the peer median.")
    c1_note.append(f"Fragility: smoothed 6-month {ret(k6['near_smooth'])} vs {ret(k6['peer_median_smooth'])} "
                   f"({'holds' if rob['smoothed_6m_holds'] else 'fails'}); "
                   f"12-month {ret(k12['near'])} vs {ret(k12['peer_median'])} ({'holds' if rob['k12_holds'] else 'fails'}).")
    return [
        dict(id="C1", claim="New NEAR developers retain at least as well as peers (Solana, Sui, Aptos, Base)",
             kill="NEAR 6-month retention below peer median",
             measured=f"{ret(k6['near'])} vs peer median {ret(k6['peer_median'])}",
             status=c1["status"] + (" (statistical tie)" if tie else ""),
             note=" ".join(c1_note), indent=False),
        dict(id="C2", claim="NEAR monthly active developers (MAD) lead contract deployments by 1–6 months",
             kill=f"No lag with p < {alpha_(c2['raw']['deploys']['bonferroni_alpha'])} (0.05 / 6, Bonferroni)",
             measured=f"best p {pval(c2_best(c, 'raw'))} raw / {pval(c2_best(c, 'adjusted'))} coverage-adjusted",
             status=c2["status"],
             note="Raw and coverage-adjusted MAD agree." if c2["status"] != "FRAGILE" else "Raw and adjusted disagree.",
             indent=False),
        dict(id="C3", claim="AI-era funnel: needs both C3a and C3b", kill="C3a or C3b killed",
             measured="see C3a, C3b", status=c["C3"]["status"], note="", indent=False),
        dict(id="C3a", claim="Contracts deployed per MAD rose since 2025",
             kill=f"Post-2025 mean not above {times(1 + a['min_rise'])} the 2023–24 mean",
             measured=f"{times(a['raw']['ratio'])} raw, {times(a['adjusted']['ratio'])} coverage-adjusted",
             status=a["status"],
             note=f"Mann-Whitney p = {pval(a['raw']['mann_whitney_p'])} (raw), not part of the criterion.", indent=True),
        dict(id="C3b", claim="A majority of NEAR HACKATHON authors are new to NEAR",
             kill="New-to-NEAR authors fewer than 50% of the cohort (stricter of two shares)",
             measured=f"{pct(b['new_share_all'])} ({frac(b['authors_new'], b['authors'])}); "
                      f"{pct(b['new_share_excl_truncated'])} excluding {b['authors_truncated']} authors with truncated event feeds",
             status=b["status"],
             note=f"AI co-authored: ≥{pct(b['ai_commit_share'])} of commits, {ai_repos(b)}.", indent=True),
    ]


def flips(c: dict) -> list[str]:
    c1, c2, a, b = c["C1"], c["C2"], c["C3a"], c["C3b"]
    k6 = c1["by_k"]["6"]
    need = (1 + a["min_rise"]) * a["raw"]["pre_mean"]
    need_adj = (1 + a["min_rise"]) * a["adjusted"]["pre_mean"]
    al = alpha_(c2["raw"]["deploys"]["bonferroni_alpha"])
    return [
        f"C1 ({c1['status']}) flips to KILLED if NEAR's 6-month retention drops below the peer median "
        f"(today {ret(k6['near'])} vs {ret(k6['peer_median'])}, a margin of {pp(c1['margin_6m_pp'])}). "
        f"Watch it: the margin is inside sampling error.",
        f"C2 ({c2['status']}) flips to HOLDS if any lag 1–6 reaches p < {al} for deploys or unique deployers, "
        f"on both raw and coverage-adjusted MAD (on only one: FRAGILE). Best today: "
        f"{pval(c2_best(c, 'raw'))} raw, {pval(c2_best(c, 'adjusted'))} adjusted.",
        f"C3a ({a['status']}) flips to HOLDS if mean contracts per MAD from 2025-01 is above "
        f"{times(1 + a['min_rise'])} the 2023–24 mean: above {need:.2f} raw (today {a['raw']['post_mean']:.2f}) and above "
        f"{need_adj:.2f} adjusted (today {a['adjusted']['post_mean']:.2f}).",
        f"C3b ({b['status']}) flips to KILLED if new-to-NEAR authors are fewer than 50% of a future cohort "
        f"(today {pct(b['new_share_strict'])}, stricter of the two shares).",
        f"The verdict ({c['verdict']}) becomes Bull if one more top-level claim holds. That means either C2 holds, or "
        f"C3a holds, which makes C3 hold because C3b already does. It becomes Bear if C1 flips to KILLED.",
    ]


def exploratory(c: dict) -> list[str]:
    rg = reverse_granger(c)
    rows = ", ".join(f"lag {k}: {pval(v)}" for k, v in sorted(rg["p"].items()))
    s = (f"Deploys → developers (the reverse of C2, raw MAD, log-differenced): Granger p-values {rows}. "
         f"Bonferroni threshold across 6 lags: {alpha_(rg['alpha'])}. ")
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
        f"{months[-1]}, the last month with reliable GHA coverage.",
        "Developers do not lead onchain usage (C2 killed), so in this data developer counts give no early warning of "
        "usage, which removes the main reason to watch them as a signal for the token.",
        f"Output per developer fell ({times(a['raw']['ratio'])} raw, {times(a['adjusted']['ratio'])} adjusted). Fewer "
        f"developers are not being offset by more contracts each.",
        "NEAR's retention is no better than its peers'. It is a statistical tie at 6 months and behind at 12.",
        f"The hackathon brought {b['authors']} mostly new authors, but a two-week cohort says nothing yet about "
        f"whether they stay. C1 suggests about {ret(c['C1']['by_k']['6']['near'])} of new NEAR developers are "
        f"still active six months later.",
    ]


def limitations(c: dict) -> list[str]:
    cov = c["coverage"]
    b = c["C3b"]
    return [
        f"GHA volume breaks in {cov['level_break_month']} (pushes fall about 30%) and collapses after "
        f"{cov['last_good_month']} (pull requests, then pushes). Series end at {cov['last_good_month']}; C2 and C3a are "
        f"also run on coverage-adjusted MAD, and disagreements would be reported as FRAGILE.",
        "Developer identity is the GHA actor of a push or PR on a repo listed in Open Dev Data. Electric Capital "
        "counts original commit authors, so levels differ from the Developer Report. Private repos and unlisted repos "
        "are invisible.",
        "I started the history at 2021-01 to stay within the BigQuery budget, so some developers counted as new in "
        "2022 had been active before 2021.",
        "Deployments are transaction-level DEPLOY_CONTRACT only. I excluded factory-created contracts on purpose "
        "(THESIS.md, Methodology changes, item 4).",
        f"C3b covers {b['repos_github']} repos with a GitHub link out of {b['nearhunt_projects']} nearhunt.xyz projects "
        f"({b['submissions_official']} official submissions); {b['commits_no_login']:,} commits had no linked GitHub "
        f"account. {b['authors_feed_capped']} authors hit GitHub's 300-event feed cap; {b['authors_truncated']} of them "
        f"have feeds that stop after 2026-10-19 and are shown both included and excluded.",
        f"AI co-authorship is detected from commit trailers only, a lower bound. The repo share uses repos with at least "
        f"one non-bot commit ({b['ai_repo_denominator']} of {b['repos_github']}); {b['repos_only_bot_commits']} repo's "
        f"only author has a login ending in \"-bot\" and is removed by the bot filter.",
        "I fixed the C3a threshold (>10%) after I had seen the deployment series. THESIS.md, Methodology changes, "
        "item 6, gives the exact order of events with commit hashes.",
    ]


# ------------------------------------------------------------------ markdown

def md_scorecard(c: dict) -> str:
    out = ["| Claim | Kill criterion | Measured | Status |", "|---|---|---|---|"]
    for r in scorecard(c):
        name = ("&nbsp;&nbsp;↳ " if r["indent"] else "") + f"{r['id']}: {r['claim']}"
        status = r["status"] + (f"<br>{r['note']}" if r["note"] else "")
        out.append(f"| {name} | {r['kill']} | {r['measured']} | {status} |")
    return "\n".join(out)


def md_results(c: dict) -> str:
    v = c["verdict"]
    parts = [
        f"## Results (verdict: **{v}**, {c['claims_holding']} of 3 top-level claims hold)", "",
        VERDICT_RULE, "",
        f"Data as of: {data_as_of(c)} Every figure below is read from "
        f"[`data/cache/claims.json`](data/cache/claims.json), produced by `make analysis`.", "",
        md_scorecard(c), "",
        "## What would change the verdict", "",
        "Each line gives the threshold that would flip a claim on the next rebuild (`make data && make all`).", "",
        *[f"- {f}" for f in flips(c)], "",
        "## Exploratory, not pre-registered", "",
        *[f"- {e}" for e in exploratory(c)], "",
        "## Bear case", "",
        *[f"- {x}" for x in bear_case(c)], "",
        "## Limitations", "",
        *[f"- {x}" for x in limitations(c)],
    ]
    return "\n".join(parts)


def md_readme_verdict(c: dict) -> str:
    return (f"**Verdict: {c['verdict']}** ({c['claims_holding']} of 3 top-level claims hold). {VERDICT_RULE}\n\n"
            f"{PREREG}\n\n" + "\n".join(f"- {h}" for h in headlines(c)))


def how_built(c: dict) -> list[str]:
    """My role, stated factually. Numbers come from claims.json."""
    return [
        f"I surveyed the {c['C3b']['submissions_official']} public NEAR HACKATHON submissions and picked the angle none "
        f"of the thesis entries used: developer data instead of fees and price.",
        "I pre-registered the claims with kill criteria and committed them before pulling any data (`333ea0c`), so the "
        "verdict could not be tuned afterwards.",
        "I set the BigQuery budget and approved each spend. When GH Archive turned out to have coverage breaks, I paid "
        "for one consistent push and pull-request coverage index across the whole period rather than a cheaper mixed "
        "method.",
        "I added the FRAGILE rule: if raw and coverage-adjusted results disagree, the claim is reported as fragile "
        "instead of taking the favourable result.",
        "I kept the results when they came out neutral to bearish, and I cut an overclaim (\"developers follow usage\") "
        "that the statistics did not support.",
        "I directed AI coding agents (Claude Code) to implement the pipeline, tests and site, reviewed every phase, and "
        "approved every change.",
        "All code in this repository was written during NEAR HACKATHON, November 2026.",
    ]


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
    t = replace_block(t, "implication", " ".join(implication(c)))
    t = replace_block(t, "results", md_results(c))
    out["THESIS.md"] = t
    r = (ROOT / "README.md").read_text(encoding="utf-8")
    r = replace_block(r, "one-liner", one_liner(c))
    r = replace_block(r, "verdict", md_readme_verdict(c))
    r = replace_block(r, "implication", " ".join(implication(c)))
    r = replace_block(r, "claims", md_scorecard(c))
    r = replace_block(r, "method", "\n".join(f"- {x}" for x in method_brief(c)))
    r = replace_block(r, "limitations", "\n".join(f"- {x}" for x in limitations(c)))
    r = replace_block(r, "how-built", "\n".join(f"- {x}" for x in how_built(c)))
    out["README.md"] = r
    return out
