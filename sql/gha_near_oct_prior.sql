-- C3b: NEAR-ecosystem logins active 2026-10-01..2026-10-18 (before the hackathon announcement on 10-19).
-- Monthly tables cannot separate the days before 10-19, so this uses the daily tables.
SELECT DISTINCT LOWER(g.actor.login) AS login
FROM `githubarchive.day.202610*` AS g
JOIN `{{project}}.{{dataset}}.repos` AS r
  ON LOWER(g.repo.name) = r.repo
WHERE g._TABLE_SUFFIX BETWEEN '01' AND '18'
  AND r.ecosystem = 'NEAR'
  AND g.type IN ('PushEvent', 'PullRequestEvent')
  AND NOT REGEXP_CONTAINS(LOWER(g.actor.login), r'(\[bot\]$|-bot$|^dependabot|^github-actions|^renovate)')
