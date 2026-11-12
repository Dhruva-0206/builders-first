-- Data-quality check: monthly event counts by type around the 2025 step change and the late-2026 drop.
-- Reads only the `type` column.
SELECT _TABLE_SUFFIX AS month, type, COUNT(*) AS events
FROM `githubarchive.month.*`
WHERE _TABLE_SUFFIX IN ('202503','202504','202505','202506','202507','202508','202606','202607','202608','202609','202610')
GROUP BY 1, 2
