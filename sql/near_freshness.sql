-- First query (CLAUDE.md §5): how recent is the NEAR public dataset?
SELECT MAX(block_date) AS max_block_date, MIN(block_date) AS min_block_date_2026
FROM `bigquery-public-data.crypto_near_mainnet_us.receipt_actions`
WHERE block_date >= '2026-01-01'
