# Phase 6 analytical and extreme-case validation

These checks test implementation invariants and directional extreme-case behavior. They do not validate a real airport or establish external predictive accuracy.

| Case | Assertion | Observed | Passed |
|---|---|---:|:---:|
| no_demand | zero arrivals produce zero completions | 0/0 | yes |
| conservation | arrivals equal completed plus unfinished | 80=80+0 | yes |
| route_accounting | B0 and B1 route values match configured geometry | 55.0/22.0 m; 1800.0/360.0 deg | yes |
| maximum_hold | undersized batch is eventually released | 30.67034340909347 | yes |
| full_lane_closure | zero active lanes produce zero completions | 0 | yes |
| lane_reduction | closing two lanes reduces horizon completions | 73>53 | yes |
| capacity_bound | completed count is positive and below the service upper bound | 73<=90 | yes |
| overload_retention | unfinished overload demand is retained | 1127 | yes |
| virtual_queue | virtual policy has no physical waiting area and uses its route | 0.0 m2; 18.0 m | yes |
| identical_footprint | primary B0/B1 capacity efficiency is identical by design | 1.4/1.4 | yes |

## Interpretation

Passenger conservation, exact route accounting, maximum-hold release, full lane closure, lane-capacity reduction, service-capacity bounds, overload retention, virtual-queue geometry, and identical-footprint capacity checks all pass.
The checks support internal correctness only. Calibration, real-site geometry, human behavioral validity, and empirical external validation remain outside the evidence base.
