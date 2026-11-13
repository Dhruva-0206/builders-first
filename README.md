# Builders First

A NEAR investment thesis from developer data, built during NEAR HACKATHON (Investment Thesis track).

<!-- BEGIN GENERATED: one-liner (do not edit by hand; `make site` rewrites this) -->
We tested three pre-registered claims about NEAR's developer base. One holds, barely; two fail. The surprise: almost every hackathon builder is new to NEAR (97%), and at least a third of their repos show AI co-authorship (34%), but developers follow usage rather than lead it.
<!-- END GENERATED: one-liner -->

Every NEAR thesis asks whether fees reach the token. This one asks the earlier question: are developers coming to NEAR, staying, and shipping, and does that lead onchain usage? Three claims, each with a kill criterion, were committed before any data was pulled ([THESIS.md](THESIS.md), see its git history) and are rebuilt from public data with one command.

## Try it in 2 minutes

1. `git clone https://github.com/Dhruva-0206/builders-first.git && cd builders-first && make setup && make all`
   → the claims are recomputed from `data/cache/`, `site/index.html` is written, and pytest ends with `N passed`. No credentials or network needed beyond `pip install`.
2. Open `site/index.html` in a browser (or the hosted copy: https://dhruva-0206.github.io/builders-first/)
   → the verdict badge, the claims scorecard, six charts (developers by ecosystem, retention, developers vs deployments, output per developer, hackathon cohort, GH Archive coverage) and a table view under each chart.
3. Optional, needs credentials: `make setup-data && make data` (with `GITHUB_TOKEN`, `GCP_PROJECT`, `GOOGLE_APPLICATION_CREDENTIALS` in `.env`, see `.env.example`), then `make all`
   → rebuilds every cached file from the sources; `git diff data/cache` shows what changed.

CI ([`.github/workflows/rebuild.yml`](.github/workflows/rebuild.yml)) runs `make setup && make all` on a clean Ubuntu runner on every push and fails if any committed output (claims, site, generated sections of this README and THESIS.md) differs from a fresh rebuild.

On Windows without GNU make, the same targets run as `python -m builders_first.claims`, `python -m builders_first.build_site` and `python -m pytest` with `PYTHONPATH=src`.

## Claims and verdict

<!-- BEGIN GENERATED: claims (do not edit by hand; `make site` rewrites this) -->
**Verdict: Neutral** (1 of 3 pre-registered claims hold)

| Claim | Kill criterion | Measured | Status |
|---|---|---|---|
| **C1** New NEAR developers retain at least as well as peers (Solana, Sui, Aptos, Base) | NEAR 6-month retention below peer median | 12.0% vs peer median 12.0% | **HOLDS (statistical tie)**<br>Statistical tie: margin +0.01 pp, NEAR 95% CI 11.3%–12.8% contains the peer median. Smoothed 6-month: 17.9% vs 18.7% (fails). 12-month: 7.9% vs 9.0% (fails). |
| **C2** NEAR monthly active developers lead contract deployments by 1–6 months | No lag with p < 0.0083 (0.05 / 6, Bonferroni) | min Granger p 0.0907 raw / 0.124 adjusted (Bonferroni threshold 0.0083) | **KILLED**<br>Raw and coverage-adjusted MAD agree. |
| **C3** AI-era funnel: (a) and (b) both hold | (a) or (b) killed | see C3a, C3b | **KILLED** |
| &nbsp;&nbsp;↳ **C3a** Contracts deployed per MAD rose since 2025 | Post-2025 mean not more than 1.10× the 2023–24 mean | contracts per MAD 0.67x pre-period (raw), 0.56x (coverage-adjusted) | **KILLED**<br>Mann-Whitney p = 0.705 (raw), not part of the criterion. |
| &nbsp;&nbsp;↳ **C3b** A majority of NEAR HACKATHON authors are new to NEAR | New-to-NEAR authors < 50% (stricter of two shares) | 97.2% of 319 authors; 97.4% excluding 11 with truncated event feeds | **HOLDS**<br>AI co-authored: ≥41.4% of commits, 34.2% of repos. |
<!-- END GENERATED: claims -->

Headline findings, the conditions that would flip each claim, an exploratory section, the bear case and limitations are in [THESIS.md](THESIS.md) and on the dashboard. All of it is generated from [`data/cache/claims.json`](data/cache/claims.json) by [`src/builders_first/report.py`](src/builders_first/report.py); `tests/test_generated.py` fails if any figure in this README or THESIS.md differs from a fresh computation.

## Data sources

| Source | Used for | Produced by |
|---|---|---|
| **Open Dev Data by Electric Capital** — https://github.com/electric-capital/open-dev-data (CC BY 4.0) | Repo lists for NEAR, Solana, Sui, Aptos, Base, sub-ecosystems included | `ingest_ecosystems.py` → `data/cache/repos_*.csv` |
| GH Archive (`githubarchive.month.*`, `githubarchive.day.*` on BigQuery) | Monthly active developers, cohorts, retention, coverage checks | `ingest_bigquery.py` + `sql/` → `data/cache/activity.csv.gz`, `gha_*.csv` |
| NEAR public dataset `bigquery-public-data.crypto_near_mainnet_us.transaction_actions` | Monthly contract deployments and unique deployers | `sql/near_deploys.sql` → `data/cache/near_deploys_monthly.csv` |
| nearhunt.xyz `/api/projects`, nearhackathon.com `/api/projects` | Hackathon submissions and repo links | `ingest_hackathon.py` → `data/cache/hackathon_*.csv` |
| GitHub REST API | Hackathon commits since 2026-10-19, authors' public event feeds | `ingest_github.py` → `data/cache/hackathon_commits.csv`, `hackathon_authors.csv` |

Source: Open Dev Data by Electric Capital — https://github.com/electric-capital/open-dev-data

GitHub logins are stored only as SHA-256 prefixes (`src/builders_first/ids.py`); `tests/test_privacy.py` checks that no logins or email addresses appear in `data/cache/` or `site/`. BigQuery costs of every query are logged in [`sql/COSTS.md`](sql/COSTS.md).

## Method summary

- **Monthly active developer (MAD):** a distinct non-bot GitHub login with at least one push or pull-request event on an ecosystem's repos in a calendar month.
- **C1:** pooled retention of monthly new-developer cohorts (2022-01 on) at 3, 6 and 12 months; NEAR vs the median of the four peers.
- **C2:** Granger causality from NEAR MAD to deployments on log-differenced monthly series, lags 1–6, Bonferroni-corrected, plus ADF checks, cross-correlations and an out-of-sample forecast test.
- **C3a:** contracts deployed per MAD, 2025 onward vs 2023–24. **C3b:** hackathon commit authors with no prior NEAR activity in GH Archive or in their GitHub event feed; AI co-author trailers detected by regex.
- **Data quality:** GH Archive volume breaks in 2025 and collapses in late 2026. A coded rule ends the series early, and C2 and C3a are also computed on coverage-adjusted developer counts; claims that disagree between the two are reported as FRAGILE.

Full definitions and every methodology change, with dates and commit hashes, are in [THESIS.md](THESIS.md).

## Limitations

Open-source activity only; repos missing from Open Dev Data are invisible; GH Archive coverage breaks (see above); AI-trailer counts are a lower bound (trailers can be stripped, and this repo strips its own). The full list is generated in THESIS.md.

## Libraries and tools

pandas, NumPy, SciPy, statsmodels, Plotly (Python, and plotly.js from its CDN on the page), requests, python-dotenv, pytest, google-cloud-bigquery, open-dev-data. Code was written with AI coding assistants (Claude Code).

## Built at NEAR HACKATHON

Built during NEAR HACKATHON (Nov 2026); all code in this repository was written in the hackathon window.

## Also by this team

[Bet on Beliefs](https://github.com/Dhruva-0206/bet-on-beliefs): a futarchy-governed memecoin treasury on NEAR testnet, also built at NEAR HACKATHON.

## License

MIT, see [LICENSE](LICENSE). Open Dev Data is CC BY 4.0 (attribution above).
