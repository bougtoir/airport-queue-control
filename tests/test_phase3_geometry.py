from __future__ import annotations

import csv
from dataclasses import replace
from pathlib import Path

import pytest

from airport_batch_queue.config import (
    ArrivalConfig,
    ControlConfig,
    GeometryConfig,
    ServiceConfig,
    SimulationConfig,
)
from airport_batch_queue.simulator import run_simulation


def compact_config(policy: str = "S0") -> SimulationConfig:
    return SimulationConfig(
        seed=41,
        horizon_seconds=600,
        drain_limit_seconds=1800,
        arrival=ArrivalConfig(rate_per_hour=180),
        service=ServiceConfig(
            servers=2,
            mean_seconds=30,
            cv=0.4,
            secondary_probability=0,
            long_inspection_probability=0,
        ),
        control=ControlConfig(
            policy=policy,
            batch_size=6,
            sub_batch_size=3,
            downstream_threshold=3,
            decision_interval_seconds=2,
            maximum_hold_seconds=30,
        ),
    )


def test_layout_and_angle_change_explicit_movement_endpoints():
    base = compact_config(policy="S3")
    switchback = run_simulation(
        replace(base, geometry=replace(base.geometry, layout="B0"))
    )
    angled_rows = run_simulation(
        replace(
            base,
            geometry=replace(
                base.geometry,
                layout="B1",
                row_angle_degrees=30,
            ),
        )
    )
    assert (
        angled_rows.summary["mean_movement_distance_m"]
        < switchback.summary["mean_movement_distance_m"]
    )
    assert (
        angled_rows.summary["mean_turning_angle_degrees"]
        < switchback.summary["mean_turning_angle_degrees"]
    )
    assert angled_rows.summary["mean_luggage_rotation_degrees"] > 0


def test_static_and_moving_footprints_remain_separate():
    result = run_simulation(compact_config(policy="S3"))
    assert result.summary["mean_moving_footprint_m2"] > result.summary[
        "mean_static_footprint_m2"
    ]
    assert result.summary["acceptable_waiting_capacity"] > 0
    assert result.summary["capacity_efficiency_passengers_per_m2"] > 0


def test_lane_schedule_changes_available_screening_capacity():
    base = compact_config()
    scheduled = replace(
        base,
        service=replace(
            base.service,
            lane_schedule=((0.0, 1), (300.0, 2)),
        ),
    )
    result = run_simulation(scheduled)
    assert min(row["active_servers"] for row in result.trajectories) == 1
    assert max(row["active_servers"] for row in result.trajectories) == 2


def test_invalid_geometry_and_lane_schedule_are_rejected():
    with pytest.raises(ValueError, match="full geometry"):
        replace(
            compact_config(),
            geometry=GeometryConfig(barrier_footprint_m2=110),
        ).validate()
    with pytest.raises(ValueError, match="active lanes"):
        replace(
            compact_config(),
            service=ServiceConfig(servers=2, lane_schedule=((0.0, 3),)),
        ).validate()


def test_phase3_screen_contains_all_prespecified_cases():
    path = Path("results/phase3_space_guidance/layout_angle_screen.csv")
    if not path.exists():
        pytest.skip("Phase 3 screen has not been generated")
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 153
    assert {row["layout"] for row in rows} == {"B0", "B1", "B2", "B3", "B4"}
    assert {float(row["row_angle_degrees"]) for row in rows if row["layout"] != "B0"} == {
        0,
        15,
        30,
        45,
    }
    assert {row["footprint_case"] for row in rows} == {"low", "base", "high"}
