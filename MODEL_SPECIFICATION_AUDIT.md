# MODEL_SPECIFICATION_AUDIT — Gate 3

## Conceptual model (verified against MODEL_SPECIFICATION.md + src/airport_batch_queue/)
- Staged DES: upstream holding store → controlled release gate → route traversal → finite
  downstream queue → parallel stochastic screening servers (secondary + long inspection).
- One-second decision grid for gate/service assignment; arrival/completion times continuous.
- Passengers: synthetic attributes (bags, group, reduced mobility, compliance, walking
  speed, static/moving footprint, service time). Arrival processes: 5 families.
- Server states: deterministic lane open/close schedules; utilization on available
  server-time only; closures produce zero completions (validation case passes).
- Finite staging: downstream capacity enforced for every policy; unfinished passengers
  retained through drain (not discarded).
- Batch-release state/action/threshold: controller observes upstream count, oldest wait,
  downstream count, idle servers, predicted completions; action = bounded release count;
  S3 releases when downstream ≤ threshold or max-hold reached. Gate delay configured.
- Random streams: single seed generates passengers; policy-specific draws only after
  generation; identical seeds preserve common passengers → CRN verified in code
  (simulator.py, seed flow).
- Warm-up/drain: runs continue through a drain period; unfinished demand retained and
  reported (0 unfinished-demand failures in Phase 8).
- Stopping conditions: fixed horizon + drain; replication cap 200 locked.
- Calibration status: none — synthetic parameters, generic geometry; explicitly disclosed.
- Scenario design: locked primary (0.85/0.95), Phase 3 geometry grid, Phase 7 289-design
  optimization, Phase 8 41 stress scenarios, Phase 9 3×3 benchmark, Phase 13 structural
  sensitivity.
- Stochastic replications/uncertainty: 200 paired CRN reps; paired-t 95% CIs; parameter
  uncertainty via finite grids only (disclosed); structural uncertainty via ablation.
- Statistical reporting: effect sizes + CIs; no composite index; safeguard rule prespecified.

## Stop-go accounting check (code-verified)
- simulator.py `_release`: under S0, every release increments `stop_go_events` for each
  passenger remaining upstream; on release starts=1+count, stops=count. Other policies:
  starts=1, stops=0. This is an explicit model convention, correctly documented in the
  manuscript as model-imposed — NOT conflated with empirically observed starts/stops. PASS.
- Throughput advantage caveat: configured-route differences (+4.0/+8.5) are explicitly
  attributed partly to route length; matched-route results retained prominently (6/6,
  −0.6..1.2). PASS.

## Issues found
- None requiring code changes. No genuine implementation bugs surfaced in this audit.
- tests/: 13 files; `make test` = Ruff on src/tests/scripts + pytest (52 tests per prior
  verified run; re-executed in Gate 9).
