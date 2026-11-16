from __future__ import annotations

from math import cos, radians, sin

from airport_batch_queue.config import SimulationConfig


def resolved_layout(config: SimulationConfig) -> str:
    if config.geometry.layout != "policy_default":
        return config.geometry.layout
    if config.control.policy == "S0":
        return "B0"
    if config.control.policy == "S5":
        return "B3"
    return "B1"


def usable_waiting_area_m2(config: SimulationConfig) -> float:
    gross_area = config.geometry.width_m * config.geometry.length_m
    fixed_area = (
        config.geometry.barrier_footprint_m2
        + config.geometry.corridor_width_m * config.geometry.length_m
    )
    return min(config.geometry.waiting_area_m2, gross_area - fixed_area)


def route_parameters(config: SimulationConfig) -> tuple[float, int, float]:
    layout = resolved_layout(config)
    if config.control.policy == "S5":
        return (
            config.geometry.virtual_distance_m,
            config.geometry.virtual_turns,
            0.0,
        )
    if layout == "B0":
        return (
            config.geometry.serpentine_distance_m,
            config.geometry.serpentine_turns,
            0.0,
        )
    angle = radians(config.geometry.row_angle_degrees)
    distance = config.geometry.stationary_distance_m / max(cos(angle), 0.50)
    return distance, config.geometry.stationary_turns, config.control.gate_delay_seconds


def cumulative_turning_degrees(config: SimulationConfig, turns: int) -> float:
    if resolved_layout(config) == "B0" or config.control.policy == "S5":
        return turns * 180.0
    return turns * 180.0 + 2.0 * config.geometry.row_angle_degrees


def passenger_footprints_m2(
    config: SimulationConfig,
    bag_count: int,
) -> tuple[float, float]:
    luggage = bag_count * config.passenger.luggage_footprint_m2_per_bag
    angle = radians(config.geometry.row_angle_degrees)
    turning_envelope = luggage * abs(sin(angle))
    static = (
        config.passenger.body_footprint_m2
        + luggage
        + config.passenger.static_clearance_m2
    )
    moving = (
        config.passenger.body_footprint_m2
        + luggage
        + config.passenger.moving_clearance_m2
        + turning_envelope
    )
    return static, moving
