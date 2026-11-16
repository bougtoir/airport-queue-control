from __future__ import annotations

import argparse
import csv
from dataclasses import replace
from pathlib import Path

from airport_batch_queue.config import load_config
from airport_batch_queue.simulator import run_simulation


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the six policy implementations")
    parser.add_argument("--config", type=Path, default=Path("configs/default.yaml"))
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/phase2_policy_smoke/summary.csv"),
    )
    args = parser.parse_args()

    base = load_config(args.config)
    rows: list[dict[str, object]] = []
    for policy in ("S0", "S1", "S2", "S3", "S4", "S5"):
        config = replace(
            base,
            control=replace(base.control, policy=policy),
        )
        result = run_simulation(config)
        rows.append(dict(result.summary))

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
