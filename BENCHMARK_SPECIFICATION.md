# Transferability benchmark specification

The benchmark isolates generic control logic from configurable facility and operating inputs. It
does not represent named terminals.

## Scenario matrix

`configs/phase9_benchmark.yaml` crosses three generic geometries (`compact`, `standard`, and
`extended`) with three operating regimes (`moderate`, `peak`, and `disrupted`). Each scenario
runs S0 conventional switchback, S3 threshold release, and S5 virtual-queue benchmark with 20
common-random-number replications.

Geometry configuration includes facility dimensions, modeled waiting and screening areas,
barrier and corridor footprint, row count, route distances, and downstream capacity. Operating
regimes configure nominal load, arrival process, service-time variability, and lane schedules.
The policy algorithms remain unchanged across scenarios.

## Machine-readable outputs

- `results/phase9/replications.csv`: one row per scenario, policy, and replication, followed by
  the scalar fields defined in `OUTPUT_SCHEMA.md`.
- `results/phase9/policy_summary.csv`: policy means by generic scenario.
- `results/phase9/transferability_comparisons.csv`: paired S3/S5 differences from S0, confidence
  intervals, and the 2% throughput-acceptability indicator.
- `results/phase9/run_manifest.json`: source/configuration hash and completeness counts.

The benchmark demonstrates configuration portability only. It does not establish external
validity for an airport without site-specific geometry, demand, service, passenger, and
implementation data.
