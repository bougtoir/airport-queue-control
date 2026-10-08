from __future__ import annotations

import csv
import math
from collections import defaultdict
from pathlib import Path
from statistics import mean, stdev

import yaml
from scipy import stats


def _mapping(value: object, name: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise TypeError(f"{name} must be a mapping")
    return {str(key): item for key, item in value.items()}


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
    standard_deviation = stdev(differences) if len(differences) > 1 else 0.0
    critical = (
        float(stats.t.ppf(0.975, len(differences) - 1))
        if len(differences) > 1
        else 0.0
    )
    half_width = critical * standard_deviation / math.sqrt(len(differences))
    return estimate, estimate - half_width, estimate + half_width


def main() -> None:
    root = Path("results/phase8")
    rows = _read(root / "replications.csv")
    specification = _mapping(
        yaml.safe_load(
            Path("configs/phase8_falsification.yaml").read_text(encoding="utf-8")
        ),
        "falsification specification",
    )
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[(row["scenario_id"], row["policy"])].append(row)
    comparison_rows: list[dict[str, float | int | str]] = []
    for scenario_id in sorted({row["scenario_id"] for row in rows}):
        baseline = sorted(
            grouped[(scenario_id, "S0")],
            key=lambda row: int(row["replication"]),
        )
        intervention = sorted(
            grouped[(scenario_id, "S3")],
            key=lambda row: int(row["replication"]),
        )
        throughput = _paired(baseline, intervention, "throughput_per_hour")
        starts = _paired(baseline, intervention, "mean_movement_starts")
        stops = _paired(baseline, intervention, "mean_movement_stops")
        wait = _paired(baseline, intervention, "mean_wait_seconds")
        area = _paired(
            baseline,
            intervention,
            "required_waiting_area_m2_at_density_limit",
        )
        unfinished = _paired(baseline, intervention, "unfinished")
        surge = _paired(
            baseline,
            intervention,
            "maximum_release_surge_index",
        )
        conflict = _paired(
            baseline,
            intervention,
            "mean_movement_conflict_proxy",
        )
        baseline_throughput = mean(
            float(row["throughput_per_hour"]) for row in baseline
        )
        baseline_area = mean(
            float(row["required_waiting_area_m2_at_density_limit"])
            for row in baseline
        )
        intervention_area = mean(
            float(row["required_waiting_area_m2_at_density_limit"])
            for row in intervention
        )
        relative_lower = (
            throughput[1] / baseline_throughput if baseline_throughput else 0.0
        )
        throughput_failure = relative_lower < -float(
            specification["throughput_relative_margin"]
        )
        movement_null = starts[0] > -float(
            specification["movement_start_minimum_benefit"]
        )
        wait_failure = wait[0] > float(
            specification["maximum_mean_wait_increase_seconds"]
        )
        area_ratio = (
            intervention_area / baseline_area if baseline_area > 0 else 1.0
        )
        area_failure = area_ratio > float(
            specification["maximum_required_area_ratio"]
        )
        unfinished_failure = unfinished[0] > float(
            specification["maximum_unfinished_increase"]
        )
        baseline_surge = mean(
            float(row["maximum_release_surge_index"]) for row in baseline
        )
        intervention_surge = mean(
            float(row["maximum_release_surge_index"]) for row in intervention
        )
        surge_ratio = (
            intervention_surge / baseline_surge if baseline_surge > 0 else 1.0
        )
        surge_failure = surge_ratio > float(
            specification["maximum_release_surge_ratio"]
        )
        baseline_conflict = mean(
            float(row["mean_movement_conflict_proxy"]) for row in baseline
        )
        intervention_conflict = mean(
            float(row["mean_movement_conflict_proxy"]) for row in intervention
        )
        conflict_ratio = (
            intervention_conflict / baseline_conflict
            if baseline_conflict > 0
            else 1.0
        )
        conflict_failure = conflict_ratio > float(
            specification["maximum_conflict_proxy_ratio"]
        )
        staffing_failure = (
            mean(float(row["release_staff_count"]) for row in intervention) < 1.0
        )
        failure_labels = [
            label
            for label, failed in (
                ("throughput", throughput_failure),
                ("movement_null", movement_null),
                ("waiting", wait_failure),
                ("space", area_failure),
                ("unfinished", unfinished_failure),
                ("release_surge_proxy", surge_failure),
                ("conflict_proxy", conflict_failure),
                ("staffing", staffing_failure),
            )
            if failed
        ]
        first = baseline[0]
        comparison_rows.append(
            {
                "scenario_id": scenario_id,
                "category": first["category"],
                "load_regime": first["load_regime"],
                "replications": len(baseline),
                "baseline_mean_throughput_per_hour": baseline_throughput,
                "throughput_difference": throughput[0],
                "throughput_ci95_lower": throughput[1],
                "throughput_ci95_upper": throughput[2],
                "throughput_relative_lower_bound": relative_lower,
                "movement_starts_difference": starts[0],
                "movement_starts_ci95_lower": starts[1],
                "movement_starts_ci95_upper": starts[2],
                "movement_stops_difference": stops[0],
                "mean_wait_difference_seconds": wait[0],
                "required_area_difference_m2": area[0],
                "required_area_ratio": area_ratio,
                "unfinished_difference": unfinished[0],
                "release_surge_difference": surge[0],
                "release_surge_ratio": surge_ratio,
                "conflict_proxy_difference": conflict[0],
                "conflict_proxy_ratio": conflict_ratio,
                "throughput_failure": "yes" if throughput_failure else "no",
                "movement_null": "yes" if movement_null else "no",
                "waiting_failure": "yes" if wait_failure else "no",
                "space_failure": "yes" if area_failure else "no",
                "unfinished_failure": "yes" if unfinished_failure else "no",
                "release_surge_failure": "yes" if surge_failure else "no",
                "conflict_proxy_failure": "yes" if conflict_failure else "no",
                "staffing_failure": "yes" if staffing_failure else "no",
                "failure_labels": ";".join(failure_labels) or "none",
                "failure_detected": "yes" if failure_labels else "no",
            }
        )
    _write(root / "scenario_comparisons.csv", comparison_rows)
    _write(Path("ROBUSTNESS_MAP.csv"), comparison_rows)
    failures = [
        row for row in comparison_rows if row["failure_detected"] == "yes"
    ]
    _write(root / "failure_regions.csv", failures)
    proxy_threshold_rows: list[dict[str, float | int]] = []
    for threshold in (1.25, 1.5, 2.0, 3.0, 4.0):
        proxy_threshold_rows.append(
            {
                "ratio_threshold": threshold,
                "release_surge_scenarios": sum(
                    float(row["release_surge_ratio"]) > threshold
                    for row in comparison_rows
                ),
                "conflict_proxy_scenarios": sum(
                    float(row["conflict_proxy_ratio"]) > threshold
                    for row in comparison_rows
                ),
            }
        )
    _write(root / "proxy_threshold_sensitivity.csv", proxy_threshold_rows)
    failure_counts = {
        label: sum(row[key] == "yes" for row in comparison_rows)
        for label, key in (
            ("throughput", "throughput_failure"),
            ("movement null", "movement_null"),
            ("waiting", "waiting_failure"),
            ("space", "space_failure"),
            ("unfinished demand", "unfinished_failure"),
            ("release-surge proxy", "release_surge_failure"),
            ("conflict proxy", "conflict_proxy_failure"),
            ("staffing", "staffing_failure"),
        )
    }

    lines = [
        "# Phase 8 active falsification and failure-region map",
        "",
        (
            f"{len(comparison_rows)} prespecified stress scenarios were tested with paired "
            f"S3-versus-S0 replications. {len(failures)} meet at least one failure criterion."
        ),
        "",
        "Criterion counts: "
        + "; ".join(f"{label}={count}" for label, count in failure_counts.items())
        + ".",
        "",
        (
            "Release-surge and conflict criteria are prespecified engineering-proxy ratio "
            "screens, not empirical safety thresholds or evidence of injury risk."
        ),
        "",
        "| Proxy ratio threshold | Release-surge flags | Conflict-proxy flags |",
        "|---:|---:|---:|",
    ]
    for row in proxy_threshold_rows:
        lines.append(
            f"| {float(row['ratio_threshold']):.2f} | "
            f"{int(row['release_surge_scenarios'])} | "
            f"{int(row['conflict_proxy_scenarios'])} |"
        )
    lines.extend(
        [
            "",
            (
                "Flag counts vary with the arbitrary screening ratio; operational throughput, "
                "waiting, area, and unfinished-demand criteria do not use these proxy thresholds."
            ),
            "",
        "| Scenario | Category | Load | Failure labels | Throughput lower bound | Starts diff | Wait diff (s) |",
        "|---|---|---:|---|---:|---:|---:|",
        ]
    )
    for row in failures:
        lines.append(
            f"| {row['scenario_id']} | {row['category']} | "
            f"{float(row['load_regime']):.2f} | {row['failure_labels']} | "
            f"{float(row['throughput_relative_lower_bound']):.3f} | "
            f"{float(row['movement_starts_difference']):.3f} | "
            f"{float(row['mean_wait_difference_seconds']):.1f} |"
        )
    lines.extend(
        [
            "",
            "## Structural limitation exposed by falsification",
            "",
            (
                "Distance and turning advantages are encoded by the B0/B1 route definitions, so "
                "this simulator cannot falsify those two endpoints without changing the geometry "
                "model. The campaign can erase the stop-go benefit or expose operational "
                "trade-offs, but it cannot independently validate a route advantage that is an "
                "input assumption. The staffing screen also exposes that staffing is tracked but "
                "does not currently alter simulated release performance."
            ),
            "",
        ]
    )
    Path("PHASE_08_FALSIFICATION_REPORT.md").write_text(
        "\n".join(lines),
        encoding="utf-8",
    )
    Path("FAILURE_MODES.md").write_text(
        "\n".join(lines),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
