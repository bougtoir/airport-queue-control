# GATE 02 — CONTRIBUTION AND ESTIMAND RESET

Verdict: **PASS**

## Title decision
Keep: "Separating waiting from movement: a stationary threshold-release architecture for
airport security queues". Precise, journal-neutral, already approved; no TR-C-specific
language. No change needed.

## Reframed contribution (SMPT)
A transparent, falsifiable discrete-event simulation framework for state-dependent release
control of stored passenger demand, comprising:
1. an explicit state/action/safeguard interface for threshold release into a constrained
   screening stage;
2. a progression-accounting convention that separates movement-event endpoints
   (model-dependent) from structural endpoints (route-determined);
3. a matched-route structural ablation isolating the movement-coordination contrast;
4. prespecified stress/falsification producing a failure-region map, including an adverse
   controller configuration and negative/precision findings.

## Estimand reset — structural vs dynamic
- Structural by construction: route distance and turning (deterministic consequences of
  route definitions); S3 one-start mechanism (design rule); S0 incremental-advance rule
  (specified progression convention). These cannot be "discovered" by the simulator.
- Dynamic conditional on simulator: queueing, waiting, throughput, required area, realized
  S0 stop-go counts (vary with arrivals/service/timing).
- What matched-route comparison validates: that the starts contrast is not solely driven
  by route length/turning. What it cannot validate: the S0 progression rule as an empirical
  behavioral model — no field-estimated locomotion, safety, comfort, fatigue, or
  real-airport effectiveness.

## TR-C residue removal plan (for Gate 5)
- Remove/soften "transport-control framework" phrasing pitched at TR-C readership; replace
  with "simulation modelling" / "decision-support" vocabulary.
- Abstract last sentence ("falsifiable transport-control framework") → simulation-methodology
  contribution wording.
- Introduction motivation paragraph stays (checkpoint as control problem is still valid),
  but the contribution sentence is reworded to the SMPT framing above.
- Discussion opening "main transport-system result" → "main simulation result".
- Cover letter: full rewrite for SMPT (Gate 10).

## Contribution paragraph (to be inserted verbatim in Introduction)
"This study contributes a reproducible discrete-event simulation framework that separates
waiting from movement through a state-dependent threshold-release controller: an explicit
state/action/safeguard interface, progression-event accounting that distinguishes
model-dependent from structural endpoints, a matched-route ablation isolating the
coordination contrast, and a prespecified falsification protocol that maps the failure
region. All analyses, seeds, and negative findings are retained and machine-traced."

## Feasibility check on theory requirement
SMPT accepts application/methodology papers; theory is "important but presented in context
of applicability". Our contribution is methodology+experimentation, so no new theorems are
required for journal fit — no NO-GO on this criterion.
