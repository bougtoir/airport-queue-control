from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict
from pathlib import Path

import yaml

from airport_batch_queue.config import load_config
from airport_batch_queue.simulator import run_simulation


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(rows[0]),
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run an airport queue simulation")
    parser.add_argument("config", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    config = load_config(args.config)
    result = run_simulation(config)
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "summary.json").write_text(
        json.dumps(result.summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _write_csv(args.output / "passengers.csv", result.passenger_rows())
    _write_csv(args.output / "trajectory.csv", result.trajectories)
    (args.output / "config_resolved.yaml").write_text(
        yaml.safe_dump(asdict(config), sort_keys=False),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
