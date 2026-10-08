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


def _integer(value: object, name: str) -> int:
    if not isinstance(value, int):
        raise TypeError(f"{name} must be an integer")
    return value


def _number(mapping: dict[str, object], key: str, default: float) -> float:
    value = mapping.get(key, default)
    if not isinstance(value, (int, float)):
        raise TypeError(f"{key} must be numeric")
    return float(value)


def _text(mapping: dict[str, object], key: str, default: str) -> str:
    value = mapping.get(key, default)
    if not isinstance(value, str):
        raise TypeError(f"{key} must be text")
    return value


def _boolean(mapping: dict[str, object], key: str) -> bool:
    value = mapping.get(key, False)
    if not isinstance(value, bool):
        raise TypeError(f"{key} must be boolean")
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


def _model_hash(specification_path: Path) -> tuple[str, dict[str, str]]:
    root = Path.cwd().resolve()
    paths = [
        *sorted(Path("src/airport_batch_queue").glob("*.py")),
        specification_path,
        Path(__file__),
    ]
    hashes: dict[str, str] = {}
    for path in paths:
        resolved = path.resolve()
        hashes[resolved.relative_to(root).as_posix()] = hashlib.sha256(
            resolved.read_bytes()
        ).hexdigest()
    bundle = hashlib.sha256(
        "\n".join(f"{path} {value}" for path, value in hashes.items()).encode()
    ).hexdigest()
    return bundle, hashes


def _lane_schedule(scenario: dict[str, object]) -> tuple[tuple[float, int], ...]:
    value = scenario.get("lane_schedule", [])
    if not isinstance(value, list):
        raise TypeError("lane_schedule must be a list")
    schedule: list[tuple[float, int]] = []
    for row in value:
        if (
            not isinstance(row, list)
            or len(row) != 2
            or not isinstance(row[0], (int, float))
            or not isinstance(row[1], int)
        ):
            raise TypeError("lane_schedule rows must be [time, active lanes]")
        schedule.append((float(row[0]), row[1]))
    return tuple(schedule)


def _scenario_config(
    base: SimulationConfig,
    scenario: dict[str, object],
    policy: str,
    seed: int,
    capacity: float,
) -> SimulationConfig:
    load = _number(scenario, "load_regime", 0.95)
    arrival_rate = capacity * load
    arrival_mode = _text(scenario, "arrival_mode", "poisson")
    batch_interval = base.arrival.batch_size * 3600.0 / arrival_rate
    footprint_case = _text(scenario, "footprint_case", "base")
    if footprint_case == "high":
        passenger = replace(
            base.passenger,
            body_footprint_m2=0.28,
            luggage_footprint_m2_per_bag=0.18,
            static_clearance_m2=0.55,
            moving_clearance_m2=0.80,
        )
    elif footprint_case == "base":
        passenger = base.passenger
    else:
        raise ValueError(f"Unsupported footprint case: {footprint_case}")
    passenger = replace(
        passenger,
        release_compliance=_number(
            scenario,
            "release_compliance",
            passenger.release_compliance,
        ),
    )
    restricted = _boolean(scenario, "restricted_space")
    geometry = replace(
        base.geometry,
        layout="B0" if policy == "S0" else "B1",
        downstream_capacity=int(
            _number(
                scenario,
                "downstream_capacity",
                base.geometry.downstream_capacity,
            )
        ),
        row_angle_degrees=_number(
            scenario,
            "row_angle_degrees",
            base.geometry.row_angle_degrees,
        ),
        gate_width_m=_number(
            scenario,
            "gate_width_m",
            base.geometry.gate_width_m,
        ),
        release_staff_count=(
            int(
                _number(
                    scenario,
                    "s3_release_staff_count",
                    base.geometry.release_staff_count,
                )
            )
            if policy == "S3"
            else base.geometry.release_staff_count
        ),
        waiting_area_m2=45.0 if restricted else base.geometry.waiting_area_m2,
        width_m=10.0 if restricted else base.geometry.width_m,
        barrier_footprint_m2=12.0 if restricted else base.geometry.barrier_footprint_m2,
        downstream_staging_area_m2=(
            20.0 if restricted else base.geometry.downstream_staging_area_m2
        ),
    )
    return replace(
        base,
        seed=seed,
        horizon_seconds=3600.0,
        drain_limit_seconds=3600.0,
        arrival=replace(
            base.arrival,
            mode=arrival_mode,
            rate_per_hour=arrival_rate,
            batch_interval_seconds=batch_interval,
        ),
        service=replace(
            base.service,
            cv=_number(scenario, "service_cv", base.service.cv),
            lane_schedule=_lane_schedule(scenario),
        ),
        passenger=passenger,
        geometry=geometry,
        control=replace(
            base.control,
            policy=policy,
            batch_size=(
                int(
                    _number(
                        scenario,
                        "s3_batch_size",
                        base.control.batch_size,
                    )
                )
                if policy == "S3"
                else base.control.batch_size
            ),
            downstream_threshold=(
                int(
                    _number(
                        scenario,
                        "s3_downstream_threshold",
                        base.control.downstream_threshold,
                    )
                )
                if policy == "S3"
                else base.control.downstream_threshold
            ),
            decision_interval_seconds=(
                _number(
                    scenario,
                    "s3_decision_interval_seconds",
                    base.control.decision_interval_seconds,
                )
                if policy == "S3"
                else base.control.decision_interval_seconds
            ),
            maximum_hold_seconds=_number(
                scenario,
                "maximum_hold_seconds",
                base.control.maximum_hold_seconds,
            ),
            gate_delay_seconds=(
                _number(
                    scenario,
                    "s3_gate_delay_seconds",
                    base.control.gate_delay_seconds,
                )
                if policy == "S3"
                else base.control.gate_delay_seconds
            ),
        ),
    )


def main() -> None:
    specification_path = Path("configs/phase8_falsification.yaml")
    specification = _mapping(
        yaml.safe_load(specification_path.read_text(encoding="utf-8")),
        "falsification specification",
    )
    base = load_config(str(specification["base_config"]))
    scenarios_value = specification["scenarios"]
    if not isinstance(scenarios_value, list):
        raise TypeError("scenarios must be a list")
    scenarios = [
        _mapping(value, "scenario")
        for value in scenarios_value
    ]
    replications = _integer(specification["replications"], "replications")
    seed_base = _integer(specification["seed_base"], "seed base")
    workers = _integer(specification["maximum_workers"], "maximum workers")
    capacity = _capacity_per_hour(base)
    specification_hash = hashlib.sha256(specification_path.read_bytes()).hexdigest()
    model_hash, model_files = _model_hash(specification_path)
    checkpoint_root = Path("results/checkpoints/phase8")
    output_root = Path("results/phase8")
    checkpoint_root.mkdir(parents=True, exist_ok=True)
    output_root.mkdir(parents=True, exist_ok=True)
    manifest_path = checkpoint_root / "manifest.json"
    if manifest_path.exists():
        manifest = _mapping(
            json.loads(manifest_path.read_text(encoding="utf-8")),
            "checkpoint manifest",
        )
        if manifest.get("model_sha256") != model_hash:
            raise SystemExit("Phase 8 checkpoint model hash mismatch")
    _write_json_atomic(
        manifest_path,
        {
            "specification_sha256": specification_hash,
            "model_sha256": model_hash,
            "model_files": model_files,
            "scenarios": len(scenarios),
            "replications": replications,
        },
    )

    tasks: list[tuple[Path, SimulationConfig, dict[str, float | int | str]]] = []
    rows: list[dict[str, float | int | str]] = []
    for scenario_index, scenario in enumerate(scenarios):
        scenario_id = _text(scenario, "scenario_id", "")
        category = _text(scenario, "category", "")
        load = _number(scenario, "load_regime", 0.95)
        for replication in range(replications):
            seed = seed_base + scenario_index * 1000 + replication
            for policy in ("S0", "S3"):
                metadata: dict[str, float | int | str] = {
                    "scenario_id": scenario_id,
                    "category": category,
                    "load_regime": load,
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
                config = _scenario_config(base, scenario, policy, seed, capacity)
                tasks.append((checkpoint, config, metadata))

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
            "specification_sha256": specification_hash,
            "model_sha256": model_hash,
            "scenario_count": len(scenarios),
            "replications_per_policy_scenario": replications,
            "replication_rows": len(rows),
        },
    )


if __name__ == "__main__":
    main()
