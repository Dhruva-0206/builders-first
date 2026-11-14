"""Build site/index.html and the per-chart CSVs from data/cache/claims.json only (no network), and
rewrite the generated blocks in THESIS.md and README.md. Output is deterministic so CI can diff it.
"""
from __future__ import annotations

import csv
import html
import io
import math
import re

import plotly.graph_objects as go
import plotly.io as pio

from . import report
from .ingest_ecosystems import ECOSYSTEMS, PEERS
from .paths import CACHE, ROOT, SITE

# The stdlib JSON encoder formats floats the same whether or not orjson is installed.
pio.json.config.default_engine = "json"

PLOTLY_CDN = "https://cdn.plot.ly/plotly-2.35.2.min.js"
SITE_URL = "https://dhruva-0206.github.io/builders-first/"
REPO_URL = "https://github.com/Dhruva-0206/builders-first"
AUTHOR = "Dhruva Somen Chakrabarty"
AUTHOR_URL = "https://github.com/Dhruva-0206"
CHART_DIR = CACHE / "charts"

# One strong colour for NEAR, greys for peers, one second accent (orange) for non-ecosystem series.
# NEAR blue and the orange are slots 1 and 2 of the validated categorical palette; every line also
# carries a direct label, so identity never depends on colour alone.
NEAR_C, ACCENT2 = "#2a78d6", "#d9581f"
PEER_C = dict(zip(PEERS, ["#4f4e4a", "#6e6d68", "#8f8e88", "#adaca6"]))
COLORS = {"NEAR": NEAR_C, **PEER_C}
INK, INK2, MUTED, GRID, SURFACE = "#1a1a19", "#4f4e4a", "#8a8984", "#e8e7e3", "#ffffff"
FONT = "system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"
TOP, BOTTOM = 16, 40


def _layout(fig: go.Figure, ytitle: str, height: int = 360, **kw) -> go.Figure:
    base = dict(
        font=dict(family=FONT, size=13, color=INK2), paper_bgcolor=SURFACE, plot_bgcolor=SURFACE,
        height=height, margin=dict(l=52, r=132, t=TOP, b=BOTTOM), hovermode="x unified", showlegend=False,
    )
    base.update(kw)
    fig.update_layout(**base)
    fig.update_xaxes(showgrid=False, linecolor=GRID, ticks="outside", tickcolor=GRID)
    fig.update_yaxes(title=ytitle, gridcolor=GRID, zeroline=False, showline=False)
    return fig


def _end_labels(fig: go.Figure, series: dict[str, tuple[list, list, str]], height: int = 360,
                log: bool = False, min_gap_px: int = 15) -> None:
    """Label each line at its right end; labels are pushed apart so they never overlap."""
    plot_px = height - TOP - BOTTOM
    tr = math.log10 if log else (lambda v: v)
    allv = [tr(v) for _, ys, _ in series.values() for v in ys if v is not None and v > 0]
    lo, hi = min(allv), max(allv)
    span = (hi - lo) or 1.0
    ends = sorted((tr(ys[-1]), name, xs[-1], color) for name, (xs, ys, color) in series.items())
    placed = []
    for y, name, x, color in ends:
        px = (y - lo) / span * plot_px
        if placed and px - placed[-1] < min_gap_px:
            px = placed[-1] + min_gap_px
        placed.append(px)
        fig.add_annotation(x=x, y=round(y, 4), yshift=round(px - (y - lo) / span * plot_px, 2),
                           text=f"<span style='color:{color}'>●</span> {name}", showarrow=False,
                           xanchor="left", xshift=6, font=dict(size=12, color=INK))


def _xrange(fig: go.Figure, xs: list[str]) -> None:
    """Pin a monthly date axis to the data (end labels sit in the right margin, outside the range)."""
    fig.update_xaxes(range=[f"{xs[0]}-01", f"{xs[-1]}-15"])


def _event(fig: go.Figure, x: str, text: str, y: float = 1.0, side: str = "right") -> None:
    fig.add_vline(x=x, line=dict(color=MUTED, width=1, dash="dot"))
    fig.add_annotation(x=x, y=y, yref="paper", text=text, showarrow=False, xanchor="left" if side == "right" else "right",
                       xshift=4 if side == "right" else -4, yanchor="top", font=dict(size=11, color=INK2),
                       bgcolor="rgba(255,255,255,0.85)")


# ------------------------------------------------------------------ figures

def fig_mad(c: dict) -> go.Figure:
    fig, ends = go.Figure(), {}
    for e in [*PEERS, "NEAR"]:
        s = c["mad"][e]
        xs, ys = sorted(s), [s[m] for m in sorted(s)]
        fig.add_trace(go.Scatter(x=xs, y=ys, name=e, mode="lines", line=dict(color=COLORS[e], width=3 if e == "NEAR" else 1.5),
                                 hovertemplate=f"{e}: %{{y:,}}<extra></extra>"))
        ends[e] = (xs, ys, COLORS[e])
    _end_labels(fig, ends)
    _xrange(fig, sorted(c["mad"]["NEAR"]))
    _event(fig, c["coverage"]["level_break_month"], "GH Archive coverage break", side="left")
    _layout(fig, "developers per month", margin=dict(l=52, r=132, t=TOP, b=76))
    fig.update_layout(updatemenus=[dict(type="buttons", direction="right", x=1, y=-0.17, xanchor="right", yanchor="top",
                                        showactive=True, font=dict(size=12),
                                        buttons=[dict(label="Linear", method="relayout", args=[{"yaxis.type": "linear"}]),
                                                 dict(label="Log", method="relayout", args=[{"yaxis.type": "log"}])])])
    return fig


def _peer_median(cur: dict) -> list[float]:
    out = []
    for i in range(len(cur["NEAR"])):
        v = sorted(cur[p][i] for p in PEERS)
        out.append((v[1] + v[2]) / 2)
    return out


def fig_retention(c: dict) -> go.Figure:
    cur = c["C1"]["curve"]
    ks = list(range(1, len(cur["NEAR"]) + 1))
    fig, ends = go.Figure(), {}
    for p in PEERS:
        fig.add_trace(go.Scatter(x=ks, y=cur[p], name=p, mode="lines", line=dict(color=PEER_C[p], width=1.2),
                                 hovertemplate=f"{p}: %{{y:.2%}}<extra></extra>"))
        ends[p] = (ks, cur[p], PEER_C[p])
    med = _peer_median(cur)
    fig.add_trace(go.Scatter(x=ks, y=med, name="Peer median", mode="lines", line=dict(color=INK, width=2, dash="dash"),
                             hovertemplate="Peer median: %{y:.2%}<extra></extra>"))
    fig.add_trace(go.Scatter(x=ks, y=cur["NEAR"], name="NEAR", mode="lines+markers", line=dict(color=NEAR_C, width=3),
                             marker=dict(size=8), hovertemplate="NEAR: %{y:.2%}<extra></extra>"))
    ends["Peer median"] = (ks, med, INK)
    ends["NEAR"] = (ks, cur["NEAR"], NEAR_C)
    _end_labels(fig, ends, min_gap_px=14)
    fig.add_vline(x=6, line=dict(color=MUTED, width=1, dash="dot"))
    fig.add_annotation(x=6, y=1, yref="paper", text="pre-registered test: month 6", showarrow=False, xanchor="left",
                       xshift=4, yanchor="top", font=dict(size=11, color=INK2))
    _layout(fig, "share still active")
    fig.update_xaxes(title="months after first activity", dtick=1, range=[0.7, 12.3])
    fig.update_yaxes(tickformat=".0%")
    fig.update_layout(margin=dict(l=52, r=132, t=TOP, b=52))
    return fig


def _c2_series(c: dict) -> tuple[list[str], dict[str, list[float]]]:
    mad, dep = c["mad"]["NEAR"], c["near_deploys"]
    months = [m for m in sorted(mad) if m >= c["C2"]["window"][0] and m in dep]
    base = [m for m in months if m.startswith("2022")]

    def idx(vals):
        b = sum(vals[m] for m in base) / len(base)
        return [round(vals[m] / b * 100, 3) for m in months]

    return months, {"Developers": idx(mad), "Deploys": idx({m: dep[m]["deploys"] for m in months}),
                    "Deployers": idx({m: dep[m]["unique_deployers"] for m in months})}


def fig_c2(c: dict) -> go.Figure:
    months, ser = _c2_series(c)
    style = {"Developers": (NEAR_C, 3, None), "Deploys": (ACCENT2, 1.5, None), "Deployers": (INK2, 1.5, "dot")}
    fig, ends = go.Figure(), {}
    for name, ys in ser.items():
        col, w, dash = style[name]
        fig.add_trace(go.Scatter(x=months, y=ys, name=name, mode="lines", line=dict(color=col, width=w, dash=dash),
                                 hovertemplate=f"{name}: %{{y:.0f}}<extra></extra>"))
        ends[name] = (months, ys, col)
    _end_labels(fig, ends, log=True)
    _xrange(fig, months)
    _layout(fig, "index (2022 average = 100)")
    fig.update_yaxes(type="log", tickvals=[3, 10, 30, 100, 300], ticktext=["3", "10", "30", "100", "300"])
    return fig


def fig_c3a(c: dict) -> go.Figure:
    a = c["C3a"]
    fig, ends = go.Figure(), {}
    for label, col, name in (("raw", NEAR_C, "Raw MAD"), ("adjusted", ACCENT2, "Adjusted")):
        s = a["series"][label]
        xs = sorted(s)
        ys = [s[m] for m in xs]
        fig.add_trace(go.Scatter(x=xs, y=ys, name=name, mode="lines", line=dict(color=col, width=2),
                                 hovertemplate=f"{name}: %{{y:.2f}}<extra></extra>"))
        ends[name] = (xs, ys, col)
        r = a[label]
        fig.add_shape(type="line", x0=a["pre"][0], x1=a["pre"][1], y0=r["pre_mean"], y1=r["pre_mean"],
                      line=dict(color=col, width=1, dash="dot"))
        fig.add_shape(type="line", x0=a["post"][0], x1=a["post"][1], y0=r["post_mean"], y1=r["post_mean"],
                      line=dict(color=col, width=1, dash="dot"))
    _end_labels(fig, ends)
    _xrange(fig, sorted(a["series"]["raw"]))
    thr = (1 + a["min_rise"]) * a["raw"]["pre_mean"]
    fig.add_shape(type="line", x0=a["post"][0], x1=a["post"][1], y0=thr, y1=thr, line=dict(color=INK, width=1.5, dash="dash"))
    fig.add_annotation(x=a["post"][0], y=thr, text=f"needed to hold: {thr:.2f}", showarrow=False, xanchor="left",
                       yanchor="bottom", font=dict(size=11, color=INK2))
    _event(fig, "2025-05", "2025-05: AI coding agents widely available", side="left")
    _layout(fig, "contracts per developer")
    return fig


def hackathon_bars(c: dict) -> str:
    """Hackathon cohort as plain HTML bars: responsive, and readable by screen readers as text."""
    b = c["C3b"]
    groups = [
        (f"Commit authors ({b['authors']:,})", NEAR_C,
         [("New to NEAR", b["authors_new"]), ("Returning (seen in GH Archive)", b["authors_prior_gha"]),
          ("Returning (seen only in their event feed)", b["authors_prior_feed_only"])]),
        (f"Commits with an AI co-author trailer ({b['ai_commits']:,} of {b['commits_non_bot']:,} non-bot commits)", ACCENT2,
         list(b["ai_by_tool"].items())),
    ]
    out = []
    for title, col, rows in groups:
        top = max(v for _, v in rows) or 1
        bars = "".join(
            f'<div class="bar"><span class="bl">{html.escape(k)}</span><span class="bt"><span class="bf" '
            f'style="width:{v / top * 100:.1f}%;background:{col}"></span><span class="bv">{v:,}</span></span></div>'
            for k, v in rows)
        out.append(f'<div class="bars"><p class="bh">{html.escape(title)}</p>{bars}</div>')
    return "".join(out)


def fig_coverage(c: dict) -> go.Figure:
    cov = c["coverage"]
    s = [r for r in cov["series"] if r["push_ratio"] is not None]
    xs = [r["month"] for r in s]
    fig, ends = go.Figure(), {}
    for key, name, col in (("push_ratio", "Pushes", NEAR_C), ("pr_ratio", "PRs", ACCENT2)):
        ys = [r[key] for r in s]
        fig.add_trace(go.Scatter(x=xs, y=ys, name=name, mode="lines", line=dict(color=col, width=2),
                                 hovertemplate=f"{name}: %{{y:.2f}}<extra></extra>"))
        ends[name] = (xs, ys, col)
    _end_labels(fig, ends)
    fig.add_hline(y=cov["threshold"], line=dict(color=INK, width=1, dash="dash"))
    fig.add_annotation(x=xs[0], y=cov["threshold"], text=f"{cov['threshold']:.0%} rule", showarrow=False, xanchor="left",
                       yanchor="top", font=dict(size=11, color=INK2))
    fig.add_vrect(x0=cov["last_good_month"], x1=xs[-1], fillcolor=GRID, opacity=0.7, line_width=0, layer="below")
    _event(fig, cov["last_good_month"], f"excluded after {cov['last_good_month']}")
    if cov["level_break_month"]:
        _event(fig, cov["level_break_month"], f"break {cov['level_break_month']}", y=0.2, side="left")
    if "2026-10" in xs:
        fig.add_annotation(x="2026-10", y=0.02, yref="paper", text="hackathon announced 2026-10-19", showarrow=False,
                           xanchor="right", yanchor="bottom", font=dict(size=11, color=INK2), bgcolor="rgba(255,255,255,0.85)")
    _xrange(fig, xs)
    _layout(fig, "ratio to trailing median")
    return fig


# ------------------------------------------------------------------ chart data (CSV)

def _csv(rows: list[list]) -> str:
    buf = io.StringIO()
    csv.writer(buf, lineterminator="\n").writerows(rows)
    return buf.getvalue()


def chart_csvs(c: dict) -> dict[str, str]:
    mad = c["mad"]
    cur = c["C1"]["curve"]
    med = _peer_median(cur)
    months, ser = _c2_series(c)
    dep, adj = c["near_deploys"], c["near_mad_adjusted"]
    a, b, cov = c["C3a"], c["C3b"], c["coverage"]
    return {
        "mad.csv": _csv([["month", *ECOSYSTEMS]] + [[m, *[mad[e].get(m, "") for e in ECOSYSTEMS]] for m in sorted(mad["NEAR"])]),
        "retention.csv": _csv([["k_months", *ECOSYSTEMS, "peer_median"]] +
                              [[k + 1, *[cur[e][k] for e in ECOSYSTEMS], round(med[k], 4)] for k in range(len(med))]),
        "c2_near.csv": _csv([["month", "near_mad", "near_mad_adjusted", "deploys", "unique_deployers", *[f"index_{n.lower()}" for n in ser]]] +
                            [[m, mad["NEAR"][m], adj[m], dep[m]["deploys"], dep[m]["unique_deployers"],
                              *[ser[n][i] for n in ser]] for i, m in enumerate(months)]),
        "c3a_contracts_per_mad.csv": _csv([["month", "raw", "adjusted"]] +
                                          [[m, a["series"]["raw"][m], a["series"]["adjusted"][m]] for m in sorted(a["series"]["raw"])]),
        "hackathon.csv": _csv([["group", "measure", "value"],
                               ["authors", "new_to_near", b["authors_new"]], ["authors", "returning_gh_archive", b["authors_prior_gha"]],
                               ["authors", "returning_feed_only", b["authors_prior_feed_only"]],
                               *[["ai_trailer_commits", k.lower(), v] for k, v in b["ai_by_tool"].items()],
                               ["commits", "non_bot", b["commits_non_bot"]], ["repos", "with_ai_trailer", b["ai_repos"]],
                               ["repos", "with_non_bot_commit", b["ai_repo_denominator"]]]),
        "gha_coverage.csv": _csv([["month", "push_events", "pr_events", "push_ratio", "pr_ratio", "good", "factor"]] +
                                 [[r["month"], r["push_events"], r["pr_events"], "" if r["push_ratio"] is None else r["push_ratio"],
                                   "" if r["pr_ratio"] is None else r["pr_ratio"], r["good"], r["factor"]] for r in cov["series"]]),
    }


# ------------------------------------------------------------------ HTML helpers

def _md_inline(s: str) -> str:
    s = html.escape(s, quote=False)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"`(.+?)`", r"<code>\1</code>", s)
    s = re.sub(r"\*(.+?)\*", r"<em>\1</em>", s)
    return s


def _table(headers: list[str], rows: list[list], caption: str = "") -> str:
    th = "".join(f'<th scope="col">{html.escape(str(h))}</th>' for h in headers)
    trs = "".join("<tr>" + "".join(f"<td>{html.escape(str(v))}</td>" for v in r) + "</tr>" for r in rows)
    cap = f"<caption>{html.escape(caption)}</caption>" if caption else ""
    return f'<div class="tw"><table>{cap}<thead><tr>{th}</tr></thead><tbody>{trs}</tbody></table></div>'


def _details(summary: str, inner: str) -> str:
    return f"<details><summary>{html.escape(summary)}</summary><div class=\"dbody\">{inner}</div></details>"


def _ul(xs: list[str]) -> str:
    return "<ul>" + "".join(f"<li>{_md_inline(x)}</li>" for x in xs) + "</ul>"


def _status_badge(s: str) -> str:
    key = s.split(" ")[0].lower()
    return f'<span class="st st-{key}">{html.escape(s)}</span>'


def _plot(fig: go.Figure, div_id: str) -> str:
    return fig.to_html(full_html=False, include_plotlyjs=False, div_id=div_id,
                       config={"displaylogo": False, "responsive": True, "displayModeBar": False})


def _chart(key: str, fig, c: dict, alt: str, source: str, csv_name: str,
           how: str = "", extra: str = "") -> str:
    title, sub = report.chart_titles(c)[key]
    how_html = f'<p class="how"><span>How to read this:</span> {_md_inline(how)}</p>' if how else ""
    return f"""<figure class="chart" aria-labelledby="t-{key}">
<h3 id="t-{key}">{html.escape(title)}</h3>
<p class="sub">{html.escape(sub)}</p>
<div role="img" aria-label="{html.escape(alt)}">{fig if isinstance(fig, str) else _plot(fig, "fig-" + key)}</div>
{how_html}<p class="src">Source: {html.escape(source)}. <a href="data/{csv_name}" download>Download data (CSV)</a></p>
{extra}</figure>"""


def _md_block(md: str) -> str:
    """Render the Methodology changes list from THESIS.md (numbered items, indented paragraphs and bullets)."""
    out, item, sub = [], None, None
    for line in md.splitlines():
        if re.match(r"^\d+\. ", line):
            if item is not None:
                out.append(item + ("</ul>" if sub else "") + "</li>")
            item, sub = "<li><p>" + _md_inline(line.split(". ", 1)[1]) + "</p>", False
        elif line.startswith("   - ") and item is not None:
            item += ("" if sub else "<ul>") + "<li>" + _md_inline(line[5:]) + "</li>"
            sub = True
        elif line.startswith("   ") and line.strip() and item is not None:
            item += ("</ul>" if sub else "") + "<p>" + _md_inline(line.strip()) + "</p>"
            sub = False
        elif line.strip() and item is None:
            out.append("<p>" + _md_inline(line.strip()) + "</p>")
    if item is not None:
        out.append(item + ("</ul>" if sub else "") + "</li>")
    paras = [o for o in out if o.startswith("<p>")]
    items = [o for o in out if o.startswith("<li>")]
    return "".join(paras) + "<ol>" + "".join(items) + "</ol>"


def _methodology_changes() -> str:
    t = (ROOT / "THESIS.md").read_text(encoding="utf-8")
    sec = t.split("## Methodology changes\n", 1)[1].split("<!-- BEGIN GENERATED: results", 1)[0]
    return _md_block(sec)


# ------------------------------------------------------------------ page

def build_html(c: dict) -> str:
    v, b, a, g, cov = c["verdict"], c["C3b"], c["C3a"], c["C2"], c["coverage"]
    score = "".join(
        f'<tr class="{"sub" if r["indent"] else ""}"><th scope="row">{r["id"]}</th><td>{html.escape(r["claim"])}</td>'
        f'<td>{html.escape(r["kill"])}</td><td>{html.escape(r["measured"])}</td>'
        f'<td>{_status_badge(r["status"])}{"<div class=note>" + html.escape(r["note"]) + "</div>" if r["note"] else ""}</td></tr>'
        for r in report.scorecard(c))
    lag_rows = [[lag, report.pval(g["raw"]["deploys"]["granger_p"][str(lag)]), report.pval(g["raw"]["unique_deployers"]["granger_p"][str(lag)]),
                 report.pval(g["adjusted"]["deploys"]["granger_p"][str(lag)]), report.pval(g["adjusted"]["unique_deployers"]["granger_p"][str(lag)]),
                 f"{g['raw']['deploys']['ccf'][str(lag)]:+.2f}", report.pval(g["raw"]["deploys"]["reverse_granger_p"][str(lag)])]
                for lag in range(1, g["max_lag"] + 1)]
    lag_tbl = _table(["Lag (months)", "p, deploys (raw)", "p, deployers (raw)", "p, deploys (adjusted)", "p, deployers (adjusted)",
                      "Correlation: developers → deploys (lag k)", "Reverse p (exploratory)"], lag_rows,
                     f"Granger p-values, {g['window'][0]} to {g['window'][1]}; significant only below "
                     f"{report.alpha_(g['raw']['deploys']['bonferroni_alpha'])}")
    cov_tbl = _table(["Month", "Push events", "PR events", "Push ratio", "PR ratio", "Good month"],
                     [[r["month"], f"{r['push_events']:,}", f"{r['pr_events']:,}",
                       "" if r["push_ratio"] is None else f"{r['push_ratio']:.2f}",
                       "" if r["pr_ratio"] is None else f"{r['pr_ratio']:.2f}", "yes" if r["good"] else "no"] for r in cov["series"]])
    k6 = c["C1"]["by_k"]["6"]
    titles = report.chart_titles(c)
    og_desc = report.one_liner(c)
    og_img = (SITE / "og.png").exists()
    og_img_tags = (f'<meta property="og:image" content="{SITE_URL}og.png">\n<meta name="twitter:image" content="{SITE_URL}og.png">\n'
                   if og_img else "")
    cite = (f"{AUTHOR} (2026). Builders First: a NEAR investment thesis from developer data. NEAR HACKATHON. "
            f"{REPO_URL} (data as of {c['data_as_of']['hackathon_fetched_at'][:10]}).")

    charts = [
        _chart("mad", fig_mad(c), c, titles["mad"][0] + ". Line chart of monthly active developers for NEAR, Solana, Sui, Aptos and Base.",
               "Open Dev Data by Electric Capital (repo lists); GH Archive; my analysis", "mad.csv",
               "the Log button puts the five ecosystems on a ratio scale, which makes the smaller ones easier to compare."),
        _chart("retention", fig_retention(c), c,
               titles["retention"][0] + ". Retention curves from 1 to 12 months for NEAR, each peer and the peer median.",
               "Open Dev Data by Electric Capital; GH Archive; my analysis", "retention.csv",
               "each point is the share of developers still active k months after their first active month. Higher is better. "
               "The pre-registered test is at month 6."),
        _chart("c2", fig_c2(c), c, titles["c2"][0] + ". Three indexed monthly lines for NEAR developers, contracts deployed and unique deployers.",
               "Open Dev Data; GH Archive; NEAR public BigQuery dataset; my analysis", "c2_near.csv",
               "all three lines are scaled so their 2022 average is 100. If developers led usage, moves in the blue line would "
               "show up in the other two a few months later. The table gives the test for each lag.",
               _details("Granger test results by lag", lag_tbl)),
        _chart("c3a", fig_c3a(c), c, titles["c3a"][0] + ". Monthly contracts per developer, raw and coverage-adjusted, with period means and the threshold.",
               "Open Dev Data; GH Archive; NEAR public BigQuery dataset; my analysis", "c3a_contracts_per_mad.csv",
               "each point divides a month's contract deployments by that month's active developers. The claim needed the "
               "average from 2025 to clear the dashed line."),
        _chart("hackathon", hackathon_bars(c), c, titles["hackathon"][0] + ". Bar charts of authors by prior NEAR activity and AI-trailer commits by tool.",
               "nearhunt.xyz; GitHub REST API; Open Dev Data; GH Archive; my analysis", "hackathon.csv"),
        _chart("coverage", fig_coverage(c), c, titles["coverage"][0] + ". Push and pull-request volume ratios over time with the 80% rule and the excluded period shaded.",
               "GH Archive; my analysis", "gha_coverage.csv",
               f"each line compares a month's GH Archive event count with the median of the 12 months before it. Below the "
               f"dashed {cov['threshold']:.0%} line a month is unreliable. Shaded months are excluded.",
               _details("Full GH Archive coverage table", cov_tbl)),
    ]

    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light">
<title>Builders First</title>
<meta name="description" content="{html.escape(og_desc)}">
<meta name="author" content="{AUTHOR}">
<meta property="og:type" content="article">
<meta property="og:title" content="Builders First: a NEAR investment thesis from developer data">
<meta property="og:description" content="{html.escape(og_desc)}">
<meta property="og:url" content="{SITE_URL}">
<meta name="twitter:card" content="{'summary_large_image' if og_img else 'summary'}">
<meta name="twitter:title" content="Builders First: a NEAR investment thesis from developer data">
<meta name="twitter:description" content="{html.escape(og_desc)}">
{og_img_tags}<script src="{PLOTLY_CDN}"></script>
<style>
:root {{ --surface:{SURFACE}; --ink:{INK}; --ink2:{INK2}; --muted:{MUTED}; --grid:{GRID}; --accent:#1c5cab; }}
* {{ box-sizing:border-box; }}
body {{ margin:0; background:var(--surface); color:var(--ink); font:17px/1.6 {FONT}; }}
main {{ max-width:960px; margin:0 auto; padding:32px 16px 72px; }}
.prose, header, section > p, section > ul, section > ol {{ max-width:68ch; }}
h1 {{ font-size:34px; line-height:1.15; margin:0; letter-spacing:-0.01em; }}
h2 {{ font-size:22px; margin:56px 0 12px; }}
h3 {{ font-size:18px; margin:0; line-height:1.35; }}
.subtitle {{ font-size:19px; color:var(--ink2); margin:8px 0 6px; }}
.byline, .asof, .meta {{ font-size:14px; color:var(--ink2); margin:4px 0; }}
.verdict {{ display:flex; flex-wrap:wrap; gap:10px; align-items:baseline; margin:20px 0 6px; }}
.badge {{ display:inline-block; padding:6px 14px; border-radius:6px; font-weight:700; font-size:18px; background:#f3f2ee; border:2px solid var(--ink); }}
.exec {{ border:2px solid var(--ink); border-radius:8px; padding:4px 20px 8px; margin-top:28px; max-width:68ch; background:#fafaf8; }}
.exec h2 {{ margin:14px 0 8px; font-size:20px; }}
.exec dl {{ margin:0; display:grid; grid-template-columns:max-content 1fr; gap:6px 14px; }}
.exec dt {{ font-weight:700; }} .exec dd {{ margin:0; }}
@media (max-width: 600px) {{ .exec dl {{ grid-template-columns:1fr; }} .exec dd {{ margin-bottom:6px; }} }}
.video {{ font-size:15px; margin:6px 0; }} .video a {{ font-weight:600; }}
.findings li {{ margin:10px 0; }}
.tw {{ overflow-x:auto; -webkit-overflow-scrolling:touch; }}
table {{ border-collapse:collapse; width:100%; font-size:14px; }}
caption {{ text-align:left; color:var(--ink2); font-size:13px; padding:4px 0 8px; }}
th, td {{ text-align:left; vertical-align:top; padding:8px 10px; border-bottom:1px solid var(--grid); }}
thead th {{ color:var(--ink2); font-weight:600; }}
tbody th {{ font-weight:600; white-space:nowrap; }}
tr.sub th {{ padding-left:26px; }}
.note {{ color:var(--ink2); font-size:13px; margin-top:4px; }}
.st {{ font-weight:700; padding:1px 6px; border-radius:4px; white-space:nowrap; }}
.st-holds::before {{ content:"✓ "; }} .st-killed::before {{ content:"✕ "; }} .st-fragile::before {{ content:"~ "; }}
.st-holds {{ background:#e3f1e3; color:#0b5d0b; }} .st-killed {{ background:#f8e1e0; color:#9b1c1b; }} .st-fragile {{ background:#fbf0d6; color:#6b4700; }}
figure.chart {{ margin:40px 0 0; padding:0; }}
.sub {{ color:var(--ink2); font-size:14px; margin:4px 0 8px; }}
.how, .src {{ font-size:14px; color:var(--ink2); margin:6px 0; max-width:68ch; }}
.bars {{ margin:8px 0 18px; max-width:640px; }} .bh {{ font-weight:600; font-size:15px; margin:0 0 6px; }}
.bar {{ display:grid; grid-template-columns:minmax(120px, 38%) 1fr; gap:10px; align-items:center; margin:5px 0; font-size:14px; }}
.bt {{ display:flex; align-items:center; gap:6px; }} .bf {{ display:block; height:18px; border-radius:0 4px 4px 0; min-width:2px; }}
.bv {{ font-variant-numeric:tabular-nums; color:var(--ink); }}
.how span {{ font-weight:600; color:var(--ink); }}
details {{ margin:10px 0; border-top:1px solid var(--grid); padding-top:8px; }}
summary {{ cursor:pointer; color:var(--accent); font-weight:600; font-size:15px; }}
summary:focus-visible, a:focus-visible {{ outline:3px solid var(--accent); outline-offset:2px; }}
.dbody {{ font-size:15px; max-width:68ch; }} .dbody .tw {{ max-width:none; }}
.dbody ol li {{ margin-bottom:10px; }}
code {{ background:#f1f0ec; padding:1px 4px; border-radius:3px; font-size:0.88em; overflow-wrap:anywhere; }}
pre {{ background:#f1f0ec; padding:12px; border-radius:6px; overflow-x:auto; font-size:14px; white-space:pre-wrap; }}
footer {{ margin-top:56px; color:var(--ink2); font-size:14px; border-top:1px solid var(--grid); padding-top:14px; max-width:68ch; }}
a {{ color:var(--accent); }}
@media (max-width: 600px) {{
  body {{ font-size:16px; }} h1 {{ font-size:28px; }} h2 {{ font-size:20px; margin-top:44px; }}
  .subtitle {{ font-size:17px; }} th, td {{ padding:6px 6px; }}
}}
</style></head>
<body><main>
<header>
<h1>Builders First</h1>
<p class="subtitle">A NEAR investment thesis built from developer data instead of fees or price.</p>
<p class="byline">By <a href="{AUTHOR_URL}">{AUTHOR}</a> · NEAR HACKATHON, November 2026</p>
<p class="asof">{_md_inline(report.data_short(c))} {_md_inline(report.data_why(c))}</p>
<p class="video"><a href="{report.VIDEO_URL}">Demo video (1:34)</a></p>
<div class="verdict"><span class="badge">Verdict: {v}</span><span>{c['claims_holding']} of 3 top-level claims hold</span></div>
<p class="meta">{_md_inline(report.VERDICT_RULE)}</p>
<p class="meta">{_md_inline(report.PREREG)}</p>
</header>

<section class="exec" aria-labelledby="h-exec">
<h2 id="h-exec">Executive summary for judges</h2>
<dl>{"".join(f"<dt>{html.escape(k)}</dt><dd>{_md_inline(v)}</dd>" for k, v in report.executive_summary(c))}</dl>
<p class="meta">Not investment advice.</p>
</section>

<section aria-labelledby="h-find">
<h2 id="h-find">Headline findings</h2>
<ul class="findings">{"".join(f"<li>{_md_inline(x)}</li>" for x in report.headlines(c))}</ul>
</section>

<section aria-labelledby="h-impl">
<h2 id="h-impl">Investment implication</h2>
<p>{" ".join(_md_inline(x) for x in report.implication(c))}</p>
</section>

<section aria-labelledby="h-score">
<h2 id="h-score">What I tested</h2>
<p>{_md_inline(report.one_liner(c))}</p>
<div class="tw"><table><caption>Pre-registered claims, kill criteria and results</caption><thead><tr><th scope="col">Claim</th><th scope="col">What it says</th><th scope="col">Kill criterion</th><th scope="col">Measured</th><th scope="col">Status</th></tr></thead><tbody>{score}</tbody></table></div>
</section>

<section aria-labelledby="h-ev">
<h2 id="h-ev">The evidence</h2>
{"".join(charts)}
</section>

<section aria-labelledby="h-flip">
<h2 id="h-flip">What would change the verdict</h2>
<p>Each line gives the threshold that would flip a claim on the next rebuild, so the thesis can be re-checked as new data arrives.</p>
{_ul(report.flips(c))}
</section>

<section aria-labelledby="h-bear">
<h2 id="h-bear">Bear case</h2>
{_ul(report.bear_case(c))}
</section>

<section aria-labelledby="h-more">
<h2 id="h-more">Method and caveats</h2>
{_details("Method in brief", _ul(report.method_brief(c) + ["Data as of: " + report.data_as_of(c)]))}
{_details("Methodology changes, with dates and commit hashes", _methodology_changes())}
{_details("Exploratory results (not pre-registered)", _ul(report.exploratory(c)))}
{_details("Limitations", _ul(report.limitations(c)))}
</section>

<section aria-labelledby="h-rerun">
<h2 id="h-rerun">How to re-run</h2>
<p>Everything on this page rebuilds offline from the cached data in the repo:</p>
<pre><code>git clone {REPO_URL}.git
cd builders-first
make setup &amp;&amp; make all</code></pre>
<p>To refresh the data from the sources, add GitHub and Google Cloud credentials to <code>.env</code> and run <code>make setup-data &amp;&amp; make data</code>. Details are in the <a href="{REPO_URL}#readme">README</a>.</p>
</section>

<section aria-labelledby="h-cite">
<h2 id="h-cite">Cite this</h2>
<p class="prose">{html.escape(cite)}</p>
</section>

<section aria-labelledby="h-about">
<h2 id="h-about">About the author</h2>
<p>I am <a href="{AUTHOR_URL}">{AUTHOR}</a>. I designed and directed this project and made its methodological decisions; AI coding agents (Claude Code) wrote most of the code under my direction, and I reviewed each phase.</p>
</section>

<footer>
<p>Source: Open Dev Data by Electric Capital — <a href="https://github.com/electric-capital/open-dev-data">https://github.com/electric-capital/open-dev-data</a> (CC BY 4.0). Also GH Archive, the NEAR public BigQuery dataset (<code>bigquery-public-data.crypto_near_mainnet_us</code>), nearhunt.xyz, nearhackathon.com and the GitHub REST API.</p>
<p>Every number on this page is generated from <code>data/cache/claims.json</code> in the <a href="{REPO_URL}">repository</a>. Built during NEAR HACKATHON, November 2026. Not investment advice.</p>
</footer>
</main>
<script>
// Narrow screens: give the plot area more room by shrinking chart margins and text.
if (window.innerWidth < 560) {{
  document.querySelectorAll(".plotly-graph-div").forEach(function (d) {{
    Plotly.relayout(d, {{"margin.l": 40, "margin.r": 96, "font.size": 11}});
  }});
}}
</script>
</body></html>
"""


def main() -> None:
    c = report.load_claims()
    SITE.mkdir(exist_ok=True)
    CHART_DIR.mkdir(exist_ok=True)
    (SITE / "data").mkdir(exist_ok=True)
    for name, text in chart_csvs(c).items():
        for d in (CHART_DIR, SITE / "data"):
            (d / name).write_text(text, encoding="utf-8", newline="\n")
    (SITE / "index.html").write_text(build_html(c), encoding="utf-8", newline="\n")
    for path, text in report.render_docs(c).items():
        (ROOT / path).write_text(text, encoding="utf-8", newline="\n")
    print("site/index.html and chart CSVs written; THESIS.md and README.md generated blocks updated")


if __name__ == "__main__":
    main()
