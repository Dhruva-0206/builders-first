# BigQuery dry-run costs

| when (UTC) | query | GB processed | note |
|---|---|---|---|
| 2026-11-12 19:43 | `near_freshness` | 19.06 | dry run |
| 2026-11-12 19:43 | `near_freshness` | 19.06 | dry run |
| 2026-11-12 19:46 | `gha_active_devs 202101-202112` | 50.75 | dry run |
| 2026-11-12 19:47 | `gha_active_devs 202201-202212` | 67.83 | dry run |
| 2026-11-12 19:47 | `gha_active_devs 202301-202312` | 77.13 | dry run |
| 2026-11-12 19:47 | `gha_active_devs 202401-202412` | 96.57 | dry run |
| 2026-11-12 19:47 | `gha_active_devs 202501-202512` | 85.24 | dry run |
| 2026-11-12 19:47 | `gha_active_devs 202601-202611` | 50.41 | dry run |
| 2026-11-12 19:47 | `near_deploys 2021-01-01..2021-12-31` | 2.51 | dry run |
| 2026-11-12 19:47 | `near_deploys 2022-01-01..2022-12-31` | 9.02 | dry run |
| 2026-11-12 19:47 | `near_deploys 2023-01-01..2023-12-31` | 22.70 | dry run |
| 2026-11-12 19:47 | `near_deploys 2024-01-01..2024-12-31` | 115.32 | dry run |
| 2026-11-12 19:47 | `near_deploys 2025-01-01..2025-12-31` | 89.33 | dry run |
| 2026-11-12 19:47 | `near_deploys 2026-01-01..2026-11-13` | 23.33 | dry run |
| 2026-11-12 19:58 | `near_deploys 2021-01-01..2021-12-31` | 2.51 | dry run (ordering) |
| 2026-11-12 19:58 | `near_deploys 2022-01-01..2022-12-31` | 9.02 | dry run (ordering) |
| 2026-11-12 19:58 | `near_deploys 2023-01-01..2023-12-31` | 22.70 | dry run (ordering) |
| 2026-11-12 19:58 | `near_deploys 2024-01-01..2024-12-31` | 115.32 | dry run (ordering) |
| 2026-11-12 19:58 | `near_deploys 2025-01-01..2025-12-31` | 89.33 | dry run (ordering) |
| 2026-11-12 19:58 | `near_deploys 2026-01-01..2026-11-13` | 23.33 | dry run (ordering) |
| 2026-11-12 19:58 | `near_deploys 2021-01-01..2021-12-31` | 2.51 | dry run |
| 2026-11-12 19:58 | `near_deploys 2021-01-01..2021-12-31` | 2.52 | ACTUAL billed (estimate 2.51 GB, cache hit False) |
| 2026-11-12 19:58 | `near_deploys 2022-01-01..2022-12-31` | 9.02 | dry run |
| 2026-11-12 19:58 | `near_deploys 2022-01-01..2022-12-31` | 9.02 | ACTUAL billed (estimate 9.02 GB, cache hit False) |
| 2026-11-12 19:58 | `near_deploys 2023-01-01..2023-12-31` | 22.70 | dry run |
| 2026-11-12 19:59 | `near_deploys 2023-01-01..2023-12-31` | 22.70 | ACTUAL billed (estimate 22.70 GB, cache hit False) |
| 2026-11-12 19:59 | `near_deploys 2026-01-01..2026-11-13` | 23.33 | dry run |
| 2026-11-12 19:59 | `near_deploys 2026-01-01..2026-11-13` | 23.34 | ACTUAL billed (estimate 23.33 GB, cache hit False) |
| 2026-11-12 19:59 | `near_deploys 2025-01-01..2025-12-31` | 89.33 | dry run |
| 2026-11-12 19:59 | `near_deploys 2025-01-01..2025-12-31` | 89.33 | ACTUAL billed (estimate 89.33 GB, cache hit False) |
| 2026-11-12 19:59 | `near_deploys 2024-01-01..2024-12-31` | 115.32 | dry run |
| 2026-11-12 19:59 | `near_deploys 2024-01-01..2024-12-31` | 115.32 | ACTUAL billed (estimate 115.32 GB, cache hit False) |
| 2026-11-12 20:00 | `gha_active_devs 202101-202112` | 50.75 | dry run |
| 2026-11-12 20:00 | `gha_active_devs 202101-202112` | 50.75 | ACTUAL billed (estimate 50.75 GB, cache hit False) |
| 2026-11-12 20:00 | `gha_active_devs 202201-202212` | 67.83 | dry run |
| 2026-11-12 20:00 | `gha_active_devs 202201-202212` | 67.83 | ACTUAL billed (estimate 67.83 GB, cache hit False) |
| 2026-11-12 20:00 | `gha_active_devs 202301-202312` | 77.13 | dry run |
| 2026-11-12 20:01 | `gha_active_devs 202301-202312` | 77.14 | ACTUAL billed (estimate 77.13 GB, cache hit False) |
| 2026-11-12 20:01 | `gha_active_devs 202401-202412` | 96.57 | dry run |
| 2026-11-12 20:01 | `gha_active_devs 202401-202412` | 96.57 | ACTUAL billed (estimate 96.57 GB, cache hit False) |
| 2026-11-12 20:01 | `gha_active_devs 202501-202512` | 85.24 | dry run |
| 2026-11-12 20:01 | `gha_near_oct_prior` | 1.20 | dry run |
| 2026-11-12 20:01 | `gha_active_devs 202501-202512` | 85.24 | ACTUAL billed (estimate 85.24 GB, cache hit False) |
| 2026-11-12 20:01 | `gha_active_devs 202601-202611` | 50.41 | dry run |
| 2026-11-12 20:02 | `gha_active_devs 202601-202611` | 50.41 | ACTUAL billed (estimate 50.41 GB, cache hit False) |
| 2026-11-12 20:02 | `gha_near_oct_prior` | 1.20 | dry run |
| 2026-11-12 20:02 | `gha_near_oct_prior` | 1.20 | ACTUAL billed (estimate 1.20 GB, cache hit False) |

## Totals (Nov 2026, computed from the rows above)

- Executed queries: 14 (incl. `near_freshness`, billed 19.06 GB, logged before actual-billing rows existed; its re-run was a cache hit, 0 GB).
- Total billed: **710.4 GB**.
- BigQuery sandbox allowance: 1,000 GB/month (decimal GB, as logged). Estimated headroom for Nov 2026: **289.6 GB** (assumes no other usage on the project).
- Approval rule from here on: any new or re-run query needs a dry-run, plus the lead's OK if over 20 GB.
