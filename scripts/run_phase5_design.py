from __future__ import annotations

import argparse
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


def _number_list(mapping: dict[str, object], key: str) -> list[float]:
    value = mapping[key]
    if not isinstance(value, list) or not all(isinstance(item, (int, float)) for item in value):
        raise TypeError(f"{key} must be a numeric list")
    return [float(item) for item in value]


def _string_list(mapping: dict[str, object], key: str) -> list[str]:
    value = mapping[key]
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise TypeError(f"{key} must be a text list")
    return list(value)


def _integer(mapping: dict[str, object], key: str) -> int:
    value = mapping[key]
    if not isinstance(value, int):
        raise TypeError(f"{key} must be an integer")
    return value


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


def _capacity_per_hour(config: SimulationConfig) -> float:
    expected_service = (
        config.service.mean_seconds
        + config.service.secondary_probability * config.service.secondary_mean_seconds
        + config.service.long_inspection_probability
        * config.service.long_inspection_mean_seconds
    )
    return config.service.servers * 3600.0 / expected_service


def _run(config: SimulationConfig) -> dict[str, float | int | str]:
    return dict(run_simulation(config).summary)


def _write_json_atomic(path: Path, value: object) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _model_manifest(base_config: Path) -> dict[str, object]:
    files = [
        *sorted(Path("src/airport_batch_queue").glob("*.py")),
        base_config,
        Path(__file__),
    ]
    root = Path.cwd().resolve()
    hashes = {}
    for path in files:
        resolved = path.resolve()
        relative = resolved.relative_to(root).as_posix()
        hashes[relative] = hashlib.sha256(resolved.read_bytes()).hexdigest()
    bundle = hashlib.sha256(
        "\n".join(f"{path} {value}" for path, value in hashes.items()).encode()
    ).hexdigest()
    return {"bundle_sha256": bundle, "files": hashes}


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the locked comparative design")
    parser.add_argument("--plan", type=Path, default=Path("ANALYSIS_PLAN_LOCKED.yaml"))
    parser.add_argument("--output", type=Path, default=Path("results/phase5"))
    parser.add_argument("--replications", type=int)
    args = parser.parse_args()

    with args.plan.open(encoding="utf-8") as handle:
        loaded: object = yaml.safe_load(handle)
    plan_hash = hashlib.sha256(args.plan.read_bytes()).hexdigest()
    hash_file = args.plan.with_suffix(".sha256")
    expected_hash = hash_file.read_text(encoding="utf-8").split()[0]
    if plan_hash != expected_hash:
        raise SystemExit("Locked analysis plan hash mismatch")
    plan = _mapping(loaded, "plan")
    replication_plan = _mapping(plan["replications"], "replications")
    base_config = Path(_text(plan, "base_config"))
    base = load_config(base_config)
    replications = args.replications or _integer(replication_plan, "count")
    routine_cap = _integer(replication_plan, "routine_cap")
    if replications < 2 or replications > routine_cap:
        raise SystemExit(f"Replications must be between 2 and the locked cap of {routine_cap}")
    seed_base = _integer(replication_plan, "seed_base")
    workers = _integer(replication_plan, "maximum_workers")
    policies = _string_list(plan, "policies")
    load_regimes = _number_list(plan, "load_regimes")
    capacity = _capacity_per_hour(base)
    model_manifest = _model_manifest(base_config)
    model_hash = str(model_manifest["bundle_sha256"])
    checkpoint_root = Path("results/checkpoints/phase5")
    checkpoint_root.mkdir(parents=True, exist_ok=True)
    args.output.mkdir(parents=True, exist_ok=True)
    manifest_path = checkpoint_root / "manifest.json"
    if manifest_path.exists():
        manifest = _mapping(
            json.loads(manifest_path.read_text(encoding="utf-8")),
            "checkpoint manifest",
        )
        if manifest.get("plan_sha256") != plan_hash:
            raise SystemExit("Checkpoint plan hash does not match the locked analysis plan")
        if manifest.get("model_sha256") != model_hash:
            raise SystemExit("Checkpoint model hash does not match the current model")
    _write_json_atomic(
        manifest_path,
        {
            "plan_sha256": plan_hash,
            "model_sha256": model_hash,
            "model_files": model_manifest["files"],
            "nominal_capacity_per_hour": capacity,
            "requested_replications": replications,
        },
    )

    tasks: list[tuple[Path, SimulationConfig, dict[str, float | int | str]]] = []
    rows: list[dict[str, float | int | str]] = []
    seeds: list[dict[str, float | int | str]] = []
    for scenario_index, load in enumerate(load_regimes):
        scenario = f"rho_{load:.2f}"
        arrival_rate = capacity * load
        for replication in range(replications):
            seed = seed_base + scenario_index * 10_000 + replication
            seeds.append(
                {
                    "load_regime": load,
                    "replication": replication,
                    "seed": seed,
                    "arrival_rate_per_hour": arrival_rate,
                }
            )
            for policy in policies:
                checkpoint = checkpoint_root / scenario / policy / f"rep_{replication:03d}.json"
                metadata: dict[str, float | int | str] = {
                    "load_regime": load,
                    "replication": replication,
                    "seed": seed,
                    "arrival_rate_per_hour": arrival_rate,
                    "policy": policy,
                }
                if checkpoint.exists():
                    try:
                        saved: object = json.loads(checkpoint.read_text(encoding="utf-8"))
                        row = _mapping(saved, "checkpoint")
                        rows.append({**metadata, **row})
                        continue
                    except JSONDecodeError:
                        pass
                config = replace(
                    base,
                    seed=seed,
                    horizon_seconds=_number(plan, "horizon_seconds"),
                    drain_limit_seconds=_number(plan, "drain_limit_seconds"),
                    time_step_seconds=_number(plan, "time_step_seconds"),
                    arrival=replace(
                        base.arrival,
                        mode=_text(plan, "arrival_mode"),
                        rate_per_hour=arrival_rate,
                    ),
                    service=replace(
                        base.service,
                        distribution=_text(plan, "service_distribution"),
                    ),
                    control=replace(base.control, policy=policy),
                )
                tasks.append((checkpoint, config, metadata))

    with ProcessPoolExecutor(max_workers=workers) as executor:
        summaries = executor.map(_run, [config for _, config, _ in tasks])
        for (checkpoint, _, metadata), summary in zip(tasks, summaries, strict=True):
            checkpoint.parent.mkdir(parents=True, exist_ok=True)
            _write_json_atomic(checkpoint, summary)
            rows.append({**metadata, **summary})

    rows.sort(key=lambda row: (float(row["load_regime"]), int(row["replication"]), str(row["policy"])))
    seeds.sort(key=lambda row: (float(row["load_regime"]), int(row["replication"])))
    for path, output_rows in (
        (args.output / "replications.csv", rows),
        (args.output / "seeds.csv", seeds),
    ):
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=list(output_rows[0]),
                lineterminator="\n",
            )
            writer.writeheader()
            writer.writerows(output_rows)
    _write_json_atomic(
        args.output / "run_manifest.json",
        {
            "status": "complete",
            "plan_sha256": plan_hash,
            "model_sha256": model_hash,
            "model_files": model_manifest["files"],
            "nominal_capacity_per_hour": capacity,
            "replications_per_cell": replications,
            "load_regimes": load_regimes,
            "policies": policies,
            "replication_rows": len(rows),
            "seed_rows": len(seeds),
        },
    )


if __name__ == "__main__":
    main()
