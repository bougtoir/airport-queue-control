# GATE 01 — SMPT JOURNAL FIT AND CLOSEST PRIOR STUDIES

Verdict: **PASS**

Evidence:
- SMPT_SCOPE_AUDIT.md: official aims/scope + guide captured and hashed; subscription
  (no-fee) route confirmed; format requirements extracted.
- CLOSEST_PRIOR_STUDIES.csv: 10 nearest papers with DOIs, paradigm, decision variables,
  endpoints, overlap and concrete differences; access levels marked honestly.
- CITATION_ECOLOGY_AUDIT.md: 20 verified refs; 2 same-journal (Fonseca i Casas 2014,
  Yuan 2025) already cited appropriately; no padding added.
- NOVELTY_BOUNDARY.md: mandatory Yuan et al. 2025 deep comparison — they optimize lane
  opening schedules via DES+MILP on real arrivals; we study state-dependent release
  control with structural ablation and failure mapping. Distinct layer; independent
  contribution stands. Full text paywalled → one sub-question marked unresolved, not invented.

Remaining issues:
- Yuan et al. within-queue micro-dynamics unresolved (full text behind paywall); manuscript
  wording must not claim what they did not model — only that lane scheduling ≠ release control.

Commit: gate-01 SMPT scope + closest prior studies.
