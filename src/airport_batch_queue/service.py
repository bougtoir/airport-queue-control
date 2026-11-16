from __future__ import annotations

import math

import numpy as np

from airport_batch_queue.config import ServiceConfig


def _gamma(mean: float, cv: float, rng: np.random.Generator) -> float:
    shape = 1.0 / max(cv, 1e-6) ** 2
    scale = mean / shape
    return float(rng.gamma(shape, scale))


def _lognormal(mean: float, cv: float, rng: np.random.Generator) -> float:
    sigma_squared = math.log(cv**2 + 1.0)
    sigma = math.sqrt(sigma_squared)
    mu = math.log(mean) - sigma_squared / 2.0
    return float(rng.lognormal(mu, sigma))


def sample_service_seconds(config: ServiceConfig, rng: np.random.Generator) -> float:
    if config.distribution == "gamma":
        duration = _gamma(config.mean_seconds, config.cv, rng)
    elif config.distribution == "lognormal":
        duration = _lognormal(config.mean_seconds, config.cv, rng)
    elif config.distribution == "mixture":
        if rng.random() < 0.75:
            duration = _gamma(config.mean_seconds * 0.8, config.cv * 0.8, rng)
        else:
            duration = _lognormal(config.mean_seconds * 1.6, config.cv * 1.2, rng)
    else:
        raise ValueError(f"Unsupported service distribution: {config.distribution}")

    if rng.random() < config.secondary_probability:
        duration += float(rng.gamma(2.0, config.secondary_mean_seconds / 2.0))
    if rng.random() < config.long_inspection_probability:
        duration += float(rng.exponential(config.long_inspection_mean_seconds))
    return max(duration, 1.0)
