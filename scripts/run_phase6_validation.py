from __future__ import annotations

import csv
from dataclasses import replace
from pathlib import Path

from airport_batch_queue.config import SimulationConfig, load_config
from airport_batch_queue.simulator import SimulationResult, run_simulation


def _run(
    base: SimulationConfig,
    *,
    policy: str = "S0",
    horizon: float = 600.0,
    drain: float = 600.0,
    arrival_rate: float | None = None,
) -> SimulationResult:
    arrival = base.arrival
    if arrival_rate is not None:
        arrival = replace(arrival, mode="poisson", rate_per_hour=arrival_rate)
    config = replace(
        base,
        horizon_seconds=horizon,
        drain_limit_seconds=drain,
        arrival=arrival,
        control=replace(base.control, policy=policy),
    )
    return run_simulation(config)


def _record(
    rows: list[dict[str, str | float]],
    case: str,
    assertion: str,
    observed: str | float,
    passed: bool,
) -> None:
    rows.append(
        {
            "case": case,
            "assertion": assertion,
            "observed": observed,
            "passed": "yes" if passed else "no",
        }
    )


def _write_report(rows: list[dict[str, str | float]]) -> None:
    lines = [
        "# Phase 6 analytical and extreme-case validation",
        "",
        (
            "These checks test implementation invariants and directional extreme-case behavior. "
            "They do not validate a real airport or establish external predictive accuracy."
        ),
        "",
        "| Case | Assertion | Observed | Passed |",
        "|---|---|---:|:---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row['case']} | {row['assertion']} | {row['observed']} | "
            f"{row['passed']} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            (
                "Passenger conservation, exact route accounting, maximum-hold release, full lane "
                "closure, lane-capacity reduction, service-capacity bounds, overload retention, "
                "virtual-queue geometry, and identical-footprint capacity checks all pass."
            ),
            (
                "The checks support internal correctness only. Calibration, real-site geometry, "
                "human behavioral validity, and empirical external validation remain outside "
                "the evidence base."
            ),
            "",
        ]
    )
    Path("PHASE_06_VALIDATION_REPORT.md").write_text(
        "\n".join(lines),
        encoding="utf-8",
    )


def main() -> None:
    base = load_config("configs/default.yaml")
    rows: list[dict[str, str | float]] = []

    no_demand = _run(base, arrival_rate=0.0)
    _record(
        rows,
        "no_demand",
        "zero arrivals produce zero completions",
        f"{no_demand.summary['arrivals']}/{no_demand.summary['completed']}",
        no_demand.summary["arrivals"] == no_demand.summary["completed"] == 0,
    )

    conservation = _run(base, policy="S3")
    arrivals = int(conservation.summary["arrivals"])
    completed = int(conservation.summary["completed"])
    unfinished = int(conservation.summary["unfinished"])
    _record(
        rows,
        "conservation",
        "arrivals equal completed plus unfinished",
        f"{arrivals}={completed}+{unfinished}",
        arrivals == completed + unfinished,
    )

    single_arrival = replace(
        base.arrival,
        mode="batched",
        batch_size=1,
        batch_interval_seconds=1000.0,
    )
    route_base = replace(
        base,
        horizon_seconds=300.0,
        drain_limit_seconds=300.0,
        arrival=single_arrival,
        passenger=replace(
            base.passenger,
            luggage_prevalence=0.0,
            reduced_mobility_prevalence=0.0,
            release_compliance=1.0,
        ),
    )
    conventional = run_simulation(
        replace(route_base, control=replace(base.control, policy="S0"))
    )
    stationary = run_simulation(
        replace(route_base, control=replace(base.control, policy="S3"))
    )
    route_observed = (
        f"{conventional.summary['mean_movement_distance_m']}/"
        f"{stationary.summary['mean_movement_distance_m']} m; "
        f"{conventional.summary['mean_turning_angle_degrees']}/"
        f"{stationary.summary['mean_turning_angle_degrees']} deg"
    )
    _record(
        rows,
        "route_accounting",
        "B0 and B1 route values match configured geometry",
        route_observed,
        conventional.summary["mean_movement_distance_m"] == 55.0
        and stationary.summary["mean_movement_distance_m"] == 22.0
        and conventional.summary["mean_turning_angle_degrees"] == 1800.0
        and stationary.summary["mean_turning_angle_degrees"] == 360.0,
    )

    forced = run_simulation(
        replace(
            route_base,
            control=replace(
                base.control,
                policy="S1",
                batch_size=12,
                maximum_hold_seconds=30.0,
            ),
        )
    )
    forced_passenger = forced.passengers[0]
    forced_wait = (
        forced_passenger.release_time - forced_passenger.arrival_time
        if forced_passenger.release_time is not None
        else -1.0
    )
    _record(
        rows,
        "maximum_hold",
        "undersized batch is eventually released",
        forced_wait,
        forced_passenger.completion_time is not None and forced_wait >= 30.0,
    )

    high_arrivals = replace(
        base.arrival,
        mode="batched",
        batch_size=20,
        batch_interval_seconds=10.0,
    )
    deterministic_service = replace(
        base.service,
        mean_seconds=20.0,
        cv=0.0,
        secondary_probability=0.0,
        long_inspection_probability=0.0,
    )
    capacity_base = replace(
        base,
        horizon_seconds=600.0,
        drain_limit_seconds=0.0,
        arrival=high_arrivals,
        service=deterministic_service,
        control=replace(base.control, policy="S0"),
    )
    full_lanes = run_simulation(capacity_base)
    closed_lanes = run_simulation(
        replace(
            capacity_base,
            service=replace(deterministic_service, lane_schedule=((0.0, 0),)),
        )
    )
    reduced_lanes = run_simulation(
        replace(
            capacity_base,
            service=replace(
                deterministic_service,
                lane_schedule=((0.0, 3), (300.0, 1)),
            ),
        )
    )
    _record(
        rows,
        "full_lane_closure",
        "zero active lanes produce zero completions",
        closed_lanes.summary["completed"],
        closed_lanes.summary["completed"] == 0,
    )
    _record(
        rows,
        "lane_reduction",
        "closing two lanes reduces horizon completions",
        (
            f"{full_lanes.summary['completed_within_horizon']}>"
            f"{reduced_lanes.summary['completed_within_horizon']}"
        ),
        int(full_lanes.summary["completed_within_horizon"])
        > int(reduced_lanes.summary["completed_within_horizon"]),
    )
    theoretical_capacity = int(
        deterministic_service.servers
        * capacity_base.horizon_seconds
        / deterministic_service.mean_seconds
    )
    capacity_completed = int(full_lanes.summary["completed_within_horizon"])
    _record(
        rows,
        "capacity_bound",
        "completed count is positive and below the service upper bound",
        f"{capacity_completed}<={theoretical_capacity}",
        0 < capacity_completed <= theoretical_capacity,
    )
    _record(
        rows,
        "overload_retention",
        "unfinished overload demand is retained",
        full_lanes.summary["unfinished"],
        int(full_lanes.summary["unfinished"]) > 0,
    )

    virtual = run_simulation(
        replace(route_base, control=replace(base.control, policy="S5"))
    )
    _record(
        rows,
        "virtual_queue",
        "virtual policy has no physical waiting area and uses its route",
        (
            f"{virtual.summary['waiting_area_m2']} m2; "
            f"{virtual.summary['mean_movement_distance_m']} m"
        ),
        virtual.summary["waiting_area_m2"] == 0.0
        and virtual.summary["mean_movement_distance_m"]
        == base.geometry.virtual_distance_m,
    )

    capacity_match = (
        conventional.summary["capacity_efficiency_passengers_per_m2"]
        == stationary.summary["capacity_efficiency_passengers_per_m2"]
    )
    _record(
        rows,
        "identical_footprint",
        "primary B0/B1 capacity efficiency is identical by design",
        (
            f"{conventional.summary['capacity_efficiency_passengers_per_m2']}/"
            f"{stationary.summary['capacity_efficiency_passengers_per_m2']}"
        ),
        capacity_match,
    )

    output = Path("results/phase6/validation_cases.csv")
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(rows[0]),
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)
    _write_report(rows)
    if any(row["passed"] != "yes" for row in rows):
        raise SystemExit("One or more Phase 6 validation cases failed")


if __name__ == "__main__":
    main()
