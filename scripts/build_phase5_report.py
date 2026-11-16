from __future__ import annotations

import csv
from pathlib import Path


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _format(value: str) -> str:
    return f"{float(value):.3f}"


def main() -> None:
    root = Path("results/phase5")
    primary = _rows(root / "primary_results.csv")
    precision = _rows(root / "monte_carlo_precision.csv")
    replications = int(float(primary[0]["replications"]))
    precision_status = (
        (
            "The design reached the prespecified routine cap of 200 paired replications per "
            "load-policy cell."
        )
        if replications >= 200
        else (
            f"The initial design contains {replications} paired replications per load-policy "
            "cell. At least one target requires escalation under the locked rule."
        )
    )
    primary_precision = {
        (row["load_regime"], row["endpoint"]): row
        for row in precision
        if row["policy"] == "S3"
        and row["load_regime"] in {"0.85", "0.95"}
        and row["endpoint"]
        in {
            "throughput_per_hour",
            "mean_movement_starts",
            "mean_movement_stops",
            "mean_turning_angle_degrees",
            "mean_movement_distance_m",
            "capacity_efficiency_passengers_per_m2",
            "required_waiting_area_m2_at_density_limit",
        }
    }
    lines = [
        "# Phase 5 comparative-design and Monte Carlo precision report",
        "",
        (
            "This report is generated from the locked-plan replication outputs. It is not a "
            "manually edited result source."
        ),
        "",
        "## Locked primary comparison",
        "",
        "| Load | Endpoint | S0 mean | S3-S0 | 95% CI | Throughput acceptable |",
        "|---:|---|---:|---:|---:|:---:|",
    ]
    for row in primary:
        lines.append(
            f"| {float(row['load_regime']):.2f} | {row['endpoint']} | "
            f"{_format(row['baseline_mean'])} | {_format(row['mean_paired_difference'])} | "
            f"[{_format(row['ci95_lower'])}, {_format(row['ci95_upper'])}] | "
            f"{row['throughput_acceptable']} |"
        )
    lines.extend(
        [
            "",
            "## Precision decision",
            "",
            precision_status,
            "Current precision results are:",
            "",
            "| Load | Endpoint | Achieved half-width | Target | Estimated replications | Met |",
            "|---:|---|---:|---:|---:|:---:|",
        ]
    )
    for load, endpoint in sorted(primary_precision):
        row = primary_precision[(load, endpoint)]
        lines.append(
            f"| {float(load):.2f} | {endpoint} | "
            f"{_format(row['achieved_half_width'])} | "
            f"{_format(row['target_half_width'])} | "
            f"{int(float(row['estimated_required_replications']))} | "
            f"{row['target_met']} |"
        )
    lines.extend(
        [
            "",
            (
                "Unmet precision targets are retained as limitations rather than silently "
                "relaxed. Phase 6 validation must assess whether large between-replication "
                "variability reflects load sensitivity, the S0 stop-go abstraction, or both."
            ),
            "",
        ]
    )
    Path("PHASE_05_PRECISION_REPORT.md").write_text(
        "\n".join(lines),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
