from __future__ import annotations

import csv
import hashlib
import json
from concurrent.futures import ProcessPoolExecutor
from dataclasses import replace
from json import JSONDecodeError
from pathlib import Path

import yaml

from airport_batch_queue.config import SimulationConfig, load_config
from airport_batch_queue.simulator import run_simulation


def _mapping(value: object, name: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise TypeError(f"{name} must be a mapping")
    return {str(key): item for key, item in value.items()}


def _number(mapping: dict[str, object], key: str) -> float:
    value = mapping[key]
    if not isinstance(value, (int, float)):
        raise TypeError(f"{key} must be numeric")
    return float(value)


def _text(mapping: dict[str, object], key: str) -> str:
    value = mapping[key]
    if not isinstance(value, str):
        raise TypeError(f"{key} must be text")
    return value


def _write_json_atomic(path: Path, value: object) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _run(config: SimulationConfig) -> dict[str, float | int | str]:
    return dict(run_simulation(config).summary)


def _capacity_per_hour(config: SimulationConfig) -> float:
    expected_service = (
        config.service.mean_seconds
        + config.service.secondary_probability * config.service.secondary_mean_seconds
        + config.service.long_inspection_probability
        * config.service.long_inspection_mean_seconds
    )
    return config.service.servers * 3600.0 / expected_service


def _lane_schedule(regime: dict[str, object]) -> tuple[tuple[float, int], ...]:
    value = regime.get("lane_schedule", [])
    if not isinstance(value, list):
        raise TypeError("lane_schedule must be a list")
    rows: list[tuple[float, int]] = []
    for row in value:
        if (
            not isinstance(row, list)
            or len(row) != 2
            or not isinstance(row[0], (int, float))
            or not isinstance(row[1], int)
        ):
            raise TypeError("lane schedule rows must be [time, lanes]")
        rows.append((float(row[0]), row[1]))
    return tuple(rows)


def _scenario_config(
    base: SimulationConfig,
    geometry: dict[str, object],
    regime: dict[str, object],
    policy: str,
    seed: int,
    capacity: float,
) -> SimulationConfig:
    load = _number(regime, "load_regime")
    rate = capacity * load
    layout = {"S0": "B0", "S3": "B1", "S5": "B3"}[policy]
    config = replace(
        base,
        seed=seed,
        horizon_seconds=3600.0,
        drain_limit_seconds=3600.0,
        arrival=replace(
            base.arrival,
            mode=_text(regime, "arrival_mode"),
            rate_per_hour=rate,
            batch_interval_seconds=base.arrival.batch_size * 3600.0 / rate,
        ),
        service=replace(
            base.service,
            cv=_number(regime, "service_cv"),
            lane_schedule=_lane_schedule(regime),
        ),
        geometry=replace(
            base.geometry,
            layout=layout,
            width_m=_number(geometry, "width_m"),
            length_m=_number(geometry, "length_m"),
            waiting_area_m2=_number(geometry, "waiting_area_m2"),
            screening_area_m2=_number(geometry, "screening_area_m2"),
            downstream_staging_area_m2=_number(
                geometry,
                "downstream_staging_area_m2",
            ),
            barrier_footprint_m2=_number(geometry, "barrier_footprint_m2"),
            corridor_width_m=_number(geometry, "corridor_width_m"),
            rows=int(_number(geometry, "rows")),
            serpentine_distance_m=_number(geometry, "serpentine_distance_m"),
            stationary_distance_m=_number(geometry, "stationary_distance_m"),
            virtual_distance_m=_number(geometry, "virtual_distance_m"),
            downstream_capacity=int(_number(geometry, "downstream_capacity")),
        ),
        control=replace(base.control, policy=policy),
    )
    config.validate()
    return config


def main() -> None:
    specification_path = Path("configs/phase9_benchmark.yaml")
    specification = _mapping(
        yaml.safe_load(specification_path.read_text(encoding="utf-8")),
        "benchmark specification",
    )
    base = load_config(str(specification["base_config"]))
    geometries_value = specification["geometries"]
    regimes_value = specification["regimes"]
    policies_value = specification["policies"]
    if (
        not isinstance(geometries_value, list)
        or not isinstance(regimes_value, list)
        or not isinstance(policies_value, list)
    ):
        raise TypeError("geometries, regimes, and policies must be lists")
    geometries = [_mapping(value, "geometry") for value in geometries_value]
    regimes = [_mapping(value, "regime") for value in regimes_value]
    policies = [str(value) for value in policies_value]
    replications = int(specification["replications"])
    seed_base = int(specification["seed_base"])
    workers = int(specification["maximum_workers"])
    capacity = _capacity_per_hour(base)
    model_paths = [
        *sorted(Path("src/airport_batch_queue").glob("*.py")),
        specification_path,
        Path(__file__),
    ]
    root = Path.cwd().resolve()
    model_files = {}
    for path in model_paths:
        resolved = path.resolve()
        model_files[resolved.relative_to(root).as_posix()] = hashlib.sha256(
            resolved.read_bytes()
        ).hexdigest()
    model_hash = hashlib.sha256(
        "\n".join(f"{path} {value}" for path, value in model_files.items()).encode()
    ).hexdigest()
    output_root = Path("results/phase9")
    checkpoint_root = Path("results/checkpoints/phase9")
    output_root.mkdir(parents=True, exist_ok=True)
    checkpoint_root.mkdir(parents=True, exist_ok=True)
    manifest_path = checkpoint_root / "manifest.json"
    if manifest_path.exists():
        manifest = _mapping(
            json.loads(manifest_path.read_text(encoding="utf-8")),
            "manifest",
        )
        if manifest.get("model_sha256") != model_hash:
            raise SystemExit("Phase 9 checkpoint model hash mismatch")
    _write_json_atomic(
        manifest_path,
        {"model_sha256": model_hash, "model_files": model_files},
    )
    tasks: list[
        tuple[Path, SimulationConfig, dict[str, float | int | str]]
    ] = []
    rows: list[dict[str, float | int | str]] = []
    scenario_index = 0
    for geometry in geometries:
        for regime in regimes:
            geometry_id = _text(geometry, "geometry_id")
            regime_id = _text(regime, "regime_id")
            scenario_id = f"{geometry_id}_{regime_id}"
            for replication in range(replications):
                seed = seed_base + scenario_index * 1000 + replication
                for policy in policies:
                    metadata: dict[str, float | int | str] = {
                        "scenario_id": scenario_id,
                        "geometry_id": geometry_id,
                        "regime_id": regime_id,
                        "load_regime": _number(regime, "load_regime"),
                        "replication": replication,
                        "seed": seed,
                        "policy": policy,
                    }
                    checkpoint = (
                        checkpoint_root
                        / scenario_id
                        / policy
                        / f"rep_{replication:03d}.json"
                    )
                    if checkpoint.exists():
                        try:
                            saved = _mapping(
                                json.loads(checkpoint.read_text(encoding="utf-8")),
                                "checkpoint",
                            )
                            rows.append({**metadata, **saved})
                            continue
                        except JSONDecodeError:
                            pass
                    config = _scenario_config(
                        base,
                        geometry,
                        regime,
                        policy,
                        seed,
                        capacity,
                    )
                    tasks.append((checkpoint, config, metadata))
            scenario_index += 1
    with ProcessPoolExecutor(max_workers=workers) as executor:
        summaries = executor.map(_run, [config for _, config, _ in tasks])
        for (checkpoint, _, metadata), summary in zip(tasks, summaries, strict=True):
            checkpoint.parent.mkdir(parents=True, exist_ok=True)
            _write_json_atomic(checkpoint, summary)
            rows.append({**metadata, **summary})
    rows.sort(
        key=lambda row: (
            str(row["scenario_id"]),
            int(row["replication"]),
            str(row["policy"]),
        )
    )
    with (output_root / "replications.csv").open(
        "w",
        newline="",
        encoding="utf-8",
    ) as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(rows[0]),
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)
    _write_json_atomic(
        output_root / "run_manifest.json",
        {
            "status": "complete",
            "model_sha256": model_hash,
            "scenario_count": len(geometries) * len(regimes),
            "policy_count": len(policies),
            "replications": replications,
            "replication_rows": len(rows),
        },
    )


if __name__ == "__main__":
    main()
