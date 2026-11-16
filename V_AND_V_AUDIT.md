# V_AND_V_AUDIT — Gate 3

## Taxonomy actually applied
1. Code verification: Ruff lint + unit tests + 10 analytical/extreme-case checks
   (Phase 6: conservation, route accounting, max-hold, full closure, lane reduction,
   capacity bound, overload retention, virtual-queue geometry, identical footprint).
2. Internal validation / face validity: directional extreme cases and invariant checks;
   implementation consistency only.
3. Parameter sensitivity: Phase 3 geometry grid; Phase 8 stress scenarios (loads, bursts,
   service variability, compliance, downstream restriction, lane shocks, controller
   settings, combined adverse).
4. Structural sensitivity: matched-route ablation (Phase, Table 4); Phase 13 structural
   sensitivity report; Phase 9 generic geometries.
5. External validation: **NOT performed** — no field data, no real-airport calibration.
   Correctly disclosed in Methods, Results, Discussion, and this audit.

## Compliance check
- No internal check is presented as external validation anywhere in the manuscript
  (verified: Methods "implementation consistency only", Discussion limitation paragraph).
- The 10/10 checks are labeled analytical/extreme-case; the phase report repeats the
  non-calibration caveat.
- Precision limitation (unmet half-width target) reported in Results.

## Verdict
Correct, transparent, internally tested simulator; limitations explicit.
Verdict: **CONDITIONAL → acceptable PASS for SMPT positioning**: external validation absent
but journal scope permits application/methodology papers without mandatory field data,
provided the absence is disclosed — which it is, prominently.
