from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from collections.abc import Sequence
from pathlib import Path
from statistics import mean


def _metric(rows: Sequence[dict[str, str]], name: str) -> float:
    return mean(float(row[name]) for row in rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the Phase 3 geometry report")
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("results/phase3_space_guidance/layout_angle_screen.csv"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("PHASE_03_SPACE_GUIDANCE_REPORT.md"),
    )
    args = parser.parse_args()

    with args.input.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    base_rows = [row for row in rows if row["footprint_case"] == "base"]
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in base_rows:
        grouped[(row["layout"], row["row_angle_degrees"])].append(row)

    lines = [
        "# Phase 3 space, guidance, movement, and capacity report",
        "",
        (
            f"The implementation screen contains {len(rows)} runs. It is an engineering "
            "sensitivity screen, not a calibrated-airport comparison or an inferential final run."
        ),
        "",
        "## Base-footprint implementation screen",
        "",
        (
            "| Layout | Angle | Throughput/h | Distance m | Starts | Turning deg | "
            "Capacity pax/m² | Required area m² | Conflict proxy |"
        ),
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for (layout, angle), group in sorted(
        grouped.items(),
        key=lambda item: (item[0][0], float(item[0][1])),
    ):
        lines.append(
            f"| {layout} | {float(angle):.0f} | "
            f"{_metric(group, 'throughput_per_hour'):.2f} | "
            f"{_metric(group, 'mean_movement_distance_m'):.2f} | "
            f"{_metric(group, 'mean_movement_starts'):.2f} | "
            f"{_metric(group, 'mean_turning_angle_degrees'):.2f} | "
            f"{_metric(group, 'capacity_efficiency_passengers_per_m2'):.3f} | "
            f"{_metric(group, 'required_waiting_area_m2_at_density_limit'):.2f} | "
            f"{_metric(group, 'mean_movement_conflict_proxy'):.3f} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation limits",
            "",
            "- B0--B4 are generic parameterized layouts, not representations of a named airport.",
            (
                "- Footprints, barrier areas, gate delays, staffing, and clearance values are "
                "explicit engineering sensitivity inputs recorded in the configuration and "
                "parameter ledger."
            ),
            "- The conflict index is a geometric release-surge proxy, not a validated safety outcome.",
            (
                "- Capacity efficiency is conditional on the configured density, footprint, "
                "accessible route, turning-space, corridor, and barrier assumptions."
            ),
            (
                "- The primary movement endpoints remain separate; no weighted composite determines "
                "the comparison."
            ),
            "",
        ]
    )
    args.output.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
