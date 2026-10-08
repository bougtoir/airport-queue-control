# Phase 9 transferability benchmark

The open benchmark crosses three generic terminal geometries with three demand/service regimes and compares S0, S3, and S5 using 20 paired replications.

14 of 18 policy-scenario comparisons satisfy the paired 2% throughput criterion.

| Scenario | Policy | Throughput lower bound | Starts diff | Wait diff (s) | Acceptable |
|---|---|---:|---:|---:|---|
| compact_disrupted | S3 | 0.048 | -57.667 | -229.3 | yes |
| compact_disrupted | S5 | 0.004 | -57.667 | -83.0 | yes |
| compact_moderate | S3 | 0.004 | -0.022 | -20.2 | yes |
| compact_moderate | S5 | -0.035 | -0.022 | 72.8 | no |
| compact_peak | S3 | 0.003 | -7.886 | -43.3 | yes |
| compact_peak | S5 | -0.028 | -7.886 | 58.6 | no |
| extended_disrupted | S3 | 0.189 | -66.138 | -471.9 | yes |
| extended_disrupted | S5 | 0.142 | -66.138 | -327.7 | yes |
| extended_moderate | S3 | 0.010 | -0.140 | -41.4 | yes |
| extended_moderate | S5 | -0.023 | -0.140 | 59.4 | no |
| extended_peak | S3 | 0.029 | -7.970 | -105.5 | yes |
| extended_peak | S5 | -0.004 | -7.970 | 1.0 | yes |
| standard_disrupted | S3 | 0.112 | -62.393 | -344.3 | yes |
| standard_disrupted | S5 | 0.065 | -62.393 | -208.8 | yes |
| standard_moderate | S3 | 0.006 | -0.138 | -27.9 | yes |
| standard_moderate | S5 | -0.029 | -0.138 | 71.2 | no |
| standard_peak | S3 | 0.020 | -12.814 | -83.9 | yes |
| standard_peak | S5 | -0.014 | -12.814 | 20.8 | yes |

These generic cases demonstrate configuration portability, not universal external validity. Geometry, demand, and service inputs remain assumptions unless replaced by locally measured values.
