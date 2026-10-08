from __future__ import annotations

from collections.abc import Sequence
from itertools import pairwise

import numpy as np

from airport_batch_queue.config import SimulationConfig
from airport_batch_queue.entities import Passenger, Server
from airport_batch_queue.geometry import resolved_layout, usable_waiting_area_m2

MetricValue = float | int | str


def _mean(values: Sequence[float]) -> float:
    return float(np.mean(values)) if values else 0.0


def _quantile(values: Sequence[float], probability: float) -> float:
    return float(np.quantile(values, probability)) if values else 0.0


def _gini(values: Sequence[float]) -> float:
    if not values:
        return 0.0
    array = np.sort(np.asarray(values, dtype=float))
    total = float(array.sum())
    if total == 0:
        return 0.0
    ranks = np.arange(1, len(array) + 1)
    return float((2 * np.sum(ranks * array) / (len(array) * total)) - (len(array) + 1) / len(array))


def summarize(
    config: SimulationConfig,
    passengers: list[Passenger],
    servers: list[Server],
    trajectories: list[dict[str, float]],
    run_end_seconds: float,
    release_sizes: list[int],
) -> dict[str, MetricValue]:
    completed = [passenger for passenger in passengers if passenger.completion_time is not None]
    started = [passenger for passenger in passengers if passenger.service_start is not None]
    waits = [
        passenger.service_start - passenger.arrival_time
        for passenger in started
        if passenger.service_start is not None
    ]
    upstream_waits = [
        passenger.release_time - passenger.arrival_time
        for passenger in passengers
        if passenger.release_time is not None
    ]
    downstream_waits = [
        passenger.service_start - passenger.screening_queue_arrival
        for passenger in started
        if passenger.service_start is not None and passenger.screening_queue_arrival is not None
    ]
    system_times = [
        passenger.completion_time - passenger.arrival_time
        for passenger in completed
        if passenger.completion_time is not None
    ]
    released = [passenger for passenger in passengers if passenger.release_time is not None]
    movement_distances = [passenger.movement_distance_m for passenger in released]
    movement_times = [passenger.movement_time_seconds for passenger in released]
    stationary_times = [
        max(wait - passenger.movement_time_seconds, 0.0)
        for passenger, wait in zip(started, waits, strict=True)
    ]
    luggage_waits = [
        passenger.service_start - passenger.arrival_time
        for passenger in started
        if passenger.has_luggage and passenger.service_start is not None
    ]
    no_luggage_waits = [
        passenger.service_start - passenger.arrival_time
        for passenger in started
        if not passenger.has_luggage and passenger.service_start is not None
    ]
    reduced_waits = [
        passenger.service_start - passenger.arrival_time
        for passenger in started
        if passenger.reduced_mobility and passenger.service_start is not None
    ]
    typical_waits = [
        passenger.service_start - passenger.arrival_time
        for passenger in started
        if not passenger.reduced_mobility and passenger.service_start is not None
    ]
    group_waits = [
        passenger.service_start - passenger.arrival_time
        for passenger in started
        if passenger.group_id is not None and passenger.service_start is not None
    ]
    solo_waits = [
        passenger.service_start - passenger.arrival_time
        for passenger in started
        if passenger.group_id is None and passenger.service_start is not None
    ]
    queue_values = [row["downstream_queue"] for row in trajectories]
    waiting_values = [row["upstream_waiting"] for row in trajectories]
    density_values = [row["waiting_density_per_m2"] for row in trajectories]
    movers_values = [row["in_transit"] for row in trajectories]
    waiting_footprints = [
        row["upstream_static_footprint_m2"] for row in trajectories
    ]
    moving_density_values = [
        row["moving_footprint_density_per_m2"] for row in trajectories
    ]
    release_surge_values = [row["release_surge_index"] for row in trajectories]
    total_server_time = (
        sum(row["active_servers"] for row in trajectories)
        * config.time_step_seconds
    )
    busy_seconds = sum(
        max(
            min(
                passenger.completion_time
                if passenger.completion_time is not None
                else run_end_seconds,
                run_end_seconds,
            )
            - passenger.service_start,
            0.0,
        )
        for passenger in started
        if passenger.service_start is not None
    )
    starvation_seconds = sum(server.starvation_seconds for server in servers)
    completed_within_horizon = sum(
        passenger.completion_time is not None
        and passenger.completion_time <= config.horizon_seconds
        for passenger in passengers
    )
    physical_waiting_area = (
        0.0 if config.control.policy == "S5" else usable_waiting_area_m2(config)
    )
    peak_waiting_count = max(waiting_values, default=0.0)
    peak_waiting_footprint = max(waiting_footprints, default=0.0)
    density_required_area = (
        peak_waiting_count / config.geometry.max_waiting_density_per_m2
    )
    required_waiting_area = max(density_required_area, peak_waiting_footprint)
    mean_static_footprint = _mean(
        [passenger.static_footprint_m2 for passenger in passengers]
    )
    acceptable_capacity = (
        min(
            physical_waiting_area * config.geometry.max_waiting_density_per_m2,
            physical_waiting_area / mean_static_footprint,
        )
        if physical_waiting_area > 0 and mean_static_footprint > 0
        else 0.0
    )
    service_order = [
        passenger.passenger_id
        for passenger in sorted(
            started,
            key=lambda passenger: (
                passenger.service_start
                if passenger.service_start is not None
                else float("inf"),
                passenger.passenger_id,
            ),
        )
    ]
    out_of_arrival_order = sum(
        passenger_id < prior_id
        for prior_id, passenger_id in pairwise(service_order)
    )

    return {
        "policy": config.control.policy,
        "layout": resolved_layout(config),
        "seed": config.seed,
        "arrival_mode": config.arrival.mode,
        "service_distribution": config.service.distribution,
        "arrivals": len(passengers),
        "service_started": len(started),
        "completed": len(completed),
        "unfinished": len(passengers) - len(completed),
        "completed_within_horizon": completed_within_horizon,
        "throughput_per_hour": completed_within_horizon * 3600.0 / config.horizon_seconds,
        "run_end_seconds": run_end_seconds,
        "utilization": busy_seconds / total_server_time if total_server_time else 0.0,
        "starvation_fraction_with_upstream_demand": (
            starvation_seconds / total_server_time if total_server_time else 0.0
        ),
        "mean_wait_seconds": _mean(waits),
        "wait_sd_seconds": float(np.std(waits, ddof=1)) if len(waits) > 1 else 0.0,
        "maximum_fifo_delay_seconds": max(waits, default=0.0),
        "p50_wait_seconds": _quantile(waits, 0.50),
        "p90_wait_seconds": _quantile(waits, 0.90),
        "p95_wait_seconds": _quantile(waits, 0.95),
        "p99_wait_seconds": _quantile(waits, 0.99),
        "mean_upstream_wait_seconds": _mean(upstream_waits),
        "mean_downstream_wait_seconds": _mean(downstream_waits),
        "mean_stationary_time_seconds": _mean(stationary_times),
        "mean_system_time_seconds": _mean(system_times),
        "mean_movement_distance_m": _mean(movement_distances),
        "mean_movement_time_seconds": _mean(movement_times),
        "mean_movement_starts": _mean([passenger.movement_starts for passenger in released]),
        "mean_movement_stops": _mean([passenger.movement_stops for passenger in released]),
        "mean_turning_angle_degrees": _mean(
            [passenger.cumulative_turning_angle_degrees for passenger in released]
        ),
        "mean_luggage_rotation_degrees": _mean(
            [passenger.luggage_rotation_degrees for passenger in released]
        ),
        "mean_static_footprint_m2": mean_static_footprint,
        "mean_moving_footprint_m2": _mean(
            [passenger.moving_footprint_m2 for passenger in passengers]
        ),
        "mean_movement_conflict_proxy": _mean(
            [passenger.movement_conflict_proxy for passenger in released]
        ),
        "intervention_count": sum(
            passenger.intervention_required for passenger in released
        ),
        "mean_downstream_queue": _mean(queue_values),
        "max_downstream_queue": max(queue_values, default=0.0),
        "mean_upstream_waiting": _mean(waiting_values),
        "max_upstream_waiting": max(waiting_values, default=0.0),
        "max_waiting_density_per_m2": max(density_values, default=0.0),
        "density_limit_exceedance_fraction": _mean(
            [
                float(value > config.geometry.max_waiting_density_per_m2)
                for value in density_values
            ]
        ),
        "peak_simultaneous_movers": max(movers_values, default=0.0),
        "peak_moving_footprint_density_per_m2": max(
            moving_density_values,
            default=0.0,
        ),
        "maximum_release_size": max(release_sizes, default=0),
        "maximum_release_surge_index": max(release_surge_values, default=0.0),
        "waiting_area_m2": physical_waiting_area,
        "required_waiting_area_m2_at_density_limit": (
            required_waiting_area
            if config.control.policy != "S5"
            else 0.0
        ),
        "acceptable_waiting_capacity": acceptable_capacity,
        "capacity_efficiency_passengers_per_m2": (
            acceptable_capacity / physical_waiting_area
            if physical_waiting_area
            else 0.0
        ),
        "minimum_residual_waiting_area_m2": max(
            physical_waiting_area - peak_waiting_footprint,
            0.0,
        ),
        "total_modeled_area_m2": physical_waiting_area + config.geometry.screening_area_m2,
        "wait_gini": _gini(waits),
        "service_order_overtaking_events": out_of_arrival_order,
        "luggage_wait_gap_seconds": _mean(luggage_waits) - _mean(no_luggage_waits),
        "reduced_mobility_wait_gap_seconds": _mean(reduced_waits) - _mean(typical_waits),
        "group_wait_gap_seconds": _mean(group_waits) - _mean(solo_waits),
        "accessible_route_width_m": config.geometry.accessible_route_width_m,
        "turning_diameter_m": config.geometry.turning_diameter_m,
        "row_angle_degrees": config.geometry.row_angle_degrees,
        "barrier_footprint_m2": config.geometry.barrier_footprint_m2,
        "release_staff_count": config.geometry.release_staff_count,
    }
