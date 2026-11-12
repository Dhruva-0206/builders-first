# Builders First — a NEAR investment thesis from developer data

**Status: pre-registration.** This file was committed on 2026-11-12, before any data was pulled or any result computed. The claims, metrics and kill criteria below are fixed. Results, the verdict and the bear case are added later by code (`make analysis`), and any change to method is logged under *Methodology changes* with the reason. Check the git history of this file to confirm the order.

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

## Data sources

- Open Dev Data by Electric Capital (repo-to-ecosystem taxonomy, CC BY 4.0) — https://github.com/electric-capital/open-dev-data
- GH Archive on BigQuery (GitHub events)
- `bigquery-public-data.crypto_near_mainnet_us` (NEAR receipts and transactions)
- nearhunt.xyz and nearhackathon.com public project APIs (hackathon submissions)
- GitHub REST API (hackathon repo commits)

## Methodology changes

Logged in the order they were made, with the date. Where the order of decision and data matters, the commit hashes are given so it can be checked with `git log`.

1. **Ecosystem names (2026-11-12).** Open Dev Data names are `NEAR`, `Solana`, `Sui`, `Aptos`, `Base`; all sub-ecosystems are included. Base is present, so the EVM L2 peer is Base. The taxonomy is pinned to the commit recorded in `data/cache/ecosystems_meta.json`. The export uses the package's `taxonomy` module directly (same code path as `open-dev-data export`).
2. **GH Archive window (2026-11-12).** History starts 2021-01, not 2019-01, to fit the BigQuery sandbox budget (dry-run costs in `sql/COSTS.md`). Consequence: a developer active before 2021 who returns in 2022 can be counted as "new" in early cohorts. Cohorts still start 2022-01, so every cohort has at least 12 months of look-back.
3. **Developer identity and events (2026-11-12).** A developer is the GH Archive `actor.login` of a `PushEvent` or `PullRequestEvent` (any action) on an ecosystem repo. "Merged only" would require reading the large `payload` column for every month, which the budget does not allow. Electric Capital counts original commit authors, so absolute numbers differ from the Developer Report; trends are comparable. Bot logins are removed by pattern (`[bot]`, `-bot`, dependabot, github-actions, renovate).
4. **NEAR deployments (2026-11-12).** Deployments come from `transaction_actions` (`action_kind = 'DEPLOY_CONTRACT'`, signed directly by an account), not `receipt_actions`, which would cost about 3× more to scan. Contracts created by factory contracts are therefore excluded, and this is deliberate, not only a cost saving. A transaction-level `DEPLOY_CONTRACT` is an account deploying code it chose to ship — a developer action. Factory deployments (DAO, token and meme-coin factories) are mostly end users pressing a button in someone else's app; they measure that app's popularity, not developer output, and a single viral factory can add thousands of deployments in a month. Excluding them makes the series a cleaner measure of developer output. Possible bias: it undercounts teams that deploy through their own factory or through a deployer contract (for example some upgrade or multisig flows), and it counts redeploys of the same contract as separate deployments; both would understate or add noise to output, and a shift of developers toward factory-style deployment over time would make the series fall even if output did not. Unique deployers = distinct `signer_account_id`. The NEAR BigQuery dataset is current (max `block_date` 2026-11-12 at fetch time); no RPC back-fill was needed.
5. **Incomplete months (2026-11-12).** The current calendar month is partial and is excluded from every monthly series and from cohort follow-up.
6. **C3a threshold (2026-11-12).** "Flat" was not defined numerically above. Fixed: C3a holds only if mean monthly contracts-deployed-per-MAD from 2025-01 onward is more than 10% above the 2023-01–2024-12 mean. A Mann-Whitney test is reported alongside, but it is not part of the criterion.
   *Order of events, stated plainly:* the threshold was committed in `4d4fc58` (2026-11-12 20:01:34 UTC), before the developer-activity data commit `3cefe2f` (20:04:15 UTC) and before any MAD figure had been computed or viewed. It was **not** fixed before all data existed: the NEAR deployment series (the numerator, `48ddb53`) had already been downloaded and printed, and four of six GH Archive raw chunks (2021–2024) had been written to `data/raw/` about a minute earlier, unopened. The 2025–2026 chunks, which contain the whole post-period, landed after the commit.
7. **C3b cohort (2026-11-12).** Repos come from nearhunt.xyz entries that link a GitHub repository; commits are from each repo's default branch since 2026-10-19T00:00Z, up to the fetch time. Commits whose author has no linked GitHub account are excluded from author counts but included in the AI-trailer share. "Prior NEAR activity": see item 9. The committed ecosystem-activity cache stores logins as unsalted SHA-256 prefixes, and the comparison is done on those hashes.
8. **GH Archive coverage breaks (2026-11-12, found after download).** GH Archive's own volume is not stable: an event-type breakdown (`data/cache/gha_type_volume.csv`, `data/cache/gha_pushpr_volume.csv`) shows that PushEvent volume falls about 30% in 2025-06 and stays lower, and that PullRequestEvent volume collapses through 2026-03..08 before pushes also fall in 2026-09. These breaks are in the source and hit every ecosystem, so they lower measured developer counts without any change in real activity. Two coded responses (`stats.py`):
   - **Cutoff.** A month is *good* if both push and PR volume are at least 80% of the median of the 12 months before it. GH Archive-based series end at the month before the final run of failing months (`stats.last_good_month`). Months after it are excluded from MAD, retention follow-up, C2 and C3a. The 80% threshold was chosen after looking at the GH Archive volume series only, not at any ecosystem's numbers. The dashboard charts push and PR volume with the cutoff marked.
   - **Coverage-adjusted MAD.** A failing month before the cutoff marks a level break. From that break on, monthly MAD is divided by push+PR volume relative to the median of the 12 months before the break, capped at 1 (`stats.coverage_factor`). This assumes developers are lost in proportion to events, which over-corrects (developers with few events are lost first), so it is a conservative test. C2 and C3a are computed on both raw and adjusted MAD and shown side by side. **If a claim's result differs between raw and adjusted, the claim is reported as FRAGILE**, and a fragile claim does not count toward the verdict.
   - Budget: these two volume queries were run once, with the lead's approval (`sql/COSTS.md`).
9. **C3b: two sources, no gap (2026-11-12).** The coverage drop would make some returning NEAR developers look new, which would favour C3b. An author is *new to NEAR* only if **both** sources show no NEAR-ecosystem activity before 2026-10-19: (a) GH Archive, 2021-01 through 2026-10-18 (monthly tables to 2026-09, daily tables for 2026-10-01..18; the incomplete late-2026 months are still used here, because more data can only move authors from "new" to "returning"); (b) the author's public GitHub event feed (`/users/{login}/events/public`), which covers roughly the last 90 days and at most 300 events, checked for Push or PullRequest events on NEAR-ecosystem repos before 2026-10-19. Very active authors can hit the 300-event cap before the feed reaches 2026-10-19; their count is reported, and the C3b share is shown both with all authors and with capped-and-truncated authors excluded. The kill criterion is evaluated on the stricter (lower) of the two shares.

## Results

*To be generated by `make analysis` from `data/cache/claims.json`.*
