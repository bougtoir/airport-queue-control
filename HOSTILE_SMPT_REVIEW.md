# HOSTILE_SMPT_REVIEW — Gate 7 (skeptical SMPT editor + 2 reviewers)

| # | Criticism | Evidence in manuscript | Severity | Action taken | Residual limitation |
|---|---|---|---|---|---|
| a | Overlap with Yuan et al. 2025 and closest work | Yuan plans lane-opening schedules via DES+MILP on real arrivals; we control release of stored demand. Distinct decision layer. Intro now differentiates explicitly [8]. | Medium | Added direct differentiation sentence; cover letter states complementarity. | Yuan full text paywalled; micro-dynamics sub-question unresolved — wording restricted to documented scope. |
| b | S0 progression rule not externally validated | Stated repeatedly: model-imposed convention; starts/stops are "model-dependent", "not a field-estimated behavioral effect"; field-pilot paragraph lists required measurements. | High (potential desk reject if overstated) | No overstatement found; disclosure retained verbatim. | Fundamental: only field trajectories can validate; honestly disclosed. |
| c | Start reduction simply encoded by design | Acknowledged: S3 assigns 1 start by construction; matched-route ablation shows contrast is not solely route-driven; all nondominated designs have 1.0 starts by construction and movement is excluded from ranking interpretation. | Medium | Manuscript already reports mechanism explicitly; Figure 6 caption notes construction. | The starts contrast is definitionally partly tautological; presented as such. |
| d | Novel simulation methodology vs routine application | Contribution: explicit state/action/safeguard interface + progression accounting + matched-route ablation + falsification failure-map. This is methodology+experimentation, in SMPT scope ("sensitivity analysis, experimental design, V&V"). | Medium | Reframed Abstract/Discussion/Conclusion as simulation-framework contribution. | Editors may still see it as applied; mitigated by transparent V&V and benchmark release. |
| e | No real checkpoint calibration | Disclosed: synthetic passengers, generic geometry, no calibration; Yuan used real arrivals. | High | Limitation stated; matched-route + benchmark used instead. | Unfixable without field data — disclosed, not hidden. |
| f | Precision target unmet | Reported: achieved 0.439/1.087 vs 0.100; required 3,805/23,359; direction-only interpretation. | Medium | Retained prominently (Results ¶3). | None — honest negative finding. |
| g | Distance/turning predetermined | Classified "structural" in manuscript and endpoint table; not promoted as findings. | Low | Already handled; Table 4 zeros. | None. |
| h | Nominal capacity not improved | Identical-footprint capacity efficiency 0.0 diff reported; "no increased safe capacity" claim. | Low | Retained. | None. |
| i | Surge/conflict proxies unvalidated | Labeled "unvalidated engineering screens"; threshold sensitivity 1.25–4.00 shown; flagged 34/34 not called safety outcomes. | Medium | Retained with explicit labels in Table 5 and text. | Proxies remain unvalidated. |
| j | Optimization adds little beyond built-in S3 one-start | All 8 nondominated designs have 1.0 starts by construction; manuscript states movement did not rank the frontier — trade-offs were waiting/area/throughput. Figure 7 maps controller tuning failure region instead. | Medium | Already disclosed; frontier read correctly. | Movement objective is degenerate by construction; stated. |

## Verdict
No unaddressed fatal novelty/methodological issue. The two structural weaknesses
(no field validation, model-imposed progression rule) are disclosed rather than
obscured, which is the defensible SMPT posture. No NO-GO triggered.
