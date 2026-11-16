# Phase 8 active falsification and failure-region map

41 prespecified stress scenarios were tested with paired S3-versus-S0 replications. 36 meet at least one failure criterion.

Criterion counts: throughput=1; movement null=1; waiting=1; space=1; unfinished demand=0; release-surge proxy=34; conflict proxy=34; staffing=1.

Release-surge and conflict criteria are prespecified engineering-proxy ratio screens, not empirical safety thresholds or evidence of injury risk.

| Proxy ratio threshold | Release-surge flags | Conflict-proxy flags |
|---:|---:|---:|
| 1.25 | 39 | 38 |
| 1.50 | 37 | 36 |
| 2.00 | 34 | 34 |
| 3.00 | 28 | 27 |
| 4.00 | 2 | 13 |

Flag counts vary with the arbitrary screening ratio; operational throughput, waiting, area, and unfinished-demand criteria do not use these proxy thresholds.

| Scenario | Category | Load | Failure labels | Throughput lower bound | Starts diff | Wait diff (s) |
|---|---|---:|---|---:|---:|---:|
| angle_045 | geometry | 0.95 | release_surge_proxy;conflict_proxy | 0.013 | -8.790 | -50.5 |
| arrivals_batched | arrival_process | 0.95 | conflict_proxy | 0.007 | -3.782 | -34.8 |
| arrivals_burst | arrival_process | 0.95 | release_surge_proxy;conflict_proxy | 0.203 | -58.674 | -553.8 |
| arrivals_flight_bank | arrival_process | 0.95 | release_surge_proxy;conflict_proxy | 0.303 | -72.874 | -707.7 |
| capacity_012 | downstream_capacity | 0.95 | release_surge_proxy;conflict_proxy | 0.013 | -9.404 | -58.3 |
| capacity_024 | downstream_capacity | 0.95 | release_surge_proxy;conflict_proxy | 0.009 | -5.710 | -41.7 |
| combined_lane_burst | combined | 1.15 | release_surge_proxy;conflict_proxy | 0.271 | -82.663 | -290.1 |
| combined_low_long_hold | combined | 0.50 | release_surge_proxy | 0.001 | -0.505 | -27.8 |
| compliance_050 | compliance | 0.95 | release_surge_proxy;conflict_proxy | 0.017 | -8.728 | -73.0 |
| compliance_080 | compliance | 0.95 | release_surge_proxy;conflict_proxy | 0.014 | -6.812 | -49.3 |
| compliance_100 | compliance | 0.95 | release_surge_proxy;conflict_proxy | 0.012 | -6.936 | -51.3 |
| cv_020 | service_variability | 0.95 | release_surge_proxy;conflict_proxy | 0.008 | -4.762 | -36.1 |
| cv_100 | service_variability | 0.95 | release_surge_proxy;conflict_proxy | 0.011 | -5.821 | -50.1 |
| cv_150 | service_variability | 0.95 | release_surge_proxy;conflict_proxy | 0.035 | -11.061 | -100.6 |
| footprint_high | footprint | 0.95 | release_surge_proxy;conflict_proxy | 0.012 | -7.083 | -53.2 |
| hold_030 | control | 0.95 | release_surge_proxy;conflict_proxy | 0.008 | -4.196 | -35.8 |
| hold_300 | control | 0.95 | release_surge_proxy;conflict_proxy | 0.021 | -11.077 | -81.0 |
| lanes_close_reopen | lane_shock | 0.95 | release_surge_proxy;conflict_proxy | 0.201 | -44.922 | -400.0 |
| lanes_one | lane_shock | 0.95 | release_surge_proxy;conflict_proxy | 0.011 | -51.903 | -19.9 |
| lanes_two | lane_shock | 0.95 | release_surge_proxy;conflict_proxy | 0.023 | -32.879 | -107.8 |
| load_050 | load | 0.50 | movement_null | 0.006 | -0.000 | -27.9 |
| load_085 | load | 0.85 | release_surge_proxy;conflict_proxy | 0.002 | -2.290 | -38.0 |
| load_095 | load | 0.95 | release_surge_proxy;conflict_proxy | 0.010 | -6.134 | -40.7 |
| load_100 | load | 1.00 | release_surge_proxy;conflict_proxy | 0.015 | -7.766 | -48.0 |
| load_115 | load | 1.15 | release_surge_proxy;conflict_proxy | 0.164 | -51.142 | -474.3 |
| load_130 | load | 1.30 | release_surge_proxy;conflict_proxy | 0.238 | -67.264 | -601.6 |
| narrow_gate | geometry | 0.95 | release_surge_proxy;conflict_proxy | 0.013 | -7.463 | -58.5 |
| restricted_space | geometry | 0.95 | release_surge_proxy;conflict_proxy | 0.009 | -6.168 | -46.5 |
| s3_bad_control | combined | 0.95 | throughput;waiting;space;release_surge_proxy;conflict_proxy | -0.047 | -5.296 | 82.9 |
| s3_batch_024 | controller_failure | 0.95 | release_surge_proxy;conflict_proxy | 0.008 | -4.004 | -33.3 |
| s3_decision_030 | controller_failure | 0.95 | release_surge_proxy;conflict_proxy | 0.011 | -7.415 | -34.1 |
| s3_decision_060 | controller_failure | 0.95 | release_surge_proxy;conflict_proxy | -0.008 | -6.034 | 4.0 |
| s3_gate_005 | guidance_delay | 0.95 | release_surge_proxy;conflict_proxy | 0.007 | -5.713 | -36.1 |
| s3_gate_015 | guidance_delay | 0.95 | release_surge_proxy;conflict_proxy | 0.008 | -7.966 | -42.5 |
| s3_staff_zero | staffing | 0.95 | release_surge_proxy;conflict_proxy;staffing | 0.013 | -8.683 | -60.5 |
| s3_threshold_zero_hold | controller_failure | 0.95 | release_surge_proxy;conflict_proxy | -0.017 | -8.244 | 10.4 |

## Structural limitation exposed by falsification

Distance and turning advantages are encoded by the B0/B1 route definitions, so this simulator cannot falsify those two endpoints without changing the geometry model. The campaign can erase the stop-go benefit or expose operational trade-offs, but it cannot independently validate a route advantage that is an input assumption. The staffing screen also exposes that staffing is tracked but does not currently alter simulated release performance.
