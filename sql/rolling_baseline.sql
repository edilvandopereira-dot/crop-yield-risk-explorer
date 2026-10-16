-- This is a retrospective, current-vintage evaluation, not an as-of-year backtest.
-- One row per state/year includes missing years, so the window cannot skip a gap.
SELECT state_id, year, yield_kg_ha,
       CASE WHEN COUNT(yield_kg_ha) OVER history = 3
            THEN AVG(yield_kg_ha) OVER history END AS baseline_kg_ha
FROM observations
WINDOW history AS (
    PARTITION BY state_id ORDER BY year
    ROWS BETWEEN 3 PRECEDING AND 1 PRECEDING
)
ORDER BY state_id, year;
