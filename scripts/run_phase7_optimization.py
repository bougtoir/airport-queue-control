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


def _number_list(value: object, name: str) -> list[float]:
    if not isinstance(value, list) or not all(
        isinstance(item, (int, float)) for item in value
    ):
        raise TypeError(f"{name} must be a numeric list")
    return [float(item) for item in value]


def _integer(value: object, name: str) -> int:
    if not isinstance(value, int):
        raise TypeError(f"{name} must be an integer")
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


def _designs(specification: dict[str, object]) -> list[dict[str, float | int | str]]:
    designs: list[dict[str, float | int | str]] = [
        {
            "design_id": "baseline_S0_B0",
            "policy": "S0",
            "layout": "B0",
            "row_angle_degrees": 0.0,
            "batch_size": 12,
            "sub_batch_size": 4,
            "downstream_threshold": 6,
            "barrier_footprint_m2": 8.0,
            "release_staff_count": 1,
            "gate_delay_seconds": 0.75,
        }
    ]
    layouts = _mapping(specification["layouts"], "layouts")
    policies = _mapping(specification["policies"], "policies")
    angles = _number_list(specification["row_angles_degrees"], "row angles")
    for layout_name, layout_value in layouts.items():
        layout = _mapping(layout_value, layout_name)
        for angle in angles:
            for policy_name, policy_value in policies.items():
                policy = _mapping(policy_value, policy_name)
                if policy_name == "S1":
                    combinations = [
                        (int(batch), 4, 6)
                        for batch in _number_list(
                            policy["batch_sizes"],
                            f"{policy_name} batch sizes",
                        )
                    ]
                elif policy_name == "S2":
                    combinations = [
                        (12, int(batch), 6)
                        for batch in _number_list(
                            policy["sub_batch_sizes"],
                            f"{policy_name} sub-batch sizes",
                        )
                    ]
                elif policy_name == "S3":
                    combinations = [
                        (int(batch), 4, int(threshold))
                        for batch in _number_list(
                            policy["batch_sizes"],
                            f"{policy_name} batch sizes",
                        )
                        for threshold in _number_list(
                            policy["downstream_thresholds"],
                            f"{policy_name} thresholds",
                        )
                    ]
                elif policy_name == "S4":
                    combinations = [
                        (int(batch), 4, 6)
                        for batch in _number_list(
                            policy["batch_sizes"],
                            f"{policy_name} batch sizes",
                        )
                    ]
                else:
                    raise ValueError(f"Unsupported optimization policy: {policy_name}")
                for batch_size, sub_batch_size, threshold in combinations:
                    design_id = (
                        f"{policy_name}_{layout_name}_a{int(angle):02d}"
                        f"_b{batch_size:02d}_s{sub_batch_size:02d}_t{threshold:02d}"
                    )
                    designs.append(
                        {
                            "design_id": design_id,
                            "policy": policy_name,
                            "layout": layout_name,
                            "row_angle_degrees": angle,
                            "batch_size": batch_size,
                            "sub_batch_size": sub_batch_size,
                            "downstream_threshold": threshold,
                            "barrier_footprint_m2": float(
                                layout["barrier_footprint_m2"]
                            ),
                            "release_staff_count": int(
                                layout["release_staff_count"]
                            ),
                            "gate_delay_seconds": float(
                                layout["gate_delay_seconds"]
                            ),
                        }
                    )
    return designs


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


def main() -> None:
    specification_path = Path("configs/phase7_optimization.yaml")
    loaded: object = yaml.safe_load(specification_path.read_text(encoding="utf-8"))
    specification = _mapping(loaded, "optimization specification")
    base_path = Path(str(specification["base_config"]))
    base = load_config(base_path)
    designs = _designs(specification)
    loads = _number_list(specification["load_regimes"], "load regimes")
    replications = _integer(specification["replications"], "replications")
    seed_base = _integer(specification["seed_base"], "seed base")
    workers = _integer(specification["maximum_workers"], "maximum workers")
    capacity = _capacity_per_hour(base)
    specification_hash = hashlib.sha256(specification_path.read_bytes()).hexdigest()
    model_hash, model_files = _model_hash(specification_path)

    checkpoint_root = Path("results/checkpoints/phase7")
    output_root = Path("results/phase7")
    checkpoint_root.mkdir(parents=True, exist_ok=True)
    output_root.mkdir(parents=True, exist_ok=True)
    manifest_path = checkpoint_root / "manifest.json"
    if manifest_path.exists():
        manifest = _mapping(
            json.loads(manifest_path.read_text(encoding="utf-8")),
            "checkpoint manifest",
        )
        if manifest.get("model_sha256") != model_hash:
            raise SystemExit("Phase 7 checkpoint model hash mismatch")
    _write_json_atomic(
        manifest_path,
        {
            "specification_sha256": specification_hash,
            "model_sha256": model_hash,
            "model_files": model_files,
            "designs": len(designs),
            "loads": loads,
            "replications": replications,
        },
    )

    tasks: list[tuple[Path, SimulationConfig, dict[str, float | int | str]]] = []
    rows: list[dict[str, float | int | str]] = []
    for load_index, load in enumerate(loads):
        arrival_rate = capacity * load
        for replication in range(replications):
            seed = seed_base + load_index * 10_000 + replication
            for design in designs:
                design_id = str(design["design_id"])
                metadata = {
                    **design,
                    "load_regime": load,
                    "replication": replication,
                    "seed": seed,
                    "arrival_rate_per_hour": arrival_rate,
                }
                checkpoint = (
                    checkpoint_root
                    / f"rho_{load:.2f}"
                    / design_id
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
                config = replace(
                    base,
                    seed=seed,
                    horizon_seconds=3600.0,
                    drain_limit_seconds=3600.0,
                    arrival=replace(base.arrival, rate_per_hour=arrival_rate),
                    geometry=replace(
                        base.geometry,
                        layout=str(design["layout"]),
                        row_angle_degrees=float(design["row_angle_degrees"]),
                        barrier_footprint_m2=float(
                            design["barrier_footprint_m2"]
                        ),
                        release_staff_count=int(design["release_staff_count"]),
                    ),
                    control=replace(
                        base.control,
                        policy=str(design["policy"]),
                        batch_size=int(design["batch_size"]),
                        sub_batch_size=int(design["sub_batch_size"]),
                        downstream_threshold=int(
                            design["downstream_threshold"]
                        ),
                        gate_delay_seconds=float(design["gate_delay_seconds"]),
                    ),
                )
                tasks.append((checkpoint, config, metadata))

    with ProcessPoolExecutor(max_workers=workers) as executor:
        summaries = executor.map(_run, [config for _, config, _ in tasks])
        for (checkpoint, _, metadata), summary in zip(tasks, summaries, strict=True):
            checkpoint.parent.mkdir(parents=True, exist_ok=True)
            _write_json_atomic(checkpoint, summary)
            rows.append({**metadata, **summary})

    rows.sort(
        key=lambda row: (
            float(row["load_regime"]),
            str(row["design_id"]),
            int(row["replication"]),
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
            "design_count": len(designs),
            "load_regimes": loads,
            "replications_per_design_load": replications,
            "replication_rows": len(rows),
        },
    )


if __name__ == "__main__":
    main()
