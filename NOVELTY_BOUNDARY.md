# NOVELTY_BOUNDARY — Gate 1

## Mandatory deep comparison: Yuan et al. (2025), SMPT 145:103202
Source: ScienceDirect article preview (abstract, highlights, introduction, methodology and
conclusion snippets, references) saved at
data/raw/literature/yuan2025_simpat_sciencedirect_preview_2026-10-13.html.
Full text is paywalled; claims below are limited to the readable preview — flagged where
unresolved.

### What Yuan et al. already do
- DES of queue dynamics at security screening checkpoints (queue lengths, waiting times,
  arrival rates).
- Investigate dynamically changing the NUMBER OF OPEN CHECKPOINTS (lanes) over time.
- DES used as a black-box evaluator producing a lookup table of system states fed into a
  MILP that optimizes the lane-opening schedule over a day (hourly periods).
- Validated on real input: one day of hourly domestic arrival data at Guangzhou Baiyun
  International Airport (2024-03-13); simulation-enhanced method achieves fewer total/peak
  lanes than stand-alone MILP at equal service levels.

### What they do NOT do (per preview)
- No release control of queued passengers: passengers wait in conventional queues served by
  lanes; there is no stationary upstream store with state-dependent batch release.
- No movement-event accounting (starts/stops, stop-go, distance, turning).
- No matched-route structural ablation, no falsification/stress matrix, no Pareto over
  movement/waiting/area/throughput.
- Optimization objective is capacity scheduling (lanes × time), not release policy design.
- Unresolved: whether their DES models within-queue progression micro-dynamics — the
  preview suggests aggregate queue dynamics only (hourly periods, queue length/waiting).
  Marked unresolved, not assumed.

### Independent contribution of this paper
- Different decision layer: state-dependent release of stored upstream demand into a
  constrained screening stage, under a prespecified throughput safeguard — complementary to
  lane scheduling, not a re-label.
- Different evidence: explicit progression-rule accounting, matched-route mechanism
  isolation, falsification-derived failure regions, negative/precision findings disclosed.
- Different validation stance: no real-airport calibration (disclosed); Yuan validated on
  one day of real arrivals. This is a limitation of ours, not a novelty claim.

## Boundary statement
Novel = the transparent, falsifiable DES framework for *release control* of stored demand:
state/action/safeguard formalization, stop-go progression accounting, structural-vs-dynamic
endpoint separation, matched-route ablation, and failure-region mapping. NOT novel and not
claimed: airport checkpoint DES itself, simulation+optimization coupling, real-data
validation, universal superiority of any layout.

## Gate 1 verdict
PASS — a nontrivial, evidence-backed simulation contribution remains after comparison with
the closest SMPT prior study. Contribution is methodological (control policy + V&V +
experimentation), not a re-labeled queue layout: the matched-route analysis, falsification
matrix and locked negative findings are the substance.
