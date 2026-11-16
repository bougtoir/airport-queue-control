from __future__ import annotations

from collections import deque
from dataclasses import asdict, dataclass

import numpy as np

from airport_batch_queue.arrivals import generate_arrivals
from airport_batch_queue.config import SimulationConfig
from airport_batch_queue.control import release_count
from airport_batch_queue.entities import Passenger, Server
from airport_batch_queue.geometry import (
    cumulative_turning_degrees,
    passenger_footprints_m2,
    route_parameters,
    usable_waiting_area_m2,
)
from airport_batch_queue.metrics import MetricValue, summarize
from airport_batch_queue.service import sample_service_seconds


@dataclass
class SimulationResult:
    config: SimulationConfig
    passengers: list[Passenger]
    trajectories: list[dict[str, float]]
    summary: dict[str, MetricValue]

    def passenger_rows(self) -> list[dict[str, float | int | bool | None]]:
        return [asdict(passenger) for passenger in self.passengers]


def _create_passengers(config: SimulationConfig, rng: np.random.Generator) -> list[Passenger]:
    arrivals = generate_arrivals(config.arrival, config.horizon_seconds, rng)
    group_ids: list[int | None] = [None] * len(arrivals)
    passenger_index = 0
    next_group_id = 0
    while passenger_index < len(arrivals):
        remaining = len(arrivals) - passenger_index
        if remaining >= 2 and rng.random() < config.passenger.group_prevalence:
            group_size = int(rng.integers(2, min(4, remaining) + 1))
            for member_index in range(passenger_index, passenger_index + group_size):
                group_ids[member_index] = next_group_id
            next_group_id += 1
            passenger_index += group_size
        else:
            passenger_index += 1
    passengers: list[Passenger] = []
    for passenger_id, arrival_time in enumerate(arrivals):
        has_luggage = bool(rng.random() < config.passenger.luggage_prevalence)
        bag_count = (
            1 + int(rng.random() < config.passenger.multiple_bag_probability)
            if has_luggage
            else 0
        )
        reduced_mobility = bool(
            rng.random() < config.passenger.reduced_mobility_prevalence
        )
        static_footprint, moving_footprint = passenger_footprints_m2(
            config,
            bag_count,
        )
        speed = float(
            rng.lognormal(
                np.log(config.passenger.walking_speed_mps)
                - np.log(config.passenger.walking_speed_cv**2 + 1.0) / 2.0,
                np.sqrt(np.log(config.passenger.walking_speed_cv**2 + 1.0)),
            )
        )
        if has_luggage:
            speed *= config.passenger.luggage_speed_multiplier
        if reduced_mobility:
            speed *= config.passenger.reduced_mobility_speed_multiplier
        passengers.append(
            Passenger(
                passenger_id=passenger_id,
                arrival_time=float(arrival_time),
                walking_speed_mps=max(speed, 0.25),
                has_luggage=has_luggage,
                bag_count=bag_count,
                reduced_mobility=reduced_mobility,
                mobility_class="reduced" if reduced_mobility else "typical",
                group_id=group_ids[passenger_id],
                compliant=bool(rng.random() < config.passenger.release_compliance),
                service_seconds=sample_service_seconds(config.service, rng),
                static_footprint_m2=static_footprint,
                moving_footprint_m2=moving_footprint,
            )
        )
    return passengers


def _active_server_count(config: SimulationConfig, current_time: float) -> int:
    active = config.service.servers
    for change_time, active_lanes in config.service.lane_schedule:
        if change_time > current_time:
            break
        active = active_lanes
    return active


def _release(
    config: SimulationConfig,
    passengers: list[Passenger],
    waiting: deque[int],
    transit: list[tuple[float, int]],
    count: int,
    current_time: float,
) -> float:
    distance, turns, gate_delay = route_parameters(config)
    selected = [waiting.popleft() for _ in range(count)]
    release_footprint = sum(
        passengers[passenger_id].moving_footprint_m2 for passenger_id in selected
    )
    gate_area = (
        config.geometry.gate_width_m * config.geometry.accessible_route_width_m
    )
    conflict_proxy = release_footprint / gate_area
    if config.control.policy == "S0":
        for passenger_id in waiting:
            passengers[passenger_id].stop_go_events += 1

    for passenger_id in selected:
        passenger = passengers[passenger_id]
        passenger.release_time = current_time
        if config.control.policy == "S0":
            passenger.movement_starts = 1 + passenger.stop_go_events
            passenger.movement_stops = passenger.stop_go_events
        else:
            passenger.movement_starts = 1
            passenger.movement_stops = 0
        passenger.movement_distance_m = distance
        passenger.cumulative_turning_angle_degrees = cumulative_turning_degrees(
            config,
            turns,
        )
        passenger.luggage_rotation_degrees = (
            passenger.bag_count * passenger.cumulative_turning_angle_degrees
        )
        passenger.movement_conflict_proxy = conflict_proxy
        passenger.intervention_required = not passenger.compliant
        passenger.movement_time_seconds = (
            distance / passenger.walking_speed_mps
            + gate_delay
            + passenger.movement_starts
            * (
                config.passenger.startup_delay_seconds
                + config.passenger.reaction_delay_seconds
            )
            + passenger.movement_stops * config.passenger.slowdown_seconds
        )
        compliance_delay = (
            0.0 if passenger.compliant else config.passenger.noncompliance_delay_seconds
        )
        queue_arrival = current_time + passenger.movement_time_seconds + compliance_delay
        passenger.screening_queue_arrival = queue_arrival
        transit.append((queue_arrival, passenger_id))
    return conflict_proxy


def run_simulation(config: SimulationConfig) -> SimulationResult:
    config.validate()
    rng = np.random.default_rng(config.seed)
    passengers = _create_passengers(config, rng)
    servers = [Server(server_id=index) for index in range(config.service.servers)]
    waiting: deque[int] = deque()
    screening_queue: deque[int] = deque()
    transit: list[tuple[float, int]] = []
    trajectories: list[dict[str, float]] = []
    release_sizes: list[int] = []
    arrival_index = 0
    next_decision = 0.0
    current_time = 0.0
    end_limit = config.horizon_seconds + config.drain_limit_seconds
    completed_count = 0
    step = config.time_step_seconds

    while current_time <= end_limit:
        current_release_size = 0
        current_release_surge = 0.0
        while (
            arrival_index < len(passengers)
            and passengers[arrival_index].arrival_time <= current_time
        ):
            waiting.append(arrival_index)
            arrival_index += 1

        for server in servers:
            if server.passenger_id is not None and server.busy_until <= current_time:
                passenger = passengers[server.passenger_id]
                passenger.completion_time = server.busy_until
                completed_count += 1
                server.passenger_id = None

        arrived_transit = [
            (queue_arrival, passenger_id)
            for queue_arrival, passenger_id in transit
            if queue_arrival <= current_time
        ]
        transit = [
            (queue_arrival, passenger_id)
            for queue_arrival, passenger_id in transit
            if queue_arrival > current_time
        ]
        for _, passenger_id in sorted(arrived_transit):
            screening_queue.append(passenger_id)

        assignable_servers = servers[: _active_server_count(config, current_time)]
        for server in assignable_servers:
            if server.passenger_id is None and screening_queue:
                passenger_id = screening_queue.popleft()
                passenger = passengers[passenger_id]
                passenger.service_start = current_time
                passenger.server_id = server.server_id
                server.passenger_id = passenger_id
                server.busy_until = current_time + passenger.service_seconds
                server.busy_seconds += passenger.service_seconds

        if current_time >= next_decision and waiting:
            idle_servers = sum(
                server.passenger_id is None for server in assignable_servers
            )
            expected_completions = sum(
                server.passenger_id is not None
                and server.busy_until
                <= current_time + config.control.prediction_horizon_seconds
                for server in servers
            )
            downstream_count = len(screening_queue) + len(transit)
            oldest_wait = current_time - passengers[waiting[0]].arrival_time
            count = release_count(
                config,
                len(waiting),
                oldest_wait,
                downstream_count,
                idle_servers,
                expected_completions,
                rng,
            )
            if count:
                current_release_surge = _release(
                    config,
                    passengers,
                    waiting,
                    transit,
                    count,
                    current_time,
                )
                current_release_size = count
                release_sizes.append(count)
            next_decision = current_time + config.control.decision_interval_seconds

        for server in assignable_servers:
            if server.passenger_id is None and waiting:
                server.starvation_seconds += step

        waiting_area = usable_waiting_area_m2(config)
        waiting_density = (
            0.0
            if config.control.policy == "S5"
            else len(waiting) / waiting_area
        )
        waiting_footprint = sum(
            passengers[passenger_id].static_footprint_m2 for passenger_id in waiting
        )
        moving_footprint = sum(
            passengers[passenger_id].moving_footprint_m2
            for _, passenger_id in transit
        )
        active_count = _active_server_count(config, current_time)
        available_server_count = max(
            active_count,
            sum(server.passenger_id is not None for server in servers),
        )
        trajectories.append(
            {
                "time_seconds": current_time,
                "upstream_waiting": float(len(waiting)),
                "in_transit": float(len(transit)),
                "downstream_queue": float(len(screening_queue)),
                "busy_servers": float(
                    sum(server.passenger_id is not None for server in servers)
                ),
                "active_servers": float(available_server_count),
                "waiting_density_per_m2": waiting_density,
                "upstream_static_footprint_m2": waiting_footprint,
                "moving_footprint_density_per_m2": (
                    moving_footprint / config.geometry.downstream_staging_area_m2
                ),
                "release_size": float(current_release_size),
                "release_surge_index": current_release_surge,
                "completed": float(completed_count),
            }
        )

        no_more_arrivals = arrival_index == len(passengers)
        system_empty = not waiting and not transit and not screening_queue
        servers_idle = all(server.passenger_id is None for server in servers)
        if (
            current_time >= config.horizon_seconds
            and no_more_arrivals
            and system_empty
            and servers_idle
        ):
            break
        current_time += step

    summary = summarize(
        config,
        passengers,
        servers,
        trajectories,
        current_time,
        release_sizes,
    )
    return SimulationResult(
        config=config,
        passengers=passengers,
        trajectories=trajectories,
        summary=summary,
    )
