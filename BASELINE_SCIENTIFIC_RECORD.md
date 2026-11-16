# BASELINE_SCIENTIFIC_RECORD — locked state before SMPT retarget

Source of truth: locked plan v1.1, results/phase5/*, manuscript_author_FINAL.docx.
Nothing below may be changed during the retarget.

## Locked design
- Comparison: S3/B1 (stationary threshold release) vs S0/B0 (switchback), common random numbers.
- Loads 0.85 and 0.95; 200 paired replications per cell; unfinished passengers retained.
- Throughput safeguard: lower 95% paired bound > −2% of baseline.
- Locked plan SHA-256: 36114b51e3f10e7708fac6867faca8fd246cbff4e0eec53dbda9656d7070619c.

## Locked primary results
- Load 0.85: throughput diff +4.0 pax/h (95% CI 3.4–4.5); starts diff −1.5 (−1.9,−1.0);
  distance −33.0 m; turning −1440°; area −0.7 m².
- Load 0.95: throughput diff +8.5 (7.0–10.0); starts −6.3 (−7.4,−5.3); area −5.2 m².
- Precision: target half-width 0.100; achieved 0.439 / 1.087; required replications
  3,805 / 23,359; cap 200 retained, shortfall disclosed.
- Matched routes: 6/6 safeguard met; throughput diff −0.6 to 1.2; start contrasts all negative.
- Optimization: 289 designs evaluated, 239 feasible, 8 nondominated (all 1.0 modeled start).
- Falsification: 36/41 scenarios flagged; 1 combined operational failure
  (−13.3 pax/h, +82.9 s wait, +12.0 m²); surge flags 34, conflict flags 34,
  unfinished-demand failures 0, movement-null 1, staffing-infeasible 1.
- Generic geometry benchmark: S3 9/9, S5 5/9 within safeguard.

## Parameters (configs/default.yaml is truth)
- Reduced-mobility share 0.04; service CV 0.55; release compliance 0.97.

## Documented limitations (must remain)
- No field/external validation; internal checks are implementation consistency only.
- S0 stop-go counts are model-imposed by the explicit progression rule, not empirical.
- Distance/turning are structural consequences of route definitions.
- Precision target unmet for the start/stop contrast.
- Capacity improvements conditional; nominal footprint capacity unchanged.
- Surge/conflict proxies are unvalidated engineering screens, not safety outcomes.
- No physiological/comfort/injury/safety claims supported.

## Manuscript structure at freeze
- Figures 1–8, Tables 1–6, 20 Vancouver-style references in first-appearance order.
- Supplement integrated into main text; no separate supplement file.
- Known removed residue: unrelated dispensing/medical consent+ethics text already replaced.

## Prior gate evidence retained
- 10/10 internal validation checks; Ruff + 52 tests; clean same-VM reproduce 528 s;
  traceability/consistency/numbering audits PASS (see repo audit files).
