from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PHASE5_OUTPUT = ROOT / "results" / "phase5" / "replications.csv"
PHASE5_MANIFEST = ROOT / "results" / "phase5" / "run_manifest.json"


@pytest.mark.skipif(not PHASE5_OUTPUT.exists(), reason="Phase 5 outputs not generated")
def test_phase5_outputs_are_complete_and_paired():
    rows = list(
        csv.DictReader(
            PHASE5_OUTPUT.open(
                newline="",
                encoding="utf-8",
            )
        )
    )
    assert len(rows) == 6 * 6 * 200
    groups: dict[tuple[str, str], list[dict[str, str]]] = {}
    for row in rows:
        groups.setdefault((row["load_regime"], row["replication"]), []).append(row)
    assert all(
        {row["policy"] for row in group} == {"S0", "S1", "S2", "S3", "S4", "S5"}
        for group in groups.values()
    )
    assert all(len({row["seed"] for row in group}) == 1 for group in groups.values())


@pytest.mark.skipif(not PHASE5_MANIFEST.exists(), reason="Phase 5 outputs not generated")
def test_checkpoint_manifest_uses_locked_plan():
    manifest = json.loads(PHASE5_MANIFEST.read_text(encoding="utf-8"))
    expected = (ROOT / "ANALYSIS_PLAN_LOCKED.sha256").read_text(encoding="utf-8").split()[0]
    assert manifest["plan_sha256"] == expected
    assert manifest["replications_per_cell"] == 200
    assert manifest["replication_rows"] == 7200
    assert manifest["seed_rows"] == 1200
    assert len(manifest["model_sha256"]) == 64
    assert all(not Path(path).is_absolute() for path in manifest["model_files"])


@pytest.mark.skipif(not PHASE5_OUTPUT.exists(), reason="Phase 5 outputs not generated")
def test_unmet_precision_targets_are_retained():
    path = ROOT / "results" / "phase5" / "monte_carlo_precision.csv"
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    primary = [
        row
        for row in rows
        if row["policy"] == "S3"
        and row["load_regime"] in {"0.85", "0.95"}
        and row["endpoint"] in {"mean_movement_starts", "mean_movement_stops"}
    ]
    assert len(primary) == 4
    assert all(row["target_met"] == "no" for row in primary)
