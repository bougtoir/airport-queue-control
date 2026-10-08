PYTHON := .venv/bin/python
PYTEST := .venv/bin/pytest
RUFF := .venv/bin/ruff

.PHONY: all reproduce test simulate geometry lock analyze validate optimize falsify benchmark structural figures tables manuscript audit package

all: simulate geometry lock analyze validate optimize falsify benchmark structural figures manuscript audit package test

reproduce: simulate geometry lock analyze validate optimize falsify benchmark structural figures test

test:
	$(RUFF) check src tests scripts
	$(PYTEST)

simulate:
	$(PYTHON) -m airport_batch_queue.cli configs/default.yaml --output results/phase2_smoke
	$(PYTHON) scripts/run_policy_smoke.py

geometry:
	$(PYTHON) scripts/run_phase3_geometry.py
	$(PYTHON) scripts/build_phase3_geometry_report.py

lock:
	$(PYTHON) scripts/lock_analysis_plan.py

analyze:
	$(PYTHON) scripts/run_phase5_design.py --replications 200
	$(PYTHON) scripts/analyze_phase5.py
	$(PYTHON) scripts/build_phase5_report.py

validate:
	$(PYTHON) scripts/run_phase6_validation.py

optimize:
	$(PYTHON) scripts/run_phase7_optimization.py
	$(PYTHON) scripts/analyze_phase7_optimization.py

falsify:
	$(PYTHON) scripts/run_phase8_falsification.py
	$(PYTHON) scripts/analyze_phase8_falsification.py

benchmark:
	$(PYTHON) scripts/run_phase9_benchmark.py
	$(PYTHON) scripts/analyze_phase9_benchmark.py

structural:
	$(PYTHON) scripts/run_phase13_structural_sensitivity.py

figures:
	$(PYTHON) scripts/build_phase10_outputs.py

tables: figures

manuscript:
	$(PYTHON) scripts/build_phase11_manuscript.py

audit:
	$(PYTHON) scripts/run_submission_audits.py

package:
	$(PYTHON) scripts/build_submission_package.py
