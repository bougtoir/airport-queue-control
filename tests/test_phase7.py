from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results" / "phase7"


def _rows(name: str) -> list[dict[str, str]]:
    with (RESULTS / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_phase7_design_is_complete():
    manifest = json.loads((RESULTS / "run_manifest.json").read_text(encoding="utf-8"))
    assert manifest["design_count"] == 289
    assert manifest["replications_per_design_load"] == 10
    assert manifest["replication_rows"] == 289 * 2 * 10
    rows = _rows("replications.csv")
    assert len(rows) == manifest["replication_rows"]


def test_phase7_pareto_front_is_feasible_and_nondominated():
    summary = _rows("design_summary.csv")
    pareto = _rows("pareto_front.csv")
    assert pareto
    assert all(row["feasible"] == "yes" for row in pareto)
    assert all(row["pareto_efficient"] == "yes" for row in pareto)
    assert {row["design_id"] for row in pareto} == {
        row["design_id"]
        for row in summary
        if row["pareto_efficient"] == "yes"
    }
