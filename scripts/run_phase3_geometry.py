from __future__ import annotations

import argparse
import csv
from dataclasses import replace
from pathlib import Path

import yaml

from airport_batch_queue.config import load_config
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


def _integer(mapping: dict[str, object], key: str) -> int:
    value = mapping[key]
    if not isinstance(value, int):
        raise TypeError(f"{key} must be an integer")
    return value


def _text(mapping: dict[str, object], key: str) -> str:
    value = mapping[key]
    if not isinstance(value, str):
        raise TypeError(f"{key} must be text")
    return value


def _mapping_list(root: dict[str, object], key: str) -> list[dict[str, object]]:
    value = root[key]
    if not isinstance(value, list):
        raise TypeError(f"{key} must be a list")
    return [_mapping(item, key) for item in value]


def _number_list(root: dict[str, object], key: str) -> list[float]:
    value = root[key]
    if not isinstance(value, list) or not all(
        isinstance(item, (int, float)) for item in value
    ):
        raise TypeError(f"{key} must be a numeric list")
    return [float(item) for item in value]


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Phase 3 geometry screen")
    parser.add_argument(
        "--screen",
        type=Path,
        default=Path("configs/phase3_geometry_screen.yaml"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/phase3_space_guidance/layout_angle_screen.csv"),
    )
    args = parser.parse_args()

    loaded: object = yaml.safe_load(args.screen.read_text(encoding="utf-8"))
    screen = _mapping(loaded, "geometry screen")
    base = load_config(_text(screen, "base_config"))
    architectures = _mapping_list(screen, "architectures")
    footprint_cases = _mapping_list(screen, "footprint_cases")
    row_angles = _number_list(screen, "row_angles_degrees")
    seeds = [int(seed) for seed in _number_list(screen, "seeds")]
    rows: list[dict[str, object]] = []

    for architecture in architectures:
        layout = _text(architecture, "layout")
        angles = [0.0] if layout == "B0" else row_angles
        for footprint in footprint_cases:
            for angle in angles:
                for seed in seeds:
                    config = replace(
                        base,
                        seed=seed,
                        horizon_seconds=_number(screen, "horizon_seconds"),
                        drain_limit_seconds=_number(screen, "drain_limit_seconds"),
                        passenger=replace(
                            base.passenger,
                            body_footprint_m2=_number(
                                footprint,
                                "body_footprint_m2",
                            ),
                            luggage_footprint_m2_per_bag=_number(
                                footprint,
                                "luggage_footprint_m2_per_bag",
                            ),
                            static_clearance_m2=_number(
                                footprint,
                                "static_clearance_m2",
                            ),
                            moving_clearance_m2=_number(
                                footprint,
                                "moving_clearance_m2",
                            ),
                        ),
                        geometry=replace(
                            base.geometry,
                            layout=layout,
                            barrier_footprint_m2=_number(
                                architecture,
                                "barrier_footprint_m2",
                            ),
                            row_angle_degrees=angle,
                            release_staff_count=_integer(
                                architecture,
                                "release_staff_count",
                            ),
                        ),
                        control=replace(
                            base.control,
                            policy=_text(architecture, "policy"),
                            gate_delay_seconds=_number(
                                architecture,
                                "gate_delay_seconds",
                            ),
                        ),
                    )
                    summary = dict(run_simulation(config).summary)
                    rows.append(
                        {
                            "architecture_label": _text(architecture, "label"),
                            "footprint_case": _text(footprint, "name"),
                            **summary,
                        }
                    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(rows[0]),
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
