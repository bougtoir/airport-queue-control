# RESULTS_INTEGRITY_AUDIT — Gate 4 (2026-10-13, machine-checked against results/)

## Locked primary (results/phase5/primary_results.csv, N=200 paired, CRN)
| Claim | Manuscript | CSV value | Status |
|---|---|---|---|
| thr diff 0.85 | 4.0 (3.4–4.5) | 3.95 (3.417–4.483) | consistent (rounded) |
| thr diff 0.95 | 8.5 (7.0–10.0) | 8.48 (6.998–9.962) | consistent |
| starts diff 0.85 | −1.5 (−1.9,−1.0) | −1.475 (−1.914,−1.036) | consistent |
| starts diff 0.95 | −6.3 (−7.4,−5.3) | −6.341 (−7.428,−5.253) | consistent |
| distance | −33.0 m | −33.0 | exact |
| turning | −1440° | −1440.0 | exact |
| area 0.85 | −0.7 m² | −0.689 (−1.188,−0.190) | consistent |
| area 0.95 | −5.2 m² | −5.243 (−6.577,−3.909) | consistent |
| capacity eff | unchanged | 0.0 diff both loads | exact |

## Precision (monte_carlo_precision.csv)
- Target 0.100; achieved 0.4388 (0.85) / 1.0873 (0.95); required 3,805 / 23,359 — exact match.

## Matched routes (results/phase13/summary.csv)
- 6/6 matched cases throughput_acceptable_2pct=yes; diffs −0.58…1.2 (claimed −0.6…1.2);
  all movement-start differences negative; distance/turning diffs exactly 0. Consistent.

## Optimization (results/phase7/)
- design_summary.csv: 289 designs; feasible=239; pareto_front.csv: 8 nondominated. Consistent.

## Falsification (results/phase8/)
- scenario_comparisons.csv: 41 scenarios; failure_regions.csv: 36 rows, all
  failure_detected=yes → 36/41 flagged. Surge=34, conflict=34, unfinished=0,
  movement_null=1, staffing=1. One conventional combo (s3_bad_control: −13.33 pax/h,
  +82.9 s wait, +12.0 m²; also surge+conflict flagged). Consistent with manuscript.

## Generic benchmark (results/phase9/transferability_comparisons.csv)
- 18 rows: S3 9/9 acceptable, S5 5/9 acceptable (4 failures). Consistent.

## Presentation-integrity checks
- Configured-route positive throughput diffs are reported with the explicit caveat
  "not a universal capacity gain" (Results ¶1) — no universal claim present.
- Identical-footprint capacity efficiency (0.0 diff) reported — no "increased safe
  capacity" claim present.
- Surge/conflict labeled unvalidated engineering screens/proxies, threshold sensitivity
  disclosed (1.25–4.00 → 39–2 and 38–13 flags). Arbitrary proxy thresholds not conflated
  with safety outcomes.
- Adverse controller configuration (s3_bad_control) and movement-null case retained.
- Effect sizes + 95% CIs throughout; paired-t intervals; no p-value theatre; no
  legitimate p-values removed.

## Discrepancies found
None. All claims trace to machine-readable outputs. No result disagrees across code,
tables and text.
