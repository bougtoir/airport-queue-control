from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass(frozen=True)
class ArrivalConfig:
    mode: str = "poisson"
    rate_per_hour: float = 420.0
    profile: tuple[tuple[float, float], ...] = ()
    burst_size: int = 35
    burst_interval_seconds: float = 900.0
    batch_size: int = 8
    batch_interval_seconds: float = 70.0


@dataclass(frozen=True)
class ServiceConfig:
    servers: int = 3
    mean_seconds: float = 20.0
    cv: float = 0.55
    distribution: str = "gamma"
    secondary_probability: float = 0.04
    secondary_mean_seconds: float = 50.0
    long_inspection_probability: float = 0.005
    long_inspection_mean_seconds: float = 180.0
    lane_schedule: tuple[tuple[float, int], ...] = ()


@dataclass(frozen=True)
class PassengerConfig:
    walking_speed_mps: float = 1.3
    walking_speed_cv: float = 0.16
    luggage_prevalence: float = 0.65
    luggage_speed_multiplier: float = 0.90
    reduced_mobility_prevalence: float = 0.04
    reduced_mobility_speed_multiplier: float = 0.65
    release_compliance: float = 0.97
    noncompliance_delay_seconds: float = 12.0
    startup_delay_seconds: float = 0.39
    reaction_delay_seconds: float = 0.48
    slowdown_seconds: float = 0.58
    body_footprint_m2: float = 0.20
    luggage_footprint_m2_per_bag: float = 0.12
    static_clearance_m2: float = 0.35
    moving_clearance_m2: float = 0.55
    multiple_bag_probability: float = 0.15
    group_prevalence: float = 0.20


@dataclass(frozen=True)
class GeometryConfig:
    waiting_area_m2: float = 90.0
    screening_area_m2: float = 45.0
    serpentine_distance_m: float = 55.0
    stationary_distance_m: float = 22.0
    virtual_distance_m: float = 18.0
    serpentine_turns: int = 10
    stationary_turns: int = 2
    virtual_turns: int = 1
    spacing_m: float = 0.75
    accessible_route_width_m: float = 1.20
    turning_diameter_m: float = 1.60
    max_waiting_density_per_m2: float = 1.40
    downstream_capacity: int = 36
    layout: str = "policy_default"
    width_m: float = 12.0
    length_m: float = 10.0
    rows: int = 6
    row_spacing_m: float = 1.20
    passenger_spacing_m: float = 0.75
    gate_width_m: float = 1.20
    downstream_staging_area_m2: float = 45.0
    corridor_width_m: float = 1.20
    screening_positions: int = 3
    barrier_footprint_m2: float = 8.0
    row_angle_degrees: float = 0.0
    release_staff_count: int = 1


@dataclass(frozen=True)
class ControlConfig:
    policy: str = "S0"
    batch_size: int = 12
    sub_batch_size: int = 4
    downstream_threshold: int = 6
    decision_interval_seconds: float = 5.0
    maximum_hold_seconds: float = 120.0
    prediction_horizon_seconds: float = 90.0
    prediction_error_sd: float = 0.12
    gate_delay_seconds: float = 0.75


@dataclass(frozen=True)
class SimulationConfig:
    seed: int = 20260924
    horizon_seconds: float = 7200.0
    drain_limit_seconds: float = 7200.0
    time_step_seconds: float = 1.0
    arrival: ArrivalConfig = field(default_factory=ArrivalConfig)
    service: ServiceConfig = field(default_factory=ServiceConfig)
    passenger: PassengerConfig = field(default_factory=PassengerConfig)
    geometry: GeometryConfig = field(default_factory=GeometryConfig)
    control: ControlConfig = field(default_factory=ControlConfig)

    def validate(self) -> None:
        if self.control.policy not in {"S0", "S1", "S2", "S3", "S4", "S5"}:
            raise ValueError(f"Unsupported policy: {self.control.policy}")
        if self.arrival.mode not in {
            "poisson",
            "nonhomogeneous",
            "burst",
            "flight_bank",
            "batched",
        }:
            raise ValueError(f"Unsupported arrival mode: {self.arrival.mode}")
        if self.service.distribution not in {"gamma", "lognormal", "mixture"}:
            raise ValueError(f"Unsupported service distribution: {self.service.distribution}")
        if self.service.servers < 1 or self.service.mean_seconds <= 0:
            raise ValueError("Service capacity must be positive")
        if self.horizon_seconds <= 0 or self.time_step_seconds <= 0:
            raise ValueError("Simulation duration and time step must be positive")
        if self.geometry.accessible_route_width_m < 0.915:
            raise ValueError("Accessible route width is below the retained 0.915 m minimum")
        if self.geometry.turning_diameter_m < 1.525:
            raise ValueError("Turning diameter is below the retained 1.525 m minimum")
        if self.geometry.downstream_capacity < self.service.servers:
            raise ValueError("Downstream capacity must accommodate at least one passenger per server")
        if self.geometry.layout not in {
            "policy_default",
            "B0",
            "B1",
            "B2",
            "B3",
            "B4",
        }:
            raise ValueError(f"Unsupported guidance layout: {self.geometry.layout}")
        if not 0 <= self.geometry.row_angle_degrees <= 45:
            raise ValueError("Row angle must be between 0 and 45 degrees")
        if self.geometry.rows < 1 or self.geometry.gate_width_m <= 0:
            raise ValueError("Rows and gate width must be positive")
        if self.geometry.release_staff_count < 0:
            raise ValueError("Release staff count cannot be negative")
        gross_area = self.geometry.width_m * self.geometry.length_m
        fixed_area = (
            self.geometry.barrier_footprint_m2
            + self.geometry.corridor_width_m * self.geometry.length_m
        )
        if fixed_area >= gross_area:
            raise ValueError("Barriers and corridor consume the full geometry")
        usable_area = gross_area - fixed_area
        if self.geometry.waiting_area_m2 > usable_area:
            raise ValueError("Waiting area exceeds the usable geometry")
        prior_time = -1.0
        for change_time, active_lanes in self.service.lane_schedule:
            if change_time < prior_time or change_time < 0:
                raise ValueError("Lane schedule times must be nonnegative and sorted")
            if not 0 <= active_lanes <= self.service.servers:
                raise ValueError("Lane schedule active lanes exceed configured servers")
            prior_time = change_time
        if not 0 <= self.passenger.release_compliance <= 1:
            raise ValueError("Release compliance must be between zero and one")


def _mapping(value: object, name: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise TypeError(f"{name} must be a mapping")
    return {str(key): item for key, item in value.items()}


def _float(mapping: dict[str, object], key: str, default: float) -> float:
    value = mapping.get(key, default)
    if not isinstance(value, (int, float)):
        raise TypeError(f"{key} must be numeric")
    return float(value)


def _int(mapping: dict[str, object], key: str, default: int) -> int:
    value = mapping.get(key, default)
    if not isinstance(value, int):
        raise TypeError(f"{key} must be an integer")
    return value


def _str(mapping: dict[str, object], key: str, default: str) -> str:
    value = mapping.get(key, default)
    if not isinstance(value, str):
        raise TypeError(f"{key} must be text")
    return value


def load_config(path: str | Path) -> SimulationConfig:
    with Path(path).open(encoding="utf-8") as handle:
        loaded: object = yaml.safe_load(handle)
    root = _mapping(loaded, "configuration")
    arrival = _mapping(root.get("arrival", {}), "arrival")
    service = _mapping(root.get("service", {}), "service")
    passenger = _mapping(root.get("passenger", {}), "passenger")
    geometry = _mapping(root.get("geometry", {}), "geometry")
    control = _mapping(root.get("control", {}), "control")

    profile_value = arrival.get("profile", [])
    if not isinstance(profile_value, list):
        raise TypeError("arrival.profile must be a list")
    profile: list[tuple[float, float]] = []
    for item in profile_value:
        if not isinstance(item, list) or len(item) != 2:
            raise ValueError("arrival.profile rows must be [time_seconds, rate_per_hour]")
        time_value, rate_value = item
        if not isinstance(time_value, (int, float)) or not isinstance(rate_value, (int, float)):
            raise TypeError("arrival.profile values must be numeric")
        profile.append((float(time_value), float(rate_value)))
    lane_schedule_value = service.get("lane_schedule", [])
    if not isinstance(lane_schedule_value, list):
        raise TypeError("service.lane_schedule must be a list")
    lane_schedule: list[tuple[float, int]] = []
    for item in lane_schedule_value:
        if (
            not isinstance(item, list)
            or len(item) != 2
            or not isinstance(item[0], (int, float))
            or not isinstance(item[1], int)
        ):
            raise TypeError("service.lane_schedule rows must be [time_seconds, active_lanes]")
        lane_schedule.append((float(item[0]), item[1]))

    config = SimulationConfig(
        seed=_int(root, "seed", 20260924),
        horizon_seconds=_float(root, "horizon_seconds", 7200.0),
        drain_limit_seconds=_float(root, "drain_limit_seconds", 7200.0),
        time_step_seconds=_float(root, "time_step_seconds", 1.0),
        arrival=ArrivalConfig(
            mode=_str(arrival, "mode", "poisson"),
            rate_per_hour=_float(arrival, "rate_per_hour", 420.0),
            profile=tuple(profile),
            burst_size=_int(arrival, "burst_size", 35),
            burst_interval_seconds=_float(arrival, "burst_interval_seconds", 900.0),
            batch_size=_int(arrival, "batch_size", 8),
            batch_interval_seconds=_float(arrival, "batch_interval_seconds", 70.0),
        ),
        service=ServiceConfig(
            servers=_int(service, "servers", 3),
            mean_seconds=_float(service, "mean_seconds", 20.0),
            cv=_float(service, "cv", 0.55),
            distribution=_str(service, "distribution", "gamma"),
            secondary_probability=_float(service, "secondary_probability", 0.04),
            secondary_mean_seconds=_float(service, "secondary_mean_seconds", 50.0),
            long_inspection_probability=_float(service, "long_inspection_probability", 0.005),
            long_inspection_mean_seconds=_float(
                service, "long_inspection_mean_seconds", 180.0
            ),
            lane_schedule=tuple(lane_schedule),
        ),
        passenger=PassengerConfig(
            walking_speed_mps=_float(passenger, "walking_speed_mps", 1.3),
            walking_speed_cv=_float(passenger, "walking_speed_cv", 0.16),
            luggage_prevalence=_float(passenger, "luggage_prevalence", 0.65),
            luggage_speed_multiplier=_float(passenger, "luggage_speed_multiplier", 0.90),
            reduced_mobility_prevalence=_float(
                passenger, "reduced_mobility_prevalence", 0.04
            ),
            reduced_mobility_speed_multiplier=_float(
                passenger, "reduced_mobility_speed_multiplier", 0.65
            ),
            release_compliance=_float(passenger, "release_compliance", 0.97),
            noncompliance_delay_seconds=_float(
                passenger, "noncompliance_delay_seconds", 12.0
            ),
            startup_delay_seconds=_float(passenger, "startup_delay_seconds", 0.39),
            reaction_delay_seconds=_float(passenger, "reaction_delay_seconds", 0.48),
            slowdown_seconds=_float(passenger, "slowdown_seconds", 0.58),
            body_footprint_m2=_float(passenger, "body_footprint_m2", 0.20),
            luggage_footprint_m2_per_bag=_float(
                passenger, "luggage_footprint_m2_per_bag", 0.12
            ),
            static_clearance_m2=_float(passenger, "static_clearance_m2", 0.35),
            moving_clearance_m2=_float(passenger, "moving_clearance_m2", 0.55),
            multiple_bag_probability=_float(
                passenger, "multiple_bag_probability", 0.15
            ),
            group_prevalence=_float(passenger, "group_prevalence", 0.20),
        ),
        geometry=GeometryConfig(
            waiting_area_m2=_float(geometry, "waiting_area_m2", 90.0),
            screening_area_m2=_float(geometry, "screening_area_m2", 45.0),
            serpentine_distance_m=_float(geometry, "serpentine_distance_m", 55.0),
            stationary_distance_m=_float(geometry, "stationary_distance_m", 22.0),
            virtual_distance_m=_float(geometry, "virtual_distance_m", 18.0),
            serpentine_turns=_int(geometry, "serpentine_turns", 10),
            stationary_turns=_int(geometry, "stationary_turns", 2),
            virtual_turns=_int(geometry, "virtual_turns", 1),
            spacing_m=_float(geometry, "spacing_m", 0.75),
            accessible_route_width_m=_float(geometry, "accessible_route_width_m", 1.20),
            turning_diameter_m=_float(geometry, "turning_diameter_m", 1.60),
            max_waiting_density_per_m2=_float(
                geometry, "max_waiting_density_per_m2", 1.40
            ),
            downstream_capacity=_int(geometry, "downstream_capacity", 36),
            layout=_str(geometry, "layout", "policy_default"),
            width_m=_float(geometry, "width_m", 12.0),
            length_m=_float(geometry, "length_m", 10.0),
            rows=_int(geometry, "rows", 6),
            row_spacing_m=_float(geometry, "row_spacing_m", 1.20),
            passenger_spacing_m=_float(geometry, "passenger_spacing_m", 0.75),
            gate_width_m=_float(geometry, "gate_width_m", 1.20),
            downstream_staging_area_m2=_float(
                geometry, "downstream_staging_area_m2", 45.0
            ),
            corridor_width_m=_float(geometry, "corridor_width_m", 1.20),
            screening_positions=_int(geometry, "screening_positions", 3),
            barrier_footprint_m2=_float(geometry, "barrier_footprint_m2", 8.0),
            row_angle_degrees=_float(geometry, "row_angle_degrees", 0.0),
            release_staff_count=_int(geometry, "release_staff_count", 1),
        ),
        control=ControlConfig(
            policy=_str(control, "policy", "S0"),
            batch_size=_int(control, "batch_size", 12),
            sub_batch_size=_int(control, "sub_batch_size", 4),
            downstream_threshold=_int(control, "downstream_threshold", 6),
            decision_interval_seconds=_float(
                control, "decision_interval_seconds", 5.0
            ),
            maximum_hold_seconds=_float(control, "maximum_hold_seconds", 120.0),
            prediction_horizon_seconds=_float(
                control, "prediction_horizon_seconds", 90.0
            ),
            prediction_error_sd=_float(control, "prediction_error_sd", 0.12),
            gate_delay_seconds=_float(control, "gate_delay_seconds", 0.75),
        ),
    )
    config.validate()
    return config
