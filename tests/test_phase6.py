from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALIDATION_OUTPUT = ROOT / "results" / "phase6" / "validation_cases.csv"


def test_phase6_validation_cases_pass():
    with VALIDATION_OUTPUT.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 10
    assert all(row["passed"] == "yes" for row in rows)
    assert {row["case"] for row in rows} == {
        "no_demand",
        "conservation",
        "route_accounting",
        "maximum_hold",
        "full_lane_closure",
        "lane_reduction",
        "capacity_bound",
        "overload_retention",
        "virtual_queue",
        "identical_footprint",
    }
