-- D3: NEAR mainnet contract deployments signed directly in transactions (transaction-level DEPLOY_CONTRACT),
-- per month: count of deploy actions and unique deployer (signer) accounts.
-- transaction_actions is used instead of receipt_actions because the latter costs ~3x more to scan;
-- factory-made deployments (contract-to-contract receipts) are therefore excluded.
SELECT
  DATE_TRUNC(block_date, MONTH) AS month,
  COUNT(*) AS deploys,
  COUNT(DISTINCT signer_account_id) AS unique_deployers
FROM `bigquery-public-data.crypto_near_mainnet_us.transaction_actions`
WHERE block_date BETWEEN '{{start}}' AND '{{end}}'
  AND action_kind = 'DEPLOY_CONTRACT'
GROUP BY 1
