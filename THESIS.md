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

Logged in the order they were made. Each was decided before the developer-activity (GH Archive) data used by C1–C3 was downloaded, except where noted.

1. **Ecosystem names (2026-11-12).** Open Dev Data names are `NEAR`, `Solana`, `Sui`, `Aptos`, `Base`; all sub-ecosystems are included. Base is present, so the EVM L2 peer is Base. The taxonomy is pinned to the commit recorded in `data/cache/ecosystems_meta.json`. The export uses the package's `taxonomy` module directly (same code path as `open-dev-data export`).
2. **GH Archive window (2026-11-12).** History starts 2021-01, not 2019-01, to fit the BigQuery sandbox budget (dry-run costs in `sql/COSTS.md`). Consequence: a developer active before 2021 who returns in 2022 can be counted as "new" in early cohorts. Cohorts still start 2022-01, so every cohort has at least 12 months of look-back.
3. **Developer identity and events (2026-11-12).** A developer is the GH Archive `actor.login` of a `PushEvent` or `PullRequestEvent` (any action) on an ecosystem repo. "Merged only" would require reading the large `payload` column for every month, which the budget does not allow. Electric Capital counts original commit authors, so absolute numbers differ from the Developer Report; trends are comparable. Bot logins are removed by pattern (`[bot]`, `-bot`, dependabot, github-actions, renovate).
4. **NEAR deployments (2026-11-12).** Deployments come from `transaction_actions` (`action_kind = 'DEPLOY_CONTRACT'`, signed directly by an account), not `receipt_actions`, which would cost about 3× more to scan. Contracts created by factory contracts are therefore excluded. Unique deployers = distinct `signer_account_id`. The NEAR BigQuery dataset is current (max `block_date` 2026-11-12 at fetch time); no RPC back-fill was needed.
5. **Incomplete months (2026-11-12).** The current calendar month is partial and is excluded from every monthly series and from cohort follow-up.
6. **C3a threshold (2026-11-12, before GH Archive data was downloaded).** "Flat" was not defined numerically above. Fixed now: C3a holds only if mean monthly contracts-deployed-per-MAD from 2025-01 onward is more than 10% above the 2023-01–2024-12 mean. A Mann-Whitney test is reported alongside, but it is not part of the criterion.
7. **C3b cohort (2026-11-12).** Repos come from nearhunt.xyz entries that link a GitHub repository; commits are from each repo's default branch since 2026-10-19T00:00Z, up to the fetch time. Commits whose author has no linked GitHub account are excluded from author counts but included in the AI-trailer share. "Prior NEAR activity" means the login appears in NEAR-ecosystem GH Archive activity from 2021-01 through 2026-10-18; October 2026 is resolved with the daily tables. The committed ecosystem-activity cache stores logins as unsalted SHA-256 prefixes, and the comparison is done on those hashes.
8. **GH Archive coverage drop (2026-11-12, found after download).** GH Archive's own event volume falls sharply in late 2026 (per-month event counts from table metadata are in `data/cache/gha_coverage.csv`). The drop is in the source and hits every ecosystem, so recent developer counts are undercounted rather than lower in reality. Rule, applied by code: GH Archive-based series end at the last month whose event count is at least 80% of the trailing 12-month median. Months after that are excluded from MAD, retention follow-up, C2 and C3a. This decision depends only on GH Archive's total volume, not on any ecosystem's numbers.
9. **C3b correction for the coverage drop (2026-11-12).** The same drop would make some returning NEAR developers look new, which would favour C3b. Each hackathon author's public GitHub event feed (`/users/{login}/events/public`, the last 90 days, up to 300 events) is also checked for Push or PullRequest events on NEAR-ecosystem repos before 2026-10-19. An author is *returning* if either source shows prior NEAR activity. Authors whose feed is capped before reaching 2026-10-19 are counted and reported.

## Results

*To be generated by `make analysis` from `data/cache/claims.json`.*
