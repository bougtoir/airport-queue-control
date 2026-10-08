from __future__ import annotations

import csv
import math
from dataclasses import replace
from pathlib import Path
from statistics import mean, stdev

from scipy import stats

from airport_batch_queue.config import load_config
from airport_batch_queue.simulator import run_simulation

OUTPUT_DIR = Path("results/phase13")
REPLICATIONS = 50
LOADS = (0.85, 0.95)
SCENARIOS = {
    "configured_routes": (55.0, 10, 22.0, 2),
    "matched_short_route": (22.0, 2, 22.0, 2),
    "matched_mid_route": (38.5, 6, 38.5, 6),
    "matched_long_route": (55.0, 10, 55.0, 10),
}
METRICS = (
    "throughput_per_hour",
    "mean_movement_starts",
    "mean_movement_stops",
    "mean_movement_time_seconds",
    "mean_wait_seconds",
    "utilization",
    "starvation_fraction_with_upstream_demand",
    "mean_movement_distance_m",
    "mean_turning_angle_degrees",
)


def _capacity_per_hour(config) -> float:
    expected_service = (
        config.service.mean_seconds
        + config.service.secondary_probability * config.service.secondary_mean_seconds
        + config.service.long_inspection_probability
        * config.service.long_inspection_mean_seconds
    )
    return config.service.servers * 3600.0 / expected_service


def _write(path: Path, rows: list[dict[str, float | int | str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    base = load_config("configs/default.yaml")
    capacity = _capacity_per_hour(base)
    replication_rows: list[dict[str, float | int | str]] = []
    for scenario, routes in SCENARIOS.items():
        s0_distance, s0_turns, s3_distance, s3_turns = routes
        geometry = replace(
            base.geometry,
            serpentine_distance_m=s0_distance,
            serpentine_turns=s0_turns,
            stationary_distance_m=s3_distance,
            stationary_turns=s3_turns,
        )
        for load in LOADS:
            for replication in range(REPLICATIONS):
                seed = 730000 + replication
                for policy, layout in (("S0", "B0"), ("S3", "B1")):
                    config = replace(
                        base,
                        seed=seed,
                        horizon_seconds=3600,
                        drain_limit_seconds=3600,
                        arrival=replace(
                            base.arrival,
                            rate_per_hour=capacity * load,
                        ),
                        geometry=replace(geometry, layout=layout),
                        control=replace(base.control, policy=policy),
                    )
                    summary = run_simulation(config).summary
                    row: dict[str, float | int | str] = {
                        "scenario": scenario,
                        "load_regime": load,
                        "replication": replication,
                        "seed": seed,
                        "policy": policy,
                        "s0_distance_m": s0_distance,
                        "s0_turns": s0_turns,
                        "s3_distance_m": s3_distance,
                        "s3_turns": s3_turns,
                    }
                    row.update({metric: summary[metric] for metric in METRICS})
                    replication_rows.append(row)
    _write(OUTPUT_DIR / "replications.csv", replication_rows)

    summary_rows: list[dict[str, float | int | str]] = []
    for scenario in SCENARIOS:
        for load in LOADS:
            group = [
                row
                for row in replication_rows
                if row["scenario"] == scenario and row["load_regime"] == load
            ]
            policies = {
                policy: sorted(
                    [row for row in group if row["policy"] == policy],
                    key=lambda row: int(row["replication"]),
                )
                for policy in ("S0", "S3")
            }
            result: dict[str, float | int | str] = {
                "scenario": scenario,
                "load_regime": load,
                "replications": REPLICATIONS,
            }
            for metric in METRICS:
                baseline = [float(row[metric]) for row in policies["S0"]]
                intervention = [float(row[metric]) for row in policies["S3"]]
                differences = [
                    treatment - control
                    for treatment, control in zip(intervention, baseline, strict=True)
                ]
                average = mean(differences)
                half_width = (
                    float(stats.t.ppf(0.975, REPLICATIONS - 1))
                    * stdev(differences)
                    / math.sqrt(REPLICATIONS)
                )
                result[f"s0_{metric}"] = mean(baseline)
                result[f"s3_{metric}"] = mean(intervention)
                result[f"difference_{metric}"] = average
                result[f"ci95_lower_{metric}"] = average - half_width
                result[f"ci95_upper_{metric}"] = average + half_width
            baseline_throughput = float(result["s0_throughput_per_hour"])
            result["throughput_relative_lower_bound"] = (
                float(result["ci95_lower_throughput_per_hour"]) / baseline_throughput
            )
            result["throughput_acceptable_2pct"] = (
                "yes"
                if float(result["throughput_relative_lower_bound"]) >= -0.02
                else "no"
            )
            summary_rows.append(result)
    _write(OUTPUT_DIR / "summary.csv", summary_rows)

    matched = [row for row in summary_rows if row["scenario"] != "configured_routes"]
    lines = [
        "# Phase 13 structural route sensitivity",
        "",
        (
            "This analysis holds the S0 and S3 path distance and turn count equal at short, "
            "mid, and long route definitions. It tests whether the movement-start and "
            "throughput comparisons require the configured B0/B1 route advantage."
        ),
        "",
        (
            "| Scenario | Load | Throughput difference/h (95% CI) | "
            "Starts difference (95% CI) | Throughput criterion |"
        ),
        "|---|---:|---:|---:|---|",
    ]
    for row in summary_rows:
        lines.append(
            f"| {row['scenario']} | {float(row['load_regime']):.2f} | "
            f"{float(row['difference_throughput_per_hour']):.1f} "
            f"({float(row['ci95_lower_throughput_per_hour']):.1f}, "
            f"{float(row['ci95_upper_throughput_per_hour']):.1f}) | "
            f"{float(row['difference_mean_movement_starts']):.2f} "
            f"({float(row['ci95_lower_mean_movement_starts']):.2f}, "
            f"{float(row['ci95_upper_mean_movement_starts']):.2f}) | "
            f"{row['throughput_acceptable_2pct']} |"
        )
    retained = sum(row["throughput_acceptable_2pct"] == "yes" for row in matched)
    lines.extend(
        [
            "",
            (
                f"The throughput criterion is retained in {retained} of {len(matched)} "
                "matched-route cases. Distance and turning differences become zero by design. "
                "The remaining movement-start contrast is not solely route-length or turning "
                "driven, but remains conditional on the explicit queue-progression and "
                "release-control rules rather than externally validated."
            ),
            "",
        ]
    )
    Path("PHASE_13_STRUCTURAL_SENSITIVITY.md").write_text(
        "\n".join(lines),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
