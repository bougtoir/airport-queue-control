# Phase 7 multi-objective Pareto optimization

The grid contains 289 designs; 239 satisfy the prespecified operational constraints and 8 are nondominated.
No weighted composite determines the result. Pareto status jointly considers movement starts, stops, turning, distance, waiting, required area, and throughput. Staffing is retained as a design descriptor but excluded because it does not alter simulator dynamics.

| Design | Policy/layout | Angle | Staff | Starts | Wait (s) | Area (m2) | Throughput/h |
|---|---|---:|---:|---:|---:|---:|---:|
| S3_B2_a00_b16_s04_t06 | S3/B2 | 0 | 0 | 1.000 | 71.6 | 8.6 | 406.2 |
| S3_B2_a00_b12_s04_t10 | S3/B2 | 0 | 0 | 1.000 | 71.8 | 6.6 | 405.9 |
| S3_B3_a00_b16_s04_t06 | S3/B3 | 0 | 1 | 1.000 | 71.3 | 8.6 | 406.0 |
| S3_B3_a00_b08_s04_t10 | S3/B3 | 0 | 1 | 1.000 | 71.4 | 6.7 | 405.9 |
| S3_B3_a00_b16_s04_t10 | S3/B3 | 0 | 1 | 1.000 | 71.5 | 6.6 | 405.9 |
| S3_B3_a00_b12_s04_t10 | S3/B3 | 0 | 1 | 1.000 | 71.5 | 6.6 | 406.1 |
| S3_B4_a00_b12_s04_t10 | S3/B4 | 0 | 1 | 1.000 | 71.9 | 6.5 | 405.9 |
| S2_B3_a00_b12_s02_t06 | S2/B3 | 0 | 1 | 1.000 | 77.8 | 3.3 | 404.8 |

The grid is an engineering design search, not proof of global optimality. Phase 8 maps failure regions beyond the feasible grid.
