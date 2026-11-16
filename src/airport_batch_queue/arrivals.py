from __future__ import annotations

import math

import numpy as np

from airport_batch_queue.config import ArrivalConfig


def _profile_rate(config: ArrivalConfig, time_seconds: float) -> float:
    if not config.profile:
        return config.rate_per_hour
    rate = config.profile[0][1]
    for start, candidate in config.profile:
        if time_seconds < start:
            break
        rate = candidate
    return rate


def _sample_rate_process(
    config: ArrivalConfig,
    horizon_seconds: float,
    step_seconds: float,
    rng: np.random.Generator,
) -> list[float]:
    arrivals: list[float] = []
    steps = math.ceil(horizon_seconds / step_seconds)
    for step in range(steps):
        start = step * step_seconds
        if start >= horizon_seconds:
            break
        width = min(step_seconds, horizon_seconds - start)
        rate = _profile_rate(config, start)
        count = int(rng.poisson(max(rate, 0.0) * width / 3600.0))
        if count:
            arrivals.extend(start + rng.uniform(0.0, width, size=count))
    return arrivals


def generate_arrivals(
    config: ArrivalConfig,
    horizon_seconds: float,
    rng: np.random.Generator,
) -> np.ndarray:
    if config.mode in {"poisson", "nonhomogeneous"}:
        arrivals = _sample_rate_process(config, horizon_seconds, 1.0, rng)
    elif config.mode == "burst":
        arrivals = _sample_rate_process(config, horizon_seconds, 1.0, rng)
        burst_time = config.burst_interval_seconds
        while burst_time < horizon_seconds:
            arrivals.extend(
                burst_time + rng.uniform(0.0, min(20.0, horizon_seconds - burst_time), config.burst_size)
            )
            burst_time += config.burst_interval_seconds
    elif config.mode == "flight_bank":
        arrivals = []
        bank_width = min(600.0, config.burst_interval_seconds)
        bank_time = 0.0
        while bank_time < horizon_seconds:
            bank_end = min(bank_time + bank_width, horizon_seconds)
            bank_rate = config.rate_per_hour * 1.8
            quiet_end = min(bank_time + config.burst_interval_seconds, horizon_seconds)
            bank = _sample_rate_process(
                ArrivalConfig(rate_per_hour=bank_rate),
                bank_end - bank_time,
                1.0,
                rng,
            )
            arrivals.extend(value + bank_time for value in bank)
            quiet_start = bank_end
            if quiet_end > quiet_start:
                quiet = _sample_rate_process(
                    ArrivalConfig(rate_per_hour=config.rate_per_hour * 0.35),
                    quiet_end - quiet_start,
                    1.0,
                    rng,
                )
                arrivals.extend(value + quiet_start for value in quiet)
            bank_time += config.burst_interval_seconds
    elif config.mode == "batched":
        arrivals = []
        time_seconds = 0.0
        while time_seconds < horizon_seconds:
            arrivals.extend(
                time_seconds
                + rng.uniform(0.0, min(5.0, horizon_seconds - time_seconds), config.batch_size)
            )
            time_seconds += config.batch_interval_seconds
    else:
        raise ValueError(f"Unsupported arrival mode: {config.mode}")
    return np.sort(np.asarray(arrivals, dtype=float))
