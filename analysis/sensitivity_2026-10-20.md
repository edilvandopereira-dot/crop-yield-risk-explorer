# Sensitivity of historical soybean yield shortfalls

The same state-year yields can produce different shortfall counts when the historical reference changes. This extension compares preceding three- and five-year means and four thresholds, preserving a matched denominator for each state. It extends the existing portfolio case rather than introducing a new data source or predictive model.

## Source and definitions

IBGE PAM, SIDRA 1612, soybean grain; 2010–2025 state observations from the preserved 16 October 2026 snapshot. No new download or data revision was introduced. Evaluate 2016–2025. Each reference uses only valid yields in the exact consecutive preceding years, excluding current and future observations. An event is a yield strictly more than the threshold below its reference; equality is excluded before rounding. Exact rational arithmetic protects threshold boundaries for decimal inputs.

For a given state, retain only evaluation years with a valid current yield and both references. This intersection is the denominator in both comparison columns. All 27 states are retained, with no minimum-area filter; 182 matched state-years are evaluable. Six states have zero matched years and show unavailable values, not zero frequencies. States with fewer than five matched valid years are flagged as limited coverage. Cross-state coverage is not necessarily equal.

## Results at a 10 percent threshold

| State | Valid paired years | Three-year mean | Five-year mean |
|---|---:|---:|---:|
| Mato Grosso | 10 | 1 | 1 |
| Rio Grande do Sul | 10 | 3 | 4 |
| Paraná | 10 | 2 | 1 |
| Goiás | 10 | 0 | 0 |

The illustration retains the same four states shown in the original README; the full report exposes every state. Other changing counts at 10% are Amapá (2/8 to 1/8) and Mato Grosso do Sul (3/10 to 2/10). State selection must not be interpreted as evidence of a nationwide causal effect.

Rio Grande do Sul in 2025 is about 3.1% below its preceding three-year mean and 12.2% below its preceding five-year mean, so its classification crosses the 10% threshold. At a 20% threshold, its counts are 2/10 and 3/10. Threshold and reference length are separate choices; vary one while holding the other fixed.

## Validation

Eight analytical tests passed. The independent SQLite window implementation checked all 216 combinations of 27 states, two reference lengths and four thresholds, including paired valid-year lists. The suite also protects strict threshold equality, missing consecutive years, separation of states and absence of current/future observations in references. The original source build rechecked hashes and passed 48 state-to-national reconciliations.

Browser validation confirmed 27 rows, Rio Grande do Sul at 10% and 20%, unavailable coverage for Paraíba and a JSON download reflecting the selected threshold. The social figure uses the computed JSON, with a zero-based count axis, explicit denominators and accessible text.

## Reproduce

```bash
python3 -m unittest discover -s tests -v
python3 scripts/build.py
# Optional, requires matplotlib:
python3 scripts/export_sensitivity_figure.py
```

The standard-library build generates data/processed/sensitivity.json and docs/sensitivity.html. The main dashboard keeps its original three-year reference and links to the companion sensitivity report; it does not silently switch its definition.

## Interpretation and limits

This checks stability of a descriptive definition. It does not select an optimal reference, establish comparative forecasting accuracy, identify weather causes, recommend suppliers or quantify financial impact. A longer mean may react more slowly to trends and past shocks. The snapshot is current-vintage retrospective data rather than observations as available at historical release dates. Different coverage and state aggregation constrain comparisons.

The follow-up LinkedIn text and chart are prepared for review. This analysis does not imply that the follow-up was published.
