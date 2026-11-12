# Demo video script (60–90 s)

Record at 1080p. Read the figures off the screen as you go; this script names where to look rather than typing them, so it can't go stale.

| Time | On screen | Voice-over |
|---|---|---|
| 0:00–0:08 | Dashboard top: title, one-liner, verdict badge | "Builders First is a NEAR investment thesis built from developer data, not price. We pre-registered three claims, each with a kill criterion, before pulling any data." |
| 0:08–0:20 | Scroll to **Headline findings** | "The surprise is the hackathon itself: [read the first headline's %] of builders had no prior public NEAR activity, and at least [second headline's %] of their commits are AI co-authored, and that's a lower bound." |
| 0:20–0:35 | **Claims scorecard**; point at C1's "statistical tie" note, C2 and C3a KILLED | "Retention is a tie with Solana, Sui, Aptos and Base. Developers do not lead usage, and output per developer fell. So the verdict is [badge]. We report that instead of tuning the method." |
| 0:35–0:48 | **C2** chart and lag table; then **Exploratory** section | "Granger tests show no lead from developers to deployments. The reverse direction is suggestive but doesn't survive Bonferroni, so it's labelled exploratory." |
| 0:48–0:60 | **Data quality** chart (GH Archive volume, cutoff shaded) | "GH Archive itself breaks in 2025 and collapses in 2026. A coded rule cuts the series, and a coverage-adjusted rerun checks every claim. Any claim that flips would be marked fragile." |
| 0:60–0:75 | **What would change the verdict** | "Each claim has the exact threshold that flips it on the next rebuild, so investors can reuse this as a monitoring framework." |
| 0:75–0:90 | Terminal: `make setup && make all` → tests pass; GitHub Actions green check | "Everything rebuilds offline from cached data with one command, and CI checks on every push that the committed numbers reproduce exactly. Built at NEAR HACKATHON." |
