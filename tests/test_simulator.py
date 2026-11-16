from __future__ import annotations

from dataclasses import replace

import numpy as np
import pytest

from airport_batch_queue.arrivals import generate_arrivals
from airport_batch_queue.config import (
    ArrivalConfig,
    ControlConfig,
    GeometryConfig,
    ServiceConfig,
    SimulationConfig,
    load_config,
)
from airport_batch_queue.service import sample_service_seconds
from airport_batch_queue.simulator import run_simulation


def compact_config(policy: str = "S0", seed: int = 41) -> SimulationConfig:
    return SimulationConfig(
        seed=seed,
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


def test_default_configuration_loads_and_validates():
    config = load_config("configs/default.yaml")
    assert config.control.policy == "S0"
    assert config.service.servers == 3


def test_simulation_is_deterministic_for_a_fixed_seed():
    first = run_simulation(compact_config())
    second = run_simulation(compact_config())
    assert first.summary == second.summary
    assert first.passenger_rows() == second.passenger_rows()


@pytest.mark.parametrize("policy", ["S0", "S1", "S2", "S3", "S4", "S5"])
def test_all_policies_complete_a_light_demand_scenario(policy: str):
    result = run_simulation(compact_config(policy=policy))
    assert result.summary["arrivals"] > 0
    assert result.summary["unfinished"] == 0
    assert result.summary["completed"] == result.summary["arrivals"]
    assert result.summary["mean_movement_distance_m"] > 0


def test_stationary_release_reduces_modeled_turning_and_stop_go_events():
    baseline = run_simulation(compact_config(policy="S0"))
    stationary = run_simulation(compact_config(policy="S1"))
    assert (
        stationary.summary["mean_turning_angle_degrees"]
        < baseline.summary["mean_turning_angle_degrees"]
    )
    assert stationary.summary["mean_movement_stops"] <= baseline.summary["mean_movement_stops"]


@pytest.mark.parametrize(
    "mode",
    ["poisson", "nonhomogeneous", "burst", "flight_bank", "batched"],
)
def test_arrival_modes_generate_sorted_arrivals(mode: str):
    config = ArrivalConfig(
        mode=mode,
        rate_per_hour=240,
        profile=((0, 120), (300, 360)),
        burst_size=6,
        burst_interval_seconds=200,
        batch_size=4,
        batch_interval_seconds=80,
    )
    arrivals = generate_arrivals(config, 600, np.random.default_rng(7))
    assert len(arrivals) > 0
    assert np.all(np.diff(arrivals) >= 0)
    assert np.all((arrivals >= 0) & (arrivals < 600))


@pytest.mark.parametrize("distribution", ["gamma", "lognormal", "mixture"])
def test_service_distributions_are_positive(distribution: str):
    config = ServiceConfig(
        distribution=distribution,
        secondary_probability=0,
        long_inspection_probability=0,
    )
    rng = np.random.default_rng(8)
    assert all(sample_service_seconds(config, rng) > 0 for _ in range(20))


def test_zero_demand_finishes_without_metrics_errors():
    config = replace(compact_config(), arrival=ArrivalConfig(rate_per_hour=0))
    result = run_simulation(config)
    assert result.summary["arrivals"] == 0
    assert result.summary["throughput_per_hour"] == 0
    assert result.summary["utilization"] == 0


def test_accessibility_minima_are_enforced():
    config = replace(
        compact_config(),
        geometry=GeometryConfig(accessible_route_width_m=0.8),
    )
    with pytest.raises(ValueError, match="Accessible route width"):
        config.validate()


def test_overload_is_retained_as_congestion_not_silently_dropped():
    config = replace(
        compact_config(),
        horizon_seconds=900,
        drain_limit_seconds=60,
        arrival=ArrivalConfig(rate_per_hour=900),
    )
    result = run_simulation(config)
    assert result.summary["max_upstream_waiting"] > 0
    assert result.summary["unfinished"] > 0
