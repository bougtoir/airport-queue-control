# Phase 5 comparative-design and Monte Carlo precision report

This report is generated from the locked-plan replication outputs. It is not a manually edited result source.

## Locked primary comparison

| Load | Endpoint | S0 mean | S3-S0 | 95% CI | Throughput acceptable |
|---:|---|---:|---:|---:|:---:|
| 0.85 | capacity_efficiency_passengers_per_m2 | 1.400 | 0.000 | [0.000, 0.000] | not_applicable |
| 0.85 | mean_movement_distance_m | 55.000 | -33.000 | [-33.000, -33.000] | not_applicable |
| 0.85 | mean_movement_starts | 2.475 | -1.475 | [-1.914, -1.036] | not_applicable |
| 0.85 | mean_movement_stops | 1.475 | -1.475 | [-1.914, -1.036] | not_applicable |
| 0.85 | mean_turning_angle_degrees | 1800.000 | -1440.000 | [-1440.000, -1440.000] | not_applicable |
| 0.85 | required_waiting_area_m2_at_density_limit | 8.507 | -0.689 | [-1.188, -0.190] | not_applicable |
| 0.85 | throughput_per_hour | 384.395 | 3.950 | [3.417, 4.483] | yes |
| 0.95 | capacity_efficiency_passengers_per_m2 | 1.400 | 0.000 | [0.000, 0.000] | not_applicable |
| 0.95 | mean_movement_distance_m | 55.000 | -33.000 | [-33.000, -33.000] | not_applicable |
| 0.95 | mean_movement_starts | 7.341 | -6.341 | [-7.428, -5.253] | not_applicable |
| 0.95 | mean_movement_stops | 6.341 | -6.341 | [-7.428, -5.253] | not_applicable |
| 0.95 | mean_turning_angle_degrees | 1800.000 | -1440.000 | [-1440.000, -1440.000] | not_applicable |
| 0.95 | required_waiting_area_m2_at_density_limit | 18.671 | -5.243 | [-6.577, -3.909] | not_applicable |
| 0.95 | throughput_per_hour | 418.175 | 8.480 | [6.998, 9.962] | yes |

## Precision decision

The design reached the prespecified routine cap of 200 paired replications per load-policy cell.
Current precision results are:

| Load | Endpoint | Achieved half-width | Target | Estimated replications | Met |
|---:|---|---:|---:|---:|:---:|
| 0.85 | capacity_efficiency_passengers_per_m2 | 0.000 | 0.020 | 1 | yes |
| 0.85 | mean_movement_distance_m | 0.000 | 0.250 | 1 | yes |
| 0.85 | mean_movement_starts | 0.439 | 0.100 | 3805 | no |
| 0.85 | mean_movement_stops | 0.439 | 0.100 | 3805 | no |
| 0.85 | mean_turning_angle_degrees | 0.000 | 15.000 | 1 | yes |
| 0.85 | required_waiting_area_m2_at_density_limit | 0.499 | 2.000 | 13 | yes |
| 0.85 | throughput_per_hour | 0.533 | 3.844 | 4 | yes |
| 0.95 | capacity_efficiency_passengers_per_m2 | 0.000 | 0.020 | 1 | yes |
| 0.95 | mean_movement_distance_m | 0.000 | 0.250 | 1 | yes |
| 0.95 | mean_movement_starts | 1.087 | 0.100 | 23359 | no |
| 0.95 | mean_movement_stops | 1.087 | 0.100 | 23359 | no |
| 0.95 | mean_turning_angle_degrees | 0.000 | 15.000 | 1 | yes |
| 0.95 | required_waiting_area_m2_at_density_limit | 1.334 | 2.000 | 88 | yes |
| 0.95 | throughput_per_hour | 1.482 | 4.182 | 25 | yes |

Unmet precision targets are retained as limitations rather than silently relaxed. Phase 6 validation must assess whether large between-replication variability reflects load sensitivity, the S0 stop-go abstraction, or both.
