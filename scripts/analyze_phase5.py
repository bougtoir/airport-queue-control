from __future__ import annotations

import csv
import math
from collections import defaultdict
from pathlib import Path

import numpy as np
import yaml
from scipy import stats


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_rows(path: Path, rows: list[dict[str, float | int | str]]) -> None:
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


def main() -> None:
    input_path = Path("results/phase5/replications.csv")
    output_root = Path("results/phase5")
    with Path("ANALYSIS_PLAN_LOCKED.yaml").open(encoding="utf-8") as handle:
        loaded: object = yaml.safe_load(handle)
    plan = _mapping(loaded, "plan")
    precision = _mapping(plan["monte_carlo_precision_targets"], "precision")
    margin_value = _mapping(plan["primary_comparison"], "primary")[
        "throughput_relative_noninferiority_margin"
    ]
    if not isinstance(margin_value, (int, float)):
        raise TypeError("throughput margin must be numeric")
    throughput_margin = float(margin_value)
    sensitivity_values = _mapping(plan["primary_comparison"], "primary")[
        "throughput_margin_sensitivity"
    ]
    if not isinstance(sensitivity_values, list) or not all(
        isinstance(value, (int, float)) for value in sensitivity_values
    ):
        raise TypeError("throughput margin sensitivities must be numeric")
    sensitivity_margins = [float(value) for value in sensitivity_values]

    rows = _read_rows(input_path)
    indexed: dict[tuple[float, int, str], dict[str, str]] = {}
    for row in rows:
        indexed[(float(row["load_regime"]), int(row["replication"]), row["policy"])] = row

    endpoints = [
        "throughput_per_hour",
        "mean_movement_starts",
        "mean_movement_stops",
        "mean_turning_angle_degrees",
        "mean_movement_distance_m",
        "mean_movement_time_seconds",
        "mean_wait_seconds",
        "utilization",
        "starvation_fraction_with_upstream_demand",
        "capacity_efficiency_passengers_per_m2",
        "required_waiting_area_m2_at_density_limit",
    ]
    grouped: dict[tuple[float, str, str], list[float]] = defaultdict(list)
    baseline_values: dict[tuple[float, str], list[float]] = defaultdict(list)
    for (load, replication, policy), row in indexed.items():
        if policy == "S0":
            for endpoint in endpoints:
                baseline_values[(load, endpoint)].append(float(row[endpoint]))
            continue
        baseline = indexed[(load, replication, "S0")]
        for endpoint in endpoints:
            grouped[(load, policy, endpoint)].append(
                float(row[endpoint]) - float(baseline[endpoint])
            )

    comparison_rows: list[dict[str, float | int | str]] = []
    precision_rows: list[dict[str, float | int | str]] = []
    for (load, policy, endpoint), differences in sorted(grouped.items()):
        array = np.asarray(differences)
        count = len(array)
        mean = float(array.mean())
        standard_deviation = float(array.std(ddof=1)) if count > 1 else 0.0
        critical = float(stats.t.ppf(0.975, count - 1)) if count > 1 else 0.0
        half_width = critical * standard_deviation / math.sqrt(count) if count > 1 else 0.0
        baseline_mean = float(np.mean(baseline_values[(load, endpoint)]))
        relative_lower = (
            (mean - half_width) / baseline_mean if baseline_mean != 0 else float("nan")
        )
        result: dict[str, float | int | str] = {
            "load_regime": load,
            "policy": policy,
            "baseline": "S0",
            "endpoint": endpoint,
            "replications": count,
            "baseline_mean": baseline_mean,
            "mean_paired_difference": mean,
            "standard_deviation_paired_difference": standard_deviation,
            "ci95_lower": mean - half_width,
            "ci95_upper": mean + half_width,
            "ci95_half_width": half_width,
            "relative_lower_bound": relative_lower,
            "throughput_acceptable": (
                "yes"
                if endpoint == "throughput_per_hour"
                and relative_lower >= -throughput_margin
                else "no"
                if endpoint == "throughput_per_hour"
                else "not_applicable"
            ),
        }
        for sensitivity_margin in sensitivity_margins:
            label = f"{round(sensitivity_margin * 100):d}pct"
            result[f"throughput_acceptable_margin_{label}"] = (
                "yes"
                if endpoint == "throughput_per_hour"
                and relative_lower >= -sensitivity_margin
                else "no"
                if endpoint == "throughput_per_hour"
                else "not_applicable"
            )
        comparison_rows.append(result)

        if endpoint == "throughput_per_hour":
            target = float(
                precision["throughput_difference_half_width_relative_to_baseline"]
            ) * baseline_mean
        elif endpoint == "mean_movement_starts":
            target = float(precision["movement_starts_difference_half_width"])
        elif endpoint == "mean_movement_stops":
            target = float(precision["movement_stops_difference_half_width"])
        elif endpoint == "mean_turning_angle_degrees":
            target = float(precision["turning_angle_difference_half_width_degrees"])
        elif endpoint == "mean_movement_distance_m":
            target = float(precision["movement_distance_difference_half_width_m"])
        elif endpoint == "capacity_efficiency_passengers_per_m2":
            target = float(
                precision["capacity_efficiency_difference_half_width_per_m2"]
            )
        elif endpoint == "required_waiting_area_m2_at_density_limit":
            target = float(precision["required_area_difference_half_width_m2"])
        elif endpoint == "mean_wait_seconds":
            target = float(precision["mean_wait_difference_half_width_seconds"])
        else:
            continue
        required = (
            math.ceil((1.96 * standard_deviation / target) ** 2)
            if target > 0 and standard_deviation > 0
            else 1
        )
        precision_rows.append(
            {
                "load_regime": load,
                "policy": policy,
                "endpoint": endpoint,
                "current_replications": count,
                "target_half_width": target,
                "achieved_half_width": half_width,
                "estimated_required_replications": required,
                "target_met": "yes" if half_width <= target else "no",
            }
        )

    _write_rows(output_root / "paired_comparisons.csv", comparison_rows)
    _write_rows(output_root / "monte_carlo_precision.csv", precision_rows)
    primary = _mapping(plan["primary_comparison"], "primary comparison")
    primary_loads_value = primary["load_regimes"]
    movement_endpoints_value = primary["movement_endpoints"]
    spatial_endpoints_value = primary["spatial_endpoints"]
    operational_endpoint_value = primary["operational_endpoint"]
    intervention_value = primary["intervention"]
    if (
        not isinstance(primary_loads_value, list)
        or not all(isinstance(value, (int, float)) for value in primary_loads_value)
        or not isinstance(movement_endpoints_value, list)
        or not all(isinstance(value, str) for value in movement_endpoints_value)
        or not isinstance(spatial_endpoints_value, list)
        or not all(isinstance(value, str) for value in spatial_endpoints_value)
        or not isinstance(operational_endpoint_value, str)
        or not isinstance(intervention_value, str)
    ):
        raise TypeError("Primary comparison fields have invalid types")
    primary_loads = {float(value) for value in primary_loads_value}
    primary_endpoints = {
        *movement_endpoints_value,
        *spatial_endpoints_value,
        operational_endpoint_value,
    }
    primary_rows = [
        row
        for row in comparison_rows
        if float(row["load_regime"]) in primary_loads
        and row["policy"] == intervention_value
        and row["endpoint"] in primary_endpoints
    ]
    _write_rows(output_root / "primary_results.csv", primary_rows)


if __name__ == "__main__":
    main()
