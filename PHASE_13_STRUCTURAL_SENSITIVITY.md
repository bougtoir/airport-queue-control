# Phase 13 structural route sensitivity

This analysis holds the S0 and S3 path distance and turn count equal at short, mid, and long route definitions. It tests whether the movement-start and throughput comparisons require the configured B0/B1 route advantage.

| Scenario | Load | Throughput difference/h (95% CI) | Starts difference (95% CI) | Throughput criterion |
|---|---:|---:|---:|---|
| configured_routes | 0.85 | 2.9 (2.5, 3.4) | -0.91 (-1.27, -0.56) | yes |
| configured_routes | 0.95 | 6.0 (4.1, 7.9) | -4.20 (-5.53, -2.86) | yes |
| matched_short_route | 0.85 | -0.1 (-0.3, 0.1) | -0.46 (-0.69, -0.24) | yes |
| matched_short_route | 0.95 | 0.1 (-0.2, 0.4) | -2.59 (-3.51, -1.66) | yes |
| matched_mid_route | 0.85 | -0.0 (-0.1, 0.1) | -0.65 (-0.93, -0.37) | yes |
| matched_mid_route | 0.95 | 0.6 (0.0, 1.1) | -3.11 (-4.12, -2.10) | yes |
| matched_long_route | 0.85 | -0.6 (-0.9, -0.3) | -0.91 (-1.27, -0.56) | yes |
| matched_long_route | 0.95 | 1.2 (-0.4, 2.8) | -4.20 (-5.53, -2.86) | yes |

The throughput criterion is retained in 6 of 6 matched-route cases. Distance and turning differences become zero by design. The remaining movement-start contrast is not solely route-length or turning driven, but remains conditional on the explicit queue-progression and release-control rules rather than externally validated.
