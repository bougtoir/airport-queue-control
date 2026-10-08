from __future__ import annotations

import numpy as np

from airport_batch_queue.config import SimulationConfig


def release_count(
    config: SimulationConfig,
    waiting_count: int,
    oldest_wait_seconds: float,
    downstream_count: int,
    idle_servers: int,
    expected_completions: int,
    rng: np.random.Generator,
) -> int:
    if waiting_count == 0:
        return 0

    control = config.control
    capacity = max(config.geometry.downstream_capacity - downstream_count, 0)
    if capacity == 0:
        return 0
    forced = oldest_wait_seconds >= control.maximum_hold_seconds

    if control.policy == "S0":
        target = max(config.service.servers * 4, 1)
        return min(waiting_count, capacity, max(target - downstream_count, 0))
    if control.policy == "S1":
        if waiting_count < control.batch_size and not forced:
            return 0
        return min(waiting_count, control.batch_size, capacity)
    if control.policy == "S2":
        if waiting_count < control.sub_batch_size and not forced:
            return 0
        return min(waiting_count, control.sub_batch_size, capacity)
    if control.policy == "S3":
        if downstream_count > control.downstream_threshold and not forced:
            return 0
        requested = min(control.batch_size, waiting_count)
        return min(requested, capacity)
    if control.policy == "S4":
        error = float(rng.normal(0.0, control.prediction_error_sd))
        predicted_capacity = max(
            round((idle_servers + expected_completions) * (1.0 + error)) - downstream_count,
            0,
        )
        if predicted_capacity == 0 and not forced:
            return 0
        requested = min(control.batch_size, max(predicted_capacity, 1 if forced else 0))
        return min(waiting_count, requested, capacity)
    if control.policy == "S5":
        requested = max(idle_servers - downstream_count, 0)
        if requested == 0 and forced:
            requested = 1
        return min(waiting_count, requested, capacity)
    raise ValueError(f"Unsupported policy: {control.policy}")
