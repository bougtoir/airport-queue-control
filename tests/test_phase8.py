from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results" / "phase8"


def _rows(name: str) -> list[dict[str, str]]:
    with (RESULTS / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_phase8_campaign_is_complete():
    manifest = json.loads((RESULTS / "run_manifest.json").read_text(encoding="utf-8"))
    assert manifest["scenario_count"] == 41
    assert manifest["replications_per_policy_scenario"] == 30
    assert manifest["replication_rows"] == 41 * 30 * 2
    assert len(_rows("scenario_comparisons.csv")) == 41


def test_phase8_retains_failures_and_nulls():
    comparisons = _rows("scenario_comparisons.csv")
    failures = _rows("failure_regions.csv")
    assert failures
    assert any(row["movement_null"] == "yes" for row in comparisons)
    assert any(row["release_surge_failure"] == "yes" for row in comparisons)
    assert any(row["conflict_proxy_failure"] == "yes" for row in comparisons)
    assert {row["scenario_id"] for row in failures} == {
        row["scenario_id"]
        for row in comparisons
        if row["failure_detected"] == "yes"
    }
