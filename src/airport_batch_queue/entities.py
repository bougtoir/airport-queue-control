from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Passenger:
    passenger_id: int
    arrival_time: float
    walking_speed_mps: float
    has_luggage: bool
    bag_count: int
    reduced_mobility: bool
    mobility_class: str
    group_id: int | None
    compliant: bool
    service_seconds: float
    static_footprint_m2: float
    moving_footprint_m2: float
    release_time: float | None = None
    screening_queue_arrival: float | None = None
    service_start: float | None = None
    completion_time: float | None = None
    server_id: int | None = None
    movement_distance_m: float = 0.0
    movement_starts: int = 0
    movement_stops: int = 0
    cumulative_turning_angle_degrees: float = 0.0
    movement_time_seconds: float = 0.0
    luggage_rotation_degrees: float = 0.0
    movement_conflict_proxy: float = 0.0
    intervention_required: bool = False
    stop_go_events: int = 0


@dataclass
class Server:
    server_id: int
    passenger_id: int | None = None
    busy_until: float = 0.0
    busy_seconds: float = 0.0
    starvation_seconds: float = 0.0
