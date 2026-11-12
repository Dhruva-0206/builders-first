-- Coverage index: monthly PushEvent and PullRequestEvent counts (the two event types the MAD metric uses).
-- Reads only the `type` column. Months already in data/cache/gha_type_volume.csv are skipped.
SELECT _TABLE_SUFFIX AS month, type, COUNT(*) AS events
FROM `githubarchive.month.*`
WHERE _TABLE_SUFFIX IN ({{months}})
  AND type IN ('PushEvent', 'PullRequestEvent')
GROUP BY 1, 2
