# Builders First: a NEAR investment thesis from developer data

By Dhruva Somen Chakrabarty. NEAR HACKATHON, November 2026.

Status: results in. I pre-registered claims C1 to C3, meaning I wrote each one down with the result that would disprove it and committed them in `333ea0c` before pulling any data. Their text below is unchanged: `git log -p THESIS.md` shows it, and `tests/test_style.py` checks it against that commit. I added C3a's >10% threshold later, in `4d4fc58`, after I had seen the deployment series (Methodology changes, item 6). Code generates the headline findings, results, verdict, bear case and limitations from `data/cache/claims.json`. I logged every change to method below, with its date and reason.

## Headline findings

Generated from `data/cache/claims.json`. The pre-registered claims further down are unchanged.

<!-- BEGIN GENERATED: headlines (do not edit by hand; `make site` rewrites this) -->
- 97.2% (310/319) of NEAR HACKATHON commit authors had no prior public activity in NEAR repos tracked by Open Dev Data, an upper bound on newness. Work in repos the taxonomy does not list is invisible to this check.
- At least 41.4% of hackathon commits are AI co-authored (6,604/15,960 non-bot commits), and 34.2% of repos (125/366 repos with at least one non-bot commit) contain at least one such commit. Both are lower bounds: trailers are easy to strip, and this repo strips its own.
- Developers do not lead onchain usage. A Granger test asks whether past developer counts help predict deployments; the best result was p = 0.091, against a Bonferroni threshold of 0.0083 (0.05 split across the 6 lags tested). The reverse direction, deployments leading developers, is suggestive (p = 0.012 to 0.026 at lags 2–6) but not significant, so I treat it as exploratory.
- Output per developer fell to 0.56 to 0.67× its 2023–24 level, measured as contracts deployed per monthly active developer (MAD: a GitHub account that pushed code or opened a pull request in an ecosystem repo that month).
<!-- END GENERATED: headlines -->

## Investment implication

<!-- BEGIN GENERATED: implication (do not edit by hand; `make site` rewrites this) -->
Developer data alone does not support a bull case for NEAR today. New developers stay only at par with peers (6-month retention 12.04% vs 12.03%), developers do not lead onchain usage (C2 killed), and output per developer fell to 0.56 to 0.67× its 2023–24 level. A bull case would have to rest on usage-side evidence, such as NEAR Intents volume and fees, which I did not measure here. Developer momentum does not carry it. The one leading indicator worth watching is the AI-assisted newcomer wave: 97.2% of hackathon commit authors (310/319) were new to tracked NEAR repos, and at least 34.2% of repos (125/366) show AI co-authorship. If those builders ship to mainnet and contracts per developer rises above 1.66 (the C3a flip threshold; 1.01 raw and 0.84 adjusted today), the verdict moves toward bullish. This is not investment advice.
<!-- END GENERATED: implication -->

<!-- pre-registration: start (verbatim from 333ea0c; not restyled) -->
## Thesis

Developers come before usage. If NEAR is gaining and keeping developers, and those developers lead onchain activity, that is an early sign of long-term demand for blockspace, and so for the token, that fee data alone shows only later. Most NEAR theses start from fees. This one starts one step earlier.

## Pre-registered claims

### C1 — Retention

New NEAR developers retain at least as well as the median of a peer set at 3, 6 and 12 months.

- **Peer set:** Solana, Sui, Aptos, plus one EVM L2 (Base) if present in the Open Dev Data taxonomy.
- **New developer:** first calendar month a GitHub login is active in the ecosystem's repos (history from 2019-01 to avoid left-censoring).
- **Retention at k months:** share of a monthly new-developer cohort active in the ecosystem in month +k. Cohorts from 2022-01 to the latest month with full k-month follow-up; pooled across cohorts (active / cohort size).
- **Peer median:** median of the peers' retention at each k.
- **Kill criterion:** NEAR's 6-month retention is below the peer median.

### C2 — Developers lead usage

NEAR monthly active developers (MAD) lead NEAR mainnet contract deployments (count, and unique deployer accounts) by 1–6 months.

- **Method:** monthly series, log-differenced; ADF stationarity check; cross-correlation by lag; Granger causality (statsmodels) MAD → deployments for lags 1–6; out-of-sample check (fit through 2024-12, test 2025-01 onward) comparing a model with lagged MAD to one without.
- **Kill criterion:** no lag 1–6 is significant at p < 0.05 after Bonferroni correction across the lags tested (for either deployment series).

### C3 — The AI-era funnel

(a) Output per developer — contracts deployed per monthly active developer — has risen since 2025 even as commit counts fell.
(b) In the NEAR HACKATHON cohort, a majority of repo authors had no public NEAR-ecosystem GitHub activity before 2026-10-19, and a measurable share of hackathon commits carry AI co-author trailers.

- **(a) measure:** mean monthly contracts-deployed-per-MAD in 2025-01 onward vs. 2023-01 to 2024-12. 2025-05 (general availability of major AI coding agents) is marked as an annotation only, not a causal claim.
- **(b) measure:** for each hackathon repo on GitHub (from the nearhunt.xyz project list), commit authors since 2026-10-19; an author is *new* if their login does not appear in NEAR-ecosystem GH Archive activity before 2026-10-19. AI trailers: case-insensitive regex `co-authored-by:.*(claude|anthropic|codex|openai|copilot|cursor|devin|gemini|aider)` or `generated with \[?claude code` in the commit message. Report share of commits and share of repos with at least one match. This is a lower bound: trailers can be stripped.
- **Kill criterion:** (a) output per developer is flat or down, or (b) new-to-NEAR authors are fewer than 50% of the cohort.

### Verdict rule

Computed by code: **Bull** if at least 2 claims hold, **Neutral** if 1, **Bear** if 0. The bear case is printed whatever the verdict.
<!-- pre-registration: end -->

## Data sources

- Source: Open Dev Data by Electric Capital — https://github.com/electric-capital/open-dev-data (repo-to-ecosystem taxonomy, CC BY 4.0).
- GH Archive on BigQuery: a public record of GitHub events (pushes, pull requests and more), one table per month.
- `bigquery-public-data.crypto_near_mainnet_us`: NEAR mainnet transactions and actions.
- nearhunt.xyz and nearhackathon.com public project APIs: hackathon submissions and their repo links.
- GitHub REST API: commits in hackathon repos since 2026-10-19, and authors' public event feeds.

## Methodology changes

I logged these in the order I made them. Where the order of a decision and the data matters, I give commit hashes so it can be checked with `git log`.

1. Ecosystem names (2026-11-12). Open Dev Data calls them `NEAR`, `Solana`, `Sui`, `Aptos` and `Base`; I included all sub-ecosystems. Base is in the taxonomy, so it is the EVM L2 peer. The taxonomy is pinned to the commit recorded in `data/cache/ecosystems_meta.json`. I call the package's `taxonomy` module directly, which runs the same code as `open-dev-data export`.
2. GH Archive window (2026-11-12). I started the history at 2021-01, not 2019-01, to fit the BigQuery sandbox budget (dry-run costs are in `sql/COSTS.md`). A developer active before 2021 who returns in 2022 can therefore count as new in early cohorts. Cohorts still start at 2022-01, so each has at least 12 months of look-back.
3. Developer identity and events (2026-11-12). A developer is the GH Archive `actor.login` of a `PushEvent` or `PullRequestEvent` (any action) on an ecosystem repo. Counting merged pull requests only would mean reading the large `payload` column for every month, which the budget did not allow. Electric Capital counts original commit authors, so my absolute numbers differ from its Developer Report, while trends are comparable. I removed bot logins by pattern (`[bot]`, `-bot`, dependabot, github-actions, renovate).
4. NEAR deployments (2026-11-12). Deployments come from `transaction_actions` (`action_kind = 'DEPLOY_CONTRACT'`, signed directly by an account), not `receipt_actions`, which would cost about 3× more to scan. This excludes contracts created by factory contracts, and I chose that on purpose, not only to save cost. A transaction-level deployment is an account shipping code it chose to ship, which is a developer action. Factory deployments (DAO, token and meme-coin factories) are mostly end users pressing a button in someone else's app. They measure that app's popularity, and one viral factory can add thousands of deployments in a month. The bias runs the other way too. The series undercounts teams that deploy through their own factory or a deployer contract (some upgrade or multisig flows), and it counts redeploys of the same contract separately. If developers shifted toward factory-style deployment over time, the series would fall even if output did not. Unique deployers are distinct `signer_account_id` values. The NEAR BigQuery dataset was current (latest `block_date` 2026-11-12 at fetch time), so I needed no RPC back-fill.
5. Incomplete months (2026-11-12). The current calendar month is partial, so I excluded it from every monthly series and from cohort follow-up.
6. C3a threshold (2026-11-12). The pre-registration did not define "flat" numerically. I fixed it: C3a holds only if mean monthly contracts per MAD from 2025-01 is more than 10% above the 2023-01 to 2024-12 mean. I report a Mann-Whitney test alongside, but it is not part of the criterion.
   Order of events: I committed the threshold in `4d4fc58` (2026-11-12 20:01:34 UTC). That was before the developer-activity data commit `3cefe2f` (20:04:15 UTC) and before I had computed or looked at any MAD figure. It was not before all data existed. I had already downloaded and printed the NEAR deployment series (the numerator, `48ddb53`), and four of the six GH Archive raw chunks (2021 to 2024) had been written to `data/raw/` about a minute earlier, unopened. The 2025 and 2026 chunks, which hold the whole post-period, arrived after the commit.
7. C3b cohort (2026-11-12). Repos come from nearhunt.xyz entries that link a GitHub repository. Commits are from each repo's default branch, from 2026-10-19T00:00Z to the fetch time. Commits whose author has no linked GitHub account are left out of author counts but kept in the AI-trailer share. Prior NEAR activity is defined in item 9. The committed activity cache stores logins as unsalted SHA-256 prefixes, and I compare those hashes.
8. GH Archive coverage breaks (2026-11-12, found after download). GH Archive's own volume is not stable. An event-type breakdown (`data/cache/gha_type_volume.csv`, `data/cache/gha_pushpr_volume.csv`) shows push volume falling about 30% in 2025-06 and staying lower, and pull-request volume collapsing from 2026-03 to 2026-08 before pushes also fall in 2026-09. The breaks are in the source and hit every ecosystem, so they lower measured developer counts with no change in real activity. I responded in code (`stats.py`) in two ways.
   - Cutoff. A month is good if push and pull-request volume are both at least 80% of the median of the 12 months before it. Series based on GH Archive end at the month before the final run of failing months (`stats.last_good_month`), and later months are excluded from MAD, retention follow-up, C2 and C3a. I chose the 80% threshold after looking at the GH Archive volume series only, not at any ecosystem's numbers. The dashboard charts push and pull-request volume with the cutoff marked.
   - Coverage-adjusted MAD. A failing month before the cutoff marks a level break. From that break on, I divide monthly MAD by push plus pull-request volume relative to the median of the 12 months before the break, capped at 1 (`stats.coverage_factor`). This assumes developers are lost in proportion to events, which over-corrects (developers with few events are lost first), so it is a conservative test. C2 and C3a are computed on raw and adjusted MAD and shown side by side. **If a claim's result differs between raw and adjusted, I report it as FRAGILE**, and a fragile claim does not count toward the verdict.
   - Budget. I ran these two volume queries once each, within the budget I set (`sql/COSTS.md`).
9. C3b uses two sources (2026-11-12). The coverage drop would make some returning NEAR developers look new, which would favour C3b. An author counts as new to NEAR only if both sources show no NEAR-ecosystem activity before 2026-10-19. The first is GH Archive from 2021-01 to 2026-10-18 (monthly tables to 2026-09, daily tables for 2026-10-01 to 2026-10-18). I still use the incomplete late-2026 months here, because more data can only move authors from new to returning. The second is the author's public GitHub event feed (`/users/{login}/events/public`), which covers about the last 90 days and at most 300 events, checked for push or pull-request events on NEAR-ecosystem repos before 2026-10-19. Very active authors can hit the 300-event cap before the feed reaches 2026-10-19. I report how many did, and I show the C3b share both with all authors and with capped, truncated authors excluded. The kill criterion uses the lower of the two shares.

<!-- BEGIN GENERATED: results (do not edit by hand; `make site` rewrites this) -->
## Results (verdict: **Neutral**, 1 of 3 top-level claims hold)

The verdict counts the three top-level claims C1 to C3: Bull if at least two hold, Neutral if one, Bear if none. A claim marked FRAGILE (raw and coverage-adjusted results disagree) does not count. C3 holds only if both C3a and C3b hold, so C3b holding on its own does not add to the count.

Data as of: GH Archive (GHA, a public record of GitHub events) usable through 2026-02 (coverage rule); NEAR contract deployments through 2026-11 (current month partial; C2 and C3a use months through 2026-02 to match GHA); hackathon cohort fetched 2026-11-12; Open Dev Data commit `d664cfa`. Every figure below is read from [`data/cache/claims.json`](data/cache/claims.json), produced by `make analysis`.

| Claim | Kill criterion | Measured | Status |
|---|---|---|---|
| C1: New NEAR developers retain at least as well as peers (Solana, Sui, Aptos, Base) | NEAR 6-month retention below peer median | 12.04% vs peer median 12.03% | HOLDS (statistical tie)<br>Statistical tie: margin +0.01 pp, NEAR 95% CI 11.34%–12.78% contains the peer median. Fragility: smoothed 6-month 17.86% vs 18.68% (fails); 12-month 7.91% vs 9.03% (fails). |
| C2: NEAR monthly active developers (MAD) lead contract deployments by 1–6 months | No lag with p < 0.0083 (0.05 / 6, Bonferroni) | best p 0.091 raw / 0.124 coverage-adjusted | KILLED<br>Raw and coverage-adjusted MAD agree. |
| C3: AI-era funnel: needs both C3a and C3b | C3a or C3b killed | see C3a, C3b | KILLED |
| &nbsp;&nbsp;↳ C3a: Contracts deployed per MAD rose since 2025 | Post-2025 mean not above 1.10× the 2023–24 mean | 0.67× raw, 0.56× coverage-adjusted | KILLED<br>Mann-Whitney p = 0.705 (raw), not part of the criterion. |
| &nbsp;&nbsp;↳ C3b: A majority of NEAR HACKATHON authors are new to NEAR | New-to-NEAR authors fewer than 50% of the cohort (stricter of two shares) | 97.2% (310/319); 97.4% excluding 11 authors with truncated event feeds | HOLDS<br>AI co-authored: ≥41.4% of commits, 34.2% of repos (125/366 repos with at least one non-bot commit). |

## What would change the verdict

Each line gives the threshold that would flip a claim on the next rebuild (`make data && make all`).

- C1 (HOLDS) flips to KILLED if NEAR's 6-month retention drops below the peer median (today 12.04% vs 12.03%, a margin of +0.01 pp). Watch it: the margin is inside sampling error.
- C2 (KILLED) flips to HOLDS if any lag 1–6 reaches p < 0.0083 for deploys or unique deployers, on both raw and coverage-adjusted MAD (on only one: FRAGILE). Best today: 0.091 raw, 0.124 adjusted.
- C3a (KILLED) flips to HOLDS if mean contracts per MAD from 2025-01 is above 1.10× the 2023–24 mean: above 1.66 raw (today 1.01) and above 1.66 adjusted (today 0.84).
- C3b (HOLDS) flips to KILLED if new-to-NEAR authors are fewer than 50% of a future cohort (today 97.2%, stricter of the two shares).
- The verdict (Neutral) becomes Bull if one more top-level claim holds. That means either C2 holds, or C3a holds, which makes C3 hold because C3b already does. It becomes Bear if C1 flips to KILLED.

## Exploratory, not pre-registered

- Deploys → developers (the reverse of C2, raw MAD, log-differenced): Granger p-values lag 1: 0.948, lag 2: 0.012, lag 3: 0.021, lag 4: 0.014, lag 5: 0.026, lag 6: 0.022. Bonferroni threshold across 6 lags: 0.0083. No lag survives the correction, so this is a hint, not a finding. It was not pre-registered and has no effect on the verdict.
- C2 out-of-sample check (fit to 2024-12, one-step forecasts after): adding lagged MAD changes forecast RMSE by a factor of 1.36 for deploys and 1.03 for unique deployers (below 1 would mean developers help predict usage).

## Bear case

- NEAR's monthly active developers peaked at 1,179 in 2022-04 and were 484 in 2026-02, the last month with reliable GHA coverage.
- Developers do not lead onchain usage (C2 killed), so in this data developer counts give no early warning of usage, which removes the main reason to watch them as a signal for the token.
- Output per developer fell (0.67× raw, 0.56× adjusted). Fewer developers are not being offset by more contracts each.
- NEAR's retention is no better than its peers'. It is a statistical tie at 6 months and behind at 12.
- The hackathon brought 319 mostly new authors, but a two-week cohort says nothing yet about whether they stay. C1 suggests about 12.04% of new NEAR developers are still active six months later.

## Limitations

- GHA volume breaks in 2025-06 (pushes fall about 30%) and collapses after 2026-02 (pull requests, then pushes). Series end at 2026-02; C2 and C3a are also run on coverage-adjusted MAD, and disagreements would be reported as FRAGILE.
- Developer identity is the GHA actor of a push or PR on a repo listed in Open Dev Data. Electric Capital counts original commit authors, so levels differ from the Developer Report. Private repos and unlisted repos are invisible.
- I started the history at 2021-01 to stay within the BigQuery budget, so some developers counted as new in 2022 had been active before 2021.
- Deployments are transaction-level DEPLOY_CONTRACT only. I excluded factory-created contracts on purpose (THESIS.md, Methodology changes, item 4).
- C3b covers 367 repos with a GitHub link out of 678 nearhunt.xyz projects (764 official submissions); 1,500 commits had no linked GitHub account. 16 authors hit GitHub's 300-event feed cap; 11 of them have feeds that stop after 2026-10-19 and are shown both included and excluded.
- AI co-authorship is detected from commit trailers only, a lower bound. The repo share uses repos with at least one non-bot commit (366 of 367); 1 repo's only author has a login ending in "-bot" and is removed by the bot filter.
- I fixed the C3a threshold (>10%) after I had seen the deployment series. THESIS.md, Methodology changes, item 6, gives the exact order of events with commit hashes.
<!-- END GENERATED: results -->
