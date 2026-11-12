-- D2: distinct (ecosystem, month, login) with >=1 PushEvent or PullRequestEvent on an ecosystem repo.
-- Reads only type, repo.name, actor.login; month comes from the table suffix (no created_at needed).
-- Repo lists: Open Dev Data by Electric Capital, loaded into {{project}}.{{dataset}}.repos.
SELECT
  r.ecosystem,
  g._TABLE_SUFFIX AS month,
  LOWER(g.actor.login) AS login
FROM `githubarchive.month.*` AS g
JOIN `{{project}}.{{dataset}}.repos` AS r
  ON LOWER(g.repo.name) = r.repo
WHERE g._TABLE_SUFFIX BETWEEN '{{start}}' AND '{{end}}'
  AND g.type IN ('PushEvent', 'PullRequestEvent')
  AND NOT REGEXP_CONTAINS(LOWER(g.actor.login), r'(\[bot\]$|-bot$|^dependabot|^github-actions|^renovate)')
GROUP BY 1, 2, 3
