-- Coverage index: monthly PushEvent and PullRequestEvent counts (the two event types the MAD metric uses).
-- Reads only the `type` column. Built by `ingest_bigquery volume`; the original run reused 11 months
-- already counted by gha_type_volume.sql (see COSTS.md).
SELECT _TABLE_SUFFIX AS month, type, COUNT(*) AS events
FROM `githubarchive.month.*`
WHERE _TABLE_SUFFIX IN ({{months}})
  AND type IN ('PushEvent', 'PullRequestEvent')
GROUP BY 1, 2
