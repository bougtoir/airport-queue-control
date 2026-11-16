from __future__ import annotations

import csv
import math
from collections import defaultdict
from pathlib import Path
from statistics import mean, stdev

from scipy import stats


def _read(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _paired(
    baseline: list[dict[str, str]],
    intervention: list[dict[str, str]],
    metric: str,
) -> tuple[float, float, float]:
    differences = [
        float(right[metric]) - float(left[metric])
        for left, right in zip(baseline, intervention, strict=True)
    ]
    estimate = mean(differences)
    critical = float(stats.t.ppf(0.975, len(differences) - 1))
    half_width = critical * stdev(differences) / math.sqrt(len(differences))
    return estimate, estimate - half_width, estimate + half_width


def main() -> None:
    root = Path("results/phase9")
    rows = _read(root / "replications.csv")
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[(row["scenario_id"], row["policy"])].append(row)
    summary_rows: list[dict[str, float | int | str]] = []
    transfer_rows: list[dict[str, float | int | str]] = []
    for (scenario_id, policy), values in sorted(grouped.items()):
        summary_rows.append(
            {
                "scenario_id": scenario_id,
                "geometry_id": values[0]["geometry_id"],
                "regime_id": values[0]["regime_id"],
                "policy": policy,
                "replications": len(values),
                "mean_throughput_per_hour": mean(
                    float(row["throughput_per_hour"]) for row in values
                ),
                "mean_wait_seconds": mean(
                    float(row["mean_wait_seconds"]) for row in values
                ),
                "mean_movement_starts": mean(
                    float(row["mean_movement_starts"]) for row in values
                ),
                "mean_distance_m": mean(
                    float(row["mean_movement_distance_m"]) for row in values
                ),
                "mean_required_waiting_area_m2": mean(
                    float(row["required_waiting_area_m2_at_density_limit"])
                    for row in values
                ),
                "mean_capacity_efficiency": mean(
                    float(row["capacity_efficiency_passengers_per_m2"])
                    for row in values
                ),
                "mean_unfinished": mean(float(row["unfinished"]) for row in values),
            }
        )
    for scenario_id in sorted({row["scenario_id"] for row in rows}):
        baseline = sorted(
            grouped[(scenario_id, "S0")],
            key=lambda row: int(row["replication"]),
        )
        baseline_throughput = mean(
            float(row["throughput_per_hour"]) for row in baseline
        )
        for policy in ("S3", "S5"):
            intervention = sorted(
                grouped[(scenario_id, policy)],
                key=lambda row: int(row["replication"]),
            )
            throughput = _paired(
                baseline,
                intervention,
                "throughput_per_hour",
            )
            movement = _paired(
                baseline,
                intervention,
                "mean_movement_starts",
            )
            waiting = _paired(
                baseline,
                intervention,
                "mean_wait_seconds",
            )
            first = baseline[0]
            transfer_rows.append(
                {
                    "scenario_id": scenario_id,
                    "geometry_id": first["geometry_id"],
                    "regime_id": first["regime_id"],
                    "policy": policy,
                    "throughput_difference": throughput[0],
                    "throughput_ci95_lower": throughput[1],
                    "throughput_ci95_upper": throughput[2],
                    "throughput_relative_lower_bound": (
                        throughput[1] / baseline_throughput
                    ),
                    "movement_starts_difference": movement[0],
                    "movement_starts_ci95_lower": movement[1],
                    "movement_starts_ci95_upper": movement[2],
                    "mean_wait_difference_seconds": waiting[0],
                    "throughput_acceptable_2pct": (
                        "yes"
                        if throughput[1] / baseline_throughput >= -0.02
                        else "no"
                    ),
                }
            )
    for path, values in (
        (root / "policy_summary.csv", summary_rows),
        (root / "transferability_comparisons.csv", transfer_rows),
    ):
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=list(values[0]),
                lineterminator="\n",
            )
            writer.writeheader()
            writer.writerows(values)
    acceptable = sum(
        row["throughput_acceptable_2pct"] == "yes" for row in transfer_rows
    )
    lines = [
        "# Phase 9 transferability benchmark",
        "",
        (
            "The open benchmark crosses three generic terminal geometries with three "
            "demand/service regimes and compares S0, S3, and S5 using 20 paired replications."
        ),
        "",
        (
            f"{acceptable} of {len(transfer_rows)} policy-scenario comparisons satisfy the "
            "paired 2% throughput criterion."
        ),
        "",
        "| Scenario | Policy | Throughput lower bound | Starts diff | Wait diff (s) | Acceptable |",
        "|---|---|---:|---:|---:|---|",
    ]
    for row in transfer_rows:
        lines.append(
            f"| {row['scenario_id']} | {row['policy']} | "
            f"{float(row['throughput_relative_lower_bound']):.3f} | "
            f"{float(row['movement_starts_difference']):.3f} | "
            f"{float(row['mean_wait_difference_seconds']):.1f} | "
            f"{row['throughput_acceptable_2pct']} |"
        )
    lines.extend(
        [
            "",
            (
                "These generic cases demonstrate configuration portability, not universal "
                "external validity. Geometry, demand, and service inputs remain assumptions "
                "unless replaced by locally measured values."
            ),
            "",
        ]
    )
    Path("PHASE_09_BENCHMARK_REPORT.md").write_text(
        "\n".join(lines),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
