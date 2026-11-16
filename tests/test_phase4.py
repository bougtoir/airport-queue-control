from __future__ import annotations

import hashlib
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def test_locked_analysis_plan_hash_matches():
    plan = ROOT / "ANALYSIS_PLAN_LOCKED.yaml"
    expected = (ROOT / "ANALYSIS_PLAN_LOCKED.sha256").read_text(
        encoding="utf-8"
    ).split()[0]
    assert hashlib.sha256(plan.read_bytes()).hexdigest() == expected


def test_primary_analysis_is_prespecified():
    plan = yaml.safe_load(
        (ROOT / "ANALYSIS_PLAN_LOCKED.yaml").read_text(encoding="utf-8")
    )
    primary = plan["primary_comparison"]
    assert primary["intervention"] == "S3"
    assert primary["baseline"] == "S0"
    assert primary["intervention_layout"] == "B1"
    assert primary["baseline_layout"] == "B0"
    assert primary["throughput_relative_noninferiority_margin"] == 0.02
    assert primary["movement_endpoints"] == [
        "mean_movement_starts",
        "mean_movement_stops",
        "mean_turning_angle_degrees",
        "mean_movement_distance_m",
    ]
    assert primary["spatial_endpoints"] == [
        "capacity_efficiency_passengers_per_m2",
        "required_waiting_area_m2_at_density_limit",
    ]
    assert plan["replications"]["common_random_numbers"] is True
    assert plan["load_regimes"] == [0.50, 0.70, 0.85, 0.95, 1.00, 1.15]
