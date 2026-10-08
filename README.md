# Airport stationary batch-release queue

This repository evaluates whether airport-security waiting can be separated from repeated
pedestrian movement. It compares a conventional serpentine queue with stationary rows,
sub-batches, threshold release, predictive release, and a virtual-queue benchmark.

The study is a **generic, parameterized simulation**, not a representation of a named airport.
Empirical inputs, standards, engineering assumptions, and sensitivity ranges are labeled
separately. No physiological or safety effect is inferred from modeled movement endpoints.

## Reproduction

```bash
python3 -m venv .venv
.venv/bin/pip install -e '.[dev]'
make reproduce
```

`make reproduce` regenerates every reported numerical result, figure, and table from the
versioned configurations and local simulation code, then runs lint and the test suite. No
external dataset download is required: all model inputs are the documented parameters in
`configs/`, `ANALYSIS_PLAN_LOCKED.yaml`, and `references/parameter_sources.csv`.

Individual stages:

```bash
make simulate     # smoke scenario and policy check
make geometry     # B0–B4 layout, row-angle, and footprint screen
make lock         # verify the frozen primary analysis-plan hash
make analyze      # paired Monte Carlo design (200 replications per cell)
make validate     # analytical and extreme-case validation
make optimize     # engineering design grid and Pareto front
make falsify      # prespecified stress campaign and failure-region map
make benchmark    # geometry-by-regime transferability matrix
make structural   # matched-route structural sensitivity
make figures      # all figures (PNG/SVG/PDF, editable PPTX) and CSV/DOCX tables
make test         # lint and tests
```

Run one resolved scenario directly:

```bash
.venv/bin/python -m airport_batch_queue.cli configs/default.yaml \
  --output results/example
```

The simulator writes a scalar summary, passenger-level event ledger, queue trajectory, and
resolved configuration. `MODEL_SPECIFICATION.md` defines the staged model and limitations;
`OUTPUT_SCHEMA.md` defines the generated fields; `BENCHMARK_SPECIFICATION.md` defines the
transferability benchmark.

## Outputs

- `results/`: machine-readable replication, summary, and figure-source CSV files.
- `figures/`, `supplementary_figures/`: generated figures.
- `tables/`, `supplementary_tables/`: generated CSV and editable DOCX tables.
- `PHASE_*_REPORT.md`, `FAILURE_MODES.md`, `ROBUSTNESS_MAP.csv`: generated numerical reports.

Release-surge and conflict outputs are engineering proxies, not validated safety outcomes.
Generated values must not be edited manually; rerun the pipeline instead.
