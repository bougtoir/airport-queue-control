from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results" / "phase9"


def _rows(name: str) -> list[dict[str, str]]:
    with (RESULTS / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_phase9_benchmark_is_complete():
    manifest = json.loads((RESULTS / "run_manifest.json").read_text(encoding="utf-8"))
    assert manifest["scenario_count"] == 9
    assert manifest["policy_count"] == 3
    assert manifest["replications"] == 20
    assert manifest["replication_rows"] == 9 * 3 * 20
    assert len(_rows("policy_summary.csv")) == 27
    assert len(_rows("transferability_comparisons.csv")) == 18


def test_phase9_model_manifest_uses_portable_paths():
    manifest = json.loads(
        (ROOT / "results" / "checkpoints" / "phase9" / "manifest.json").read_text(
            encoding="utf-8"
        )
    )
    assert all(not Path(path).is_absolute() for path in manifest["model_files"])


def test_phase9_contains_all_generic_geometries_and_regimes():
    rows = _rows("replications.csv")
    assert {row["geometry_id"] for row in rows} == {
        "compact",
        "standard",
        "extended",
    }
    assert {row["regime_id"] for row in rows} == {
        "moderate",
        "peak",
        "disrupted",
    }
    assert {row["policy"] for row in rows} == {"S0", "S3", "S5"}
