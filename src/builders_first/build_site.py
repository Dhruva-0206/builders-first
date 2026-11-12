"""Build site/index.html from data/cache/claims.json only (no network), and rewrite the generated
blocks in THESIS.md and README.md. Output is deterministic so CI can diff it against the commit.
"""
from __future__ import annotations

import html
import re

import plotly.graph_objects as go

from . import report
from .ingest_ecosystems import ECOSYSTEMS, PEERS
from .paths import ROOT, SITE

PLOTLY_CDN = "https://cdn.plot.ly/plotly-2.35.2.min.js"
# Categorical slots 1-5 (validated: scripts/validate_palette.js, light surface #fcfcfb).
COLORS = dict(zip(ECOSYSTEMS, ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]))
S1, S2, S3 = "#2a78d6", "#eb6834", "#1baf7a"
INK, INK2, MUTED, GRID, SURFACE = "#0b0b0b", "#52514e", "#8a8984", "#e6e5e1", "#fcfcfb"
FONT = "Inter, -apple-system, Segoe UI, Roboto, sans-serif"


def _layout(fig: go.Figure, title: str, ytitle: str, height: int = 380, **kw) -> go.Figure:
    base = dict(
        title=dict(text=title, font=dict(size=15, color=INK), x=0, xanchor="left"),
        font=dict(family=FONT, size=12, color=INK2), paper_bgcolor=SURFACE, plot_bgcolor=SURFACE,
        height=height, margin=dict(l=56, r=86, t=56, b=44), hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.0, xanchor="right", x=1, font=dict(size=11)),
    )
    base.update(kw)
    fig.update_layout(**base)
    fig.update_xaxes(showgrid=False, linecolor=GRID, ticks="outside", tickcolor=GRID)
    fig.update_yaxes(title=ytitle, gridcolor=GRID, zeroline=False, linecolor=GRID)
    return fig


def _end_labels(fig: go.Figure, series: dict[str, tuple[list, list, str]]) -> None:
    """Direct labels at the right end of each line (text in ink, a colored mark beside it)."""
    for name, (xs, ys, color) in series.items():
        fig.add_annotation(x=xs[-1], y=ys[-1], text=f"<span style='color:{color}'>●</span> {name}",
                           showarrow=False, xanchor="left", xshift=6, font=dict(size=11, color=INK))


def fig_mad(c: dict) -> go.Figure:
    fig = go.Figure()
    ends = {}
    for e in ECOSYSTEMS:
        s = c["mad"][e]
        xs, ys = sorted(s), [s[m] for m in sorted(s)]
        fig.add_trace(go.Scatter(x=xs, y=ys, name=e, mode="lines", line=dict(color=COLORS[e], width=3 if e == "NEAR" else 2),
                                 hovertemplate=f"{e}: %{{y:,}}<extra></extra>"))
        ends[e] = (xs, ys, COLORS[e])
    _end_labels(fig, ends)
    _layout(fig, "Monthly active developers by ecosystem", "developers / month")
    fig.update_layout(updatemenus=[dict(type="buttons", direction="right", x=0, y=1.13, xanchor="left", showactive=True,
                                        buttons=[dict(label="Linear", method="relayout", args=[{"yaxis.type": "linear"}]),
                                                 dict(label="Log", method="relayout", args=[{"yaxis.type": "log"}])])])
    return fig


def fig_retention(c: dict) -> go.Figure:
    cur = c["C1"]["curve"]
    ks = list(range(1, len(cur["NEAR"]) + 1))
    peer_med = [sorted(cur[p][i] for p in PEERS)[1:3] for i in range(len(ks))]
    peer_med = [(a + b) / 2 for a, b in peer_med]
    fig = go.Figure()
    for p in PEERS:
        fig.add_trace(go.Scatter(x=ks, y=cur[p], name=p, mode="lines", line=dict(color=COLORS[p], width=1),
                                 opacity=0.55, hovertemplate=f"{p}: %{{y:.1%}}<extra></extra>"))
    fig.add_trace(go.Scatter(x=ks, y=peer_med, name="Peer median", mode="lines", line=dict(color=INK2, width=2, dash="dash"),
                             hovertemplate="Peer median: %{y:.1%}<extra></extra>"))
    fig.add_trace(go.Scatter(x=ks, y=cur["NEAR"], name="NEAR", mode="lines+markers", line=dict(color=COLORS["NEAR"], width=3),
                             marker=dict(size=8), hovertemplate="NEAR: %{y:.1%}<extra></extra>"))
    fig.add_vline(x=6, line=dict(color=MUTED, width=1, dash="dot"))
    fig.add_annotation(x=6, y=1, yref="paper", text="pre-registered test: month 6", showarrow=False, xanchor="left",
                       xshift=4, font=dict(size=11, color=INK2))
    _layout(fig, f"Retention of new developers (cohorts {c['C1']['cohort_start']} on, pooled)", "share still active")
    fig.update_xaxes(title="months after first activity", dtick=1)
    fig.update_yaxes(tickformat=".0%")
    return fig


def fig_c2(c: dict) -> go.Figure:
    mad = c["mad"]["NEAR"]
    dep = c["near_deploys"]
    months = [m for m in sorted(mad) if m >= c["C2"]["window"][0] and m in dep]
    base = [m for m in months if m.startswith("2022")]

    def idx(vals):
        b = sum(vals[m] for m in base) / len(base)
        return [vals[m] / b * 100 for m in months]

    series = {
        "Active developers": (idx(mad), S1),
        "Contracts deployed": (idx({m: dep[m]["deploys"] for m in months}), S2),
        "Unique deployers": (idx({m: dep[m]["unique_deployers"] for m in months}), S3),
    }
    fig = go.Figure()
    ends = {}
    for name, (ys, col) in series.items():
        fig.add_trace(go.Scatter(x=months, y=ys, name=name, mode="lines", line=dict(color=col, width=2),
                                 hovertemplate=f"{name}: %{{y:.0f}}<extra></extra>"))
        ends[name] = (months, ys, col)
    _end_labels(fig, ends)
    _layout(fig, "NEAR developers vs contract deployments (index, 2022 average = 100, log scale)", "index")
    fig.update_yaxes(type="log")
    return fig


def fig_c3a(c: dict) -> go.Figure:
    a = c["C3a"]
    fig = go.Figure()
    for label, col, name in (("raw", S1, "Raw MAD"), ("adjusted", S2, "Coverage-adjusted MAD")):
        s = a["series"][label]
        xs = sorted(s)
        fig.add_trace(go.Scatter(x=xs, y=[s[m] for m in xs], name=name, mode="lines", line=dict(color=col, width=2),
                                 hovertemplate=f"{name}: %{{y:.2f}}<extra></extra>"))
    pre_end, post = a["pre"][1], a["post"]
    for label, col in (("raw", S1), ("adjusted", S2)):
        r = a[label]
        fig.add_shape(type="line", x0=a["pre"][0], x1=pre_end, y0=r["pre_mean"], y1=r["pre_mean"], line=dict(color=col, width=1, dash="dot"))
        fig.add_shape(type="line", x0=post[0], x1=post[1], y0=r["post_mean"], y1=r["post_mean"], line=dict(color=col, width=1, dash="dot"))
    thr = (1 + a["min_rise"]) * a["raw"]["pre_mean"]
    fig.add_shape(type="line", x0=post[0], x1=post[1], y0=thr, y1=thr, line=dict(color=INK2, width=1.5, dash="dash"))
    fig.add_annotation(x=post[1], y=thr, text=f"needed to hold (raw): {thr:.2f}", showarrow=False, xanchor="right",
                       yshift=10, font=dict(size=11, color=INK2))
    fig.add_vline(x="2025-05", line=dict(color=MUTED, width=1, dash="dot"))
    fig.add_annotation(x="2025-05", y=1, yref="paper", text="2025-05: AI coding agents GA (annotation only)",
                       showarrow=False, xanchor="right", xshift=-4, font=dict(size=11, color=INK2))
    _layout(fig, "Contracts deployed per monthly active developer (dotted: period means)", "contracts / developer")
    return fig


def fig_hackathon(c: dict) -> go.Figure:
    b = c["C3b"]
    tools = b["ai_by_tool"]
    fig = go.Figure()
    cats = ["New to NEAR", "Returning (GH Archive)", "Returning (feed only)"]
    vals = [b["authors_new"], b["authors_prior_gha"], b["authors_prior_feed_only"]]
    fig.add_trace(go.Bar(y=cats, x=vals, orientation="h", marker=dict(color=S1, cornerradius=4), name="Authors",
                         text=vals, textposition="outside", xaxis="x", yaxis="y", hovertemplate="%{y}: %{x}<extra></extra>"))
    tn = [k for k in tools]
    fig.add_trace(go.Bar(y=tn, x=[tools[k] for k in tn], orientation="h", marker=dict(color=S2, cornerradius=4),
                         name="AI-trailer commits", text=[f"{tools[k]:,}" for k in tn], textposition="outside",
                         xaxis="x2", yaxis="y2", hovertemplate="%{y}: %{x:,} commits<extra></extra>"))
    _layout(fig, f"NEAR HACKATHON cohort: {b['authors']} commit authors, {b['commits_non_bot']:,} non-bot commits", "", height=360,
            showlegend=False, hovermode="closest",
            xaxis=dict(domain=[0, 0.44]), xaxis2=dict(domain=[0.56, 1], showgrid=False),
            yaxis=dict(anchor="x", autorange="reversed"), yaxis2=dict(anchor="x2", autorange="reversed"))
    fig.update_yaxes(title=None)
    fig.add_annotation(x=0.22, y=-0.16, xref="paper", yref="paper", text="authors", showarrow=False, font=dict(color=INK2))
    fig.add_annotation(x=0.78, y=-0.16, xref="paper", yref="paper", text="commits with an AI co-author trailer, by tool",
                       showarrow=False, font=dict(color=INK2))
    return fig


def fig_coverage(c: dict) -> go.Figure:
    cov = c["coverage"]
    s = [r for r in cov["series"] if r["push_ratio"] is not None]
    xs = [r["month"] for r in s]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=xs, y=[r["push_ratio"] for r in s], name="Push events", mode="lines", line=dict(color=S1, width=2),
                             hovertemplate="Push: %{y:.2f}<extra></extra>"))
    fig.add_trace(go.Scatter(x=xs, y=[r["pr_ratio"] for r in s], name="Pull-request events", mode="lines", line=dict(color=S2, width=2),
                             hovertemplate="PR: %{y:.2f}<extra></extra>"))
    fig.add_hline(y=cov["threshold"], line=dict(color=INK2, width=1, dash="dash"))
    fig.add_annotation(x=xs[0], y=cov["threshold"], text=f"{cov['threshold']:.0%} rule", showarrow=False, xanchor="left",
                       yshift=-10, font=dict(size=11, color=INK2))
    fig.add_vrect(x0=cov["last_good_month"], x1=xs[-1], fillcolor=GRID, opacity=0.6, line_width=0)
    fig.add_annotation(x=cov["last_good_month"], y=1, yref="paper", text=f"excluded after {cov['last_good_month']}",
                       showarrow=False, xanchor="left", xshift=4, font=dict(size=11, color=INK2))
    if cov["level_break_month"]:
        fig.add_vline(x=cov["level_break_month"], line=dict(color=MUTED, width=1, dash="dot"))
        fig.add_annotation(x=cov["level_break_month"], y=0.04, yref="paper", text=f"level break {cov['level_break_month']}",
                           showarrow=False, xanchor="right", xshift=-4, font=dict(size=11, color=INK2))
    _layout(fig, "GH Archive volume vs its trailing 12-month median (why the series stop early)", "ratio")
    return fig


# ------------------------------------------------------------------ HTML

def _md_inline(s: str) -> str:
    s = html.escape(s, quote=False)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"`(.+?)`", r"<code>\1</code>", s)
    return s


def _table(headers: list[str], rows: list[list]) -> str:
    th = "".join(f"<th>{html.escape(str(h))}</th>" for h in headers)
    trs = "".join("<tr>" + "".join(f"<td>{html.escape(str(v))}</td>" for v in r) + "</tr>" for r in rows)
    return f'<div class="tw"><table><thead><tr>{th}</tr></thead><tbody>{trs}</tbody></table></div>'


def _details(summary: str, inner: str) -> str:
    return f"<details><summary>{html.escape(summary)}</summary>{inner}</details>"


def _fig(fig: go.Figure, div_id: str) -> str:
    return fig.to_html(full_html=False, include_plotlyjs=False, div_id=div_id,
                       config={"displaylogo": False, "responsive": True, "modeBarButtonsToRemove": ["select2d", "lasso2d"]})


def _status_badge(s: str) -> str:
    key = s.split(" ")[0].lower()
    return f'<span class="st st-{key}">{html.escape(s)}</span>'


def build_html(c: dict) -> str:
    rows = report.scorecard(c)
    score = "".join(
        f'<tr class="{"sub" if r["indent"] else ""}"><td><strong>{r["id"]}</strong> {html.escape(r["claim"])}</td>'
        f'<td>{html.escape(r["kill"])}</td><td>{html.escape(r["measured"])}</td>'
        f'<td>{_status_badge(r["status"])}{"<div class=note>" + html.escape(r["note"]) + "</div>" if r["note"] else ""}</td></tr>'
        for r in rows)
    mad = c["mad"]
    months = sorted(mad["NEAR"])
    mad_tbl = _table(["month", *ECOSYSTEMS], [[m, *[mad[e].get(m, "") for e in ECOSYSTEMS]] for m in months])
    cur = c["C1"]["curve"]
    ret_tbl = _table(["k (months)", *ECOSYSTEMS], [[k + 1, *[f"{cur[e][k]:.1%}" for e in ECOSYSTEMS]] for k in range(len(cur["NEAR"]))])
    g = c["C2"]
    lag_rows = []
    for lag in range(1, g["max_lag"] + 1):
        L = str(lag)
        lag_rows.append([lag, f"{g['raw']['deploys']['granger_p'][L]:.3f}", f"{g['raw']['unique_deployers']['granger_p'][L]:.3f}",
                         f"{g['adjusted']['deploys']['granger_p'][L]:.3f}", f"{g['adjusted']['unique_deployers']['granger_p'][L]:.3f}",
                         f"{g['raw']['deploys']['ccf'][L]:+.2f}", f"{g['raw']['deploys']['reverse_granger_p'][L]:.3f}"])
    lag_tbl = _table(["lag", "p deploys (raw)", "p deployers (raw)", "p deploys (adj.)", "p deployers (adj.)",
                      "corr dev→deploys", "reverse p (exploratory)"], lag_rows)
    a = c["C3a"]
    c3a_tbl = _table(["month", "raw", "adjusted"], [[m, a["series"]["raw"][m], a["series"]["adjusted"][m]] for m in sorted(a["series"]["raw"])])
    cov_tbl = _table(["month", "push events", "PR events", "push ratio", "PR ratio", "good"],
                     [[r["month"], f"{r['push_events']:,}", f"{r['pr_events']:,}", r["push_ratio"] if r["push_ratio"] is not None else "",
                       r["pr_ratio"] if r["pr_ratio"] is not None else "", "yes" if r["good"] else "no"] for r in c["coverage"]["series"]])
    b = c["C3b"]
    hk_tbl = _table(["measure", "value"], [[k, v] for k, v in b.items() if not isinstance(v, dict)] +
                    [[f"AI commits: {k}", v] for k, v in b["ai_by_tool"].items()])
    li = lambda xs: "<ul>" + "".join(f"<li>{_md_inline(x)}</li>" for x in xs) + "</ul>"
    v = c["verdict"]
    d = c["data_as_of"]

    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Builders First</title>
<meta name="description" content="A NEAR investment thesis from developer data: three pre-registered claims, rebuilt from public data.">
<script src="{PLOTLY_CDN}"></script>
<style>
:root {{ --surface:{SURFACE}; --ink:{INK}; --ink2:{INK2}; --muted:{MUTED}; --grid:{GRID}; --accent:{S1}; }}
* {{ box-sizing:border-box; }}
body {{ margin:0; background:var(--surface); color:var(--ink); font:15px/1.55 {FONT}; }}
main {{ max-width:1000px; margin:0 auto; padding:24px 16px 64px; }}
h1 {{ font-size:28px; margin:0 0 4px; }} h2 {{ font-size:19px; margin:40px 0 8px; }}
.lede {{ color:var(--ink2); font-size:16px; max-width:760px; }}
.meta {{ color:var(--ink2); font-size:13px; }}
.verdict {{ display:inline-block; padding:4px 12px; border-radius:6px; font-weight:700; border:2px solid var(--ink); margin:12px 0; }}
.box {{ border:1px solid var(--grid); border-radius:8px; padding:4px 18px; background:#fff; }}
.box li {{ margin:10px 0; }}
.tw {{ overflow-x:auto; }}
table {{ border-collapse:collapse; width:100%; font-size:13px; }}
th, td {{ text-align:left; vertical-align:top; padding:8px 10px; border-bottom:1px solid var(--grid); }}
th {{ color:var(--ink2); font-weight:600; }}
tr.sub td:first-child {{ padding-left:28px; }}
.note {{ color:var(--ink2); font-size:12px; margin-top:4px; }}
.st {{ font-weight:700; padding:1px 6px; border-radius:4px; white-space:nowrap; }}
.st-holds::before {{ content:"✓ "; }} .st-killed::before {{ content:"✕ "; }} .st-fragile::before {{ content:"~ "; }}
.st-holds {{ background:#e3f1e3; color:#0b5d0b; }} .st-killed {{ background:#f8e1e0; color:#9b1c1b; }} .st-fragile {{ background:#fbf0d6; color:#7a5200; }}
.chart {{ margin:8px 0 4px; }}
details {{ margin:4px 0 16px; font-size:13px; }} summary {{ cursor:pointer; color:var(--accent); }}
details table {{ margin-top:8px; }}
code {{ background:#f1f0ec; padding:1px 4px; border-radius:3px; font-size:13px; }}
footer {{ margin-top:48px; color:var(--ink2); font-size:13px; border-top:1px solid var(--grid); padding-top:12px; }}
a {{ color:var(--accent); }}
</style></head>
<body><main>
<h1>Builders First</h1>
<p class="lede">{_md_inline(report.one_liner(c))}</p>
<div class="verdict">Verdict: {v} ({c['claims_holding']} of 3 claims hold)</div>
<p class="meta">Data as of: NEAR deployments to {d['near_deploys_last_month']} · GH Archive reliable to {d['gha_last_good_month']} ·
hackathon data fetched {d['hackathon_fetched_at'][:10]} · Open Dev Data commit <code>{d['open_dev_data_commit']}</code>.
Every number on this page is read from <code>data/cache/claims.json</code>.</p>

<h2>Headline findings</h2>
<div class="box">{li(report.headlines(c))}</div>

<h2>Claims scorecard</h2>
<p class="meta">Claims, thresholds and methods were committed before the results (see THESIS.md and its git history). Verdict rule: Bull if ≥2 claims hold, Neutral if 1, Bear if 0; FRAGILE claims do not count.</p>
<div class="tw"><table><thead><tr><th>Claim</th><th>Kill criterion</th><th>Measured</th><th>Status</th></tr></thead><tbody>{score}</tbody></table></div>

<h2>Developers: NEAR vs peers</h2>
<div class="chart">{_fig(fig_mad(c), "fig-mad")}</div>
{_details("Table: monthly active developers", mad_tbl)}

<h2>C1 · Retention</h2>
<div class="chart">{_fig(fig_retention(c), "fig-ret")}</div>
{_details("Table: retention by month after first activity", ret_tbl)}

<h2>C2 · Do developers lead usage?</h2>
<div class="chart">{_fig(fig_c2(c), "fig-c2")}</div>
<p class="meta">Granger tests on log-differenced monthly series, {g['window'][0]} to {g['window'][1]}. Bonferroni threshold {g['raw']['deploys']['bonferroni_alpha']:.4f}. The last column is exploratory (deploys → developers) and not part of any claim.</p>
{lag_tbl}

<h2>C3a · Output per developer</h2>
<div class="chart">{_fig(fig_c3a(c), "fig-c3a")}</div>
{_details("Table: contracts per MAD", c3a_tbl)}

<h2>C3b · The NEAR HACKATHON cohort</h2>
<div class="chart">{_fig(fig_hackathon(c), "fig-hack")}</div>
{_details("Table: cohort measures", hk_tbl)}

<h2>Data quality · GH Archive coverage</h2>
<div class="chart">{_fig(fig_coverage(c), "fig-cov")}</div>
<p class="meta">A month is good if push and PR volume are both ≥{c['coverage']['threshold']:.0%} of their trailing 12-month median. Series end before the final run of bad months; from the level break on, C2 and C3a are also computed on coverage-adjusted MAD.</p>
{_details("Table: GH Archive volume", cov_tbl)}

<h2>What would change the verdict</h2>
{li(report.flips(c))}

<h2>Exploratory, not pre-registered</h2>
{li(report.exploratory(c))}

<h2>Bear case</h2>
{li(report.bear_case(c))}

<h2>Limitations</h2>
{li(report.limitations(c))}

<h2>Re-run it</h2>
<p><code>make setup &amp;&amp; make all</code> rebuilds the claims, this page and the tests offline from <code>data/cache/</code>.
<code>make setup-data &amp;&amp; make data</code> refreshes the caches from the sources (needs GitHub and Google Cloud credentials; see README).</p>

<footer>
Source: Open Dev Data by Electric Capital — <a href="https://github.com/electric-capital/open-dev-data">https://github.com/electric-capital/open-dev-data</a> (CC BY 4.0).
Also GH Archive, the NEAR public BigQuery dataset (<code>bigquery-public-data.crypto_near_mainnet_us</code>), nearhunt.xyz, nearhackathon.com and the GitHub REST API.
Built during NEAR HACKATHON (Nov 2026). Not investment advice.
</footer>
</main></body></html>
"""


def main() -> None:
    c = report.load_claims()
    SITE.mkdir(exist_ok=True)
    (SITE / "index.html").write_text(build_html(c), encoding="utf-8", newline="\n")
    for path, text in report.render_docs(c).items():
        (ROOT / path).write_text(text, encoding="utf-8", newline="\n")
    print("site/index.html written; THESIS.md and README.md generated blocks updated")


if __name__ == "__main__":
    main()
