from __future__ import annotations

import csv
import math
from collections import defaultdict
from pathlib import Path
from statistics import mean, stdev

import yaml
from scipy import stats


def _read(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write(path: Path, rows: list[dict[str, float | int | str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(rows[0]),
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def _mapping(value: object, name: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise TypeError(f"{name} must be a mapping")
    return {str(key): item for key, item in value.items()}


def _dominates(
    left: dict[str, float | int | str],
    right: dict[str, float | int | str],
    minimize: list[str],
    maximize: list[str],
) -> bool:
    no_worse = all(float(left[key]) <= float(right[key]) for key in minimize)
    no_worse = no_worse and all(
        float(left[key]) >= float(right[key]) for key in maximize
    )
    strictly_better = any(
        float(left[key]) < float(right[key]) for key in minimize
    ) or any(float(left[key]) > float(right[key]) for key in maximize)
    return no_worse and strictly_better


def main() -> None:
    root = Path("results/phase7")
    rows = _read(root / "replications.csv")
    specification = _mapping(
        yaml.safe_load(
            Path("configs/phase7_optimization.yaml").read_text(encoding="utf-8")
        ),
        "optimization specification",
    )
    constraints = _mapping(specification["constraints"], "constraints")
    objectives = _mapping(specification["pareto_objectives"], "objectives")
    minimize = [str(value) for value in objectives["minimize"]]
    maximize = [str(value) for value in objectives["maximize"]]
    metrics = [
        "throughput_per_hour",
        "mean_movement_starts",
        "mean_movement_stops",
        "mean_turning_angle_degrees",
        "mean_movement_distance_m",
        "mean_movement_time_seconds",
        "mean_wait_seconds",
        "p95_wait_seconds",
        "required_waiting_area_m2_at_density_limit",
        "capacity_efficiency_passengers_per_m2",
        "density_limit_exceedance_fraction",
        "mean_movement_conflict_proxy",
        "intervention_count",
        "unfinished",
    ]
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    indexed: dict[tuple[str, str, str], dict[str, str]] = {}
    for row in rows:
        grouped[(row["design_id"], row["load_regime"])].append(row)
        indexed[(row["design_id"], row["load_regime"], row["replication"])] = row

    aggregate_rows: list[dict[str, float | int | str]] = []
    for (design_id, load), group in sorted(grouped.items()):
        first = group[0]
        result: dict[str, float | int | str] = {
            "design_id": design_id,
            "load_regime": load,
            "policy": first["policy"],
            "layout": first["layout"],
            "row_angle_degrees": float(first["row_angle_degrees"]),
            "batch_size": int(float(first["batch_size"])),
            "sub_batch_size": int(float(first["sub_batch_size"])),
            "downstream_threshold": int(float(first["downstream_threshold"])),
            "barrier_footprint_m2": float(first["barrier_footprint_m2"]),
            "release_staff_count": int(float(first["release_staff_count"])),
            "gate_delay_seconds": float(first["gate_delay_seconds"]),
            "replications": len(group),
        }
        for metric in metrics:
            result[metric] = mean(float(row[metric]) for row in group)
        baseline = [
            indexed[("baseline_S0_B0", load, row["replication"])]
            for row in group
        ]
        differences = [
            float(row["throughput_per_hour"])
            - float(baseline_row["throughput_per_hour"])
            for row, baseline_row in zip(group, baseline, strict=True)
        ]
        difference_mean = mean(differences)
        difference_sd = stdev(differences) if len(differences) > 1 else 0.0
        critical = (
            float(stats.t.ppf(0.975, len(differences) - 1))
            if len(differences) > 1
            else 0.0
        )
        half_width = critical * difference_sd / math.sqrt(len(differences))
        baseline_throughput = mean(
            float(row["throughput_per_hour"]) for row in baseline
        )
        result["throughput_relative_lower_bound"] = (
            (difference_mean - half_width) / baseline_throughput
            if baseline_throughput
            else 0.0
        )
        baseline_wait = mean(float(row["mean_wait_seconds"]) for row in baseline)
        wait_limit = (
            baseline_wait * float(constraints["mean_wait_multiplier"])
            + float(constraints["mean_wait_additive_seconds"])
        )
        result["mean_wait_limit_seconds"] = wait_limit
        result["load_feasible"] = (
            "yes"
            if float(result["throughput_relative_lower_bound"])
            >= -float(constraints["throughput_relative_margin"])
            and float(result["mean_wait_seconds"]) <= wait_limit
            and float(result["density_limit_exceedance_fraction"])
            <= float(constraints["maximum_density_exceedance_fraction"])
            else "no"
        )
        aggregate_rows.append(result)
    _write(root / "design_load_aggregates.csv", aggregate_rows)

    by_design: dict[str, list[dict[str, float | int | str]]] = defaultdict(list)
    for row in aggregate_rows:
        by_design[str(row["design_id"])].append(row)
    design_rows: list[dict[str, float | int | str]] = []
    for design_id, group in sorted(by_design.items()):
        first = group[0]
        result = {
            key: first[key]
            for key in (
                "design_id",
                "policy",
                "layout",
                "row_angle_degrees",
                "batch_size",
                "sub_batch_size",
                "downstream_threshold",
                "barrier_footprint_m2",
                "release_staff_count",
                "gate_delay_seconds",
            )
        }
        for metric in metrics:
            result[metric] = mean(float(row[metric]) for row in group)
        result["minimum_throughput_relative_lower_bound"] = min(
            float(row["throughput_relative_lower_bound"]) for row in group
        )
        result["feasible"] = (
            "yes" if all(row["load_feasible"] == "yes" for row in group) else "no"
        )
        design_rows.append(result)

    feasible = [row for row in design_rows if row["feasible"] == "yes"]
    for row in design_rows:
        row["pareto_efficient"] = (
            "yes"
            if row in feasible
            and not any(
                candidate is not row
                and _dominates(candidate, row, minimize, maximize)
                for candidate in feasible
            )
            else "no"
        )
    _write(root / "design_summary.csv", design_rows)
    pareto = [row for row in design_rows if row["pareto_efficient"] == "yes"]
    pareto.sort(
        key=lambda row: (
            int(row["release_staff_count"]),
            float(row["mean_wait_seconds"]),
            -float(row["throughput_per_hour"]),
        )
    )
    _write(root / "pareto_front.csv", pareto)

    lines = [
        "# Phase 7 multi-objective Pareto optimization",
        "",
        (
            f"The grid contains {len(design_rows)} designs; {len(feasible)} satisfy the "
            f"prespecified operational constraints and {len(pareto)} are nondominated."
        ),
        (
            "No weighted composite determines the result. Pareto status jointly considers "
            "movement starts, stops, turning, distance, waiting, required area, and throughput. "
            "Staffing is retained as a design descriptor but excluded because it does not alter "
            "simulator dynamics."
        ),
        "",
        "| Design | Policy/layout | Angle | Staff | Starts | Wait (s) | Area (m2) | Throughput/h |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in pareto[:30]:
        lines.append(
            f"| {row['design_id']} | {row['policy']}/{row['layout']} | "
            f"{float(row['row_angle_degrees']):.0f} | "
            f"{int(row['release_staff_count'])} | "
            f"{float(row['mean_movement_starts']):.3f} | "
            f"{float(row['mean_wait_seconds']):.1f} | "
            f"{float(row['required_waiting_area_m2_at_density_limit']):.1f} | "
            f"{float(row['throughput_per_hour']):.1f} |"
        )
    lines.extend(
        [
            "",
            (
                "The grid is an engineering design search, not proof of global optimality. "
                "Phase 8 maps failure regions beyond the feasible grid."
            ),
            "",
        ]
    )
    Path("PHASE_07_OPTIMIZATION_REPORT.md").write_text(
        "\n".join(lines),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
