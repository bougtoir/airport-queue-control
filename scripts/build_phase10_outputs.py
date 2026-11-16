from __future__ import annotations

import csv
from dataclasses import replace
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from docx import Document
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
from pptx import Presentation
from pptx.util import Inches, Pt

from airport_batch_queue.config import load_config
from airport_batch_queue.simulator import run_simulation

COLORS = {
    "S0": "#0072B2",
    "S3": "#D55E00",
    "S5": "#009E73",
    "neutral": "#666666",
}
FIGURE_DIR = Path("figures")
TABLE_DIR = Path("tables")
DATA_DIR = Path("results/phase10")


def _prepare() -> None:
    for path in (
        FIGURE_DIR,
        TABLE_DIR,
        DATA_DIR,
    ):
        path.mkdir(parents=True, exist_ok=True)


def _save_figure(figure: plt.Figure, name: str) -> Path:
    directory = FIGURE_DIR
    png_path = directory / f"{name}.png"
    svg_path = directory / f"{name}.svg"
    pdf_path = directory / f"{name}.pdf"
    figure.savefig(png_path, dpi=300, bbox_inches="tight")
    figure.savefig(svg_path, bbox_inches="tight")
    figure.savefig(pdf_path, bbox_inches="tight")
    svg_path.write_text(
        "\n".join(line.rstrip() for line in svg_path.read_text(encoding="utf-8").splitlines())
        + "\n",
        encoding="utf-8",
    )
    plt.close(figure)
    return png_path


def _concept_figure() -> tuple[Path, str]:
    figure, axes = plt.subplots(1, 3, figsize=(12, 3.5))
    titles = ["S0: serpentine", "S3: stationary rows", "Threshold release"]
    for axis, title in zip(axes, titles, strict=True):
        axis.set_title(title, fontweight="bold")
        axis.set_xlim(0, 10)
        axis.set_ylim(0, 7)
        axis.axis("off")
    axes[0].plot([1, 9, 1, 9, 1, 9], [1, 1, 2, 3, 4, 5], color=COLORS["S0"], lw=3)
    for x, y in zip([2, 4, 6, 8], [1, 2, 3, 4], strict=True):
        axes[0].add_patch(plt.Circle((x, y), 0.15, color=COLORS["S0"]))
    for y in (1.5, 3, 4.5):
        axes[1].plot([1, 8], [y, y], color=COLORS["neutral"], lw=2)
        for x in np.linspace(2, 7, 4):
            axes[1].add_patch(plt.Circle((x, y), 0.15, color=COLORS["S3"]))
    axes[1].add_patch(
        FancyArrowPatch((8, 3), (9.5, 3), arrowstyle="->", mutation_scale=16)
    )
    for index, label in enumerate(("Wait", "Sense", "Release", "Screen")):
        x = 0.4 + index * 2.4
        axes[2].add_patch(
            FancyBboxPatch(
                (x, 2.6),
                1.8,
                1.2,
                boxstyle="round,pad=0.1",
                facecolor="#E6E6E6",
                edgecolor=COLORS["neutral"],
            )
        )
        axes[2].text(x + 0.9, 3.2, label, ha="center", va="center")
        if index < 3:
            axes[2].add_patch(
                FancyArrowPatch(
                    (x + 1.8, 3.2),
                    (x + 2.35, 3.2),
                    arrowstyle="->",
                    mutation_scale=14,
                )
            )
    figure.suptitle("Separating waiting from repeated movement")
    caption = "Conceptual control architecture; diagrams are generic and not site layouts."
    return _save_figure(figure, "figure_01_concept_architecture"), caption


def _trajectory_figure() -> tuple[Path, str]:
    base = load_config("configs/default.yaml")
    results = {}
    for policy, layout in (("S0", "B0"), ("S3", "B1")):
        config = replace(
            base,
            horizon_seconds=3600,
            drain_limit_seconds=3600,
            control=replace(base.control, policy=policy),
            geometry=replace(base.geometry, layout=layout),
        )
        results[policy] = run_simulation(config)
    figure, axes = plt.subplots(1, 2, figsize=(11, 4))
    for policy in ("S0", "S3"):
        trajectory = pd.DataFrame(results[policy].trajectories)
        axes[0].plot(
            trajectory["time_seconds"] / 60,
            trajectory["upstream_waiting"],
            label=policy,
            color=COLORS[policy],
        )
    axes[0].set(
        xlabel="Time (min)",
        ylabel="Upstream waiting passengers",
        title="Representative queue trajectories",
    )
    axes[0].legend(frameon=False)
    metrics = ["Movement starts", "Movement stops", "Distance (m)", "Turning / 100°"]
    values = {}
    for policy in ("S0", "S3"):
        summary = results[policy].summary
        values[policy] = [
            float(summary["mean_movement_starts"]),
            float(summary["mean_movement_stops"]),
            float(summary["mean_movement_distance_m"]),
            float(summary["mean_turning_angle_degrees"]) / 100,
        ]
    x = np.arange(len(metrics))
    axes[1].bar(x - 0.18, values["S0"], 0.36, label="S0", color=COLORS["S0"])
    axes[1].bar(x + 0.18, values["S3"], 0.36, label="S3", color=COLORS["S3"])
    axes[1].set_xticks(x, metrics, rotation=20, ha="right")
    axes[1].set_title("Movement-event decomposition")
    axes[1].legend(frameon=False)
    figure.tight_layout()
    caption = "One common-seed realization; movement endpoints are modeled locomotion metrics."
    return _save_figure(figure, "figure_02_trajectories_events"), caption


def _movement_load_figures() -> tuple[Path, str]:
    data = pd.read_csv("results/phase5/replications.csv")
    data = data[data["policy"].isin(["S0", "S3"])]
    endpoints = [
        ("mean_movement_starts", "Movement starts"),
        ("mean_movement_stops", "Movement stops"),
        ("mean_movement_distance_m", "Distance (m)"),
        ("mean_turning_angle_degrees", "Turning (degrees)"),
    ]
    output_rows = []
    summaries: dict[str, dict[str, tuple[pd.Series, pd.Series]]] = {}
    for column, _ in endpoints:
        summaries[column] = {}
        for policy in ("S0", "S3"):
            grouped = data[data["policy"] == policy].groupby("load_regime")[column]
            means = grouped.mean()
            errors = 1.96 * grouped.sem()
            summaries[column][policy] = (means, errors)
            output_rows.extend(
                {
                    "endpoint": column,
                    "policy": policy,
                    "load_regime": load,
                    "mean": value,
                    "ci95_half_width": error,
                }
                for load, value, error in zip(
                    means.index,
                    means.values,
                    errors.values,
                    strict=True,
                )
            )
    pd.DataFrame(output_rows).to_csv(DATA_DIR / "figure_03_data.csv", index=False)

    styles = {
        "S0": {"marker": "o", "linestyle": "-"},
        "S3": {"marker": "s", "linestyle": "--"},
    }
    figure, axis = plt.subplots(figsize=(7.2, 4.4))
    for policy in ("S0", "S3"):
        means, errors = summaries["mean_movement_starts"][policy]
        axis.errorbar(
            means.index,
            means.values,
            yerr=errors.values,
            label=policy,
            color=COLORS[policy],
            linewidth=2,
            capsize=3,
            **styles[policy],
        )
    axis.set(
        xlabel="Nominal load ratio",
        ylabel="Modeled movement starts per passenger",
        title="Model-dependent movement starts across nominal load",
    )
    axis.grid(alpha=0.2)
    axis.legend(frameon=False)
    figure.tight_layout()
    main_caption = (
        "Model-dependent mean movement starts and 95% Monte Carlo intervals; "
        "S3 has one start by construction under the specified progression rule."
    )
    main_item = (
        _save_figure(figure, "figure_03_movement_by_load"),
        main_caption,
    )

    return main_item


def _control_response_figure() -> tuple[Path, str]:
    data = pd.read_csv("results/phase7/replications.csv")
    data = data[
        (data["policy"] == "S3")
        & (data["layout"] == "B1")
        & (data["row_angle_degrees"] == 0)
        & (data["load_regime"] == 0.95)
    ]
    data = data.groupby(
        ["batch_size", "downstream_threshold"],
        as_index=False,
    ).agg(
        throughput_per_hour=("throughput_per_hour", "mean"),
        utilization=("utilization", "mean"),
        starvation_fraction_with_upstream_demand=(
            "starvation_fraction_with_upstream_demand",
            "mean",
        ),
    )
    metrics = [
        ("throughput_per_hour", "Throughput (passengers/h)"),
        ("utilization", "Lane utilization"),
        (
            "starvation_fraction_with_upstream_demand",
            "Starvation fraction",
        ),
    ]
    figure, axes = plt.subplots(1, 3, figsize=(12, 3.7))
    for axis, (column, label) in zip(axes, metrics, strict=True):
        for threshold, values in data.groupby("downstream_threshold"):
            values = values.sort_values("batch_size")
            axis.plot(
                values["batch_size"],
                values[column],
                marker="o",
                label=f"Threshold {threshold}",
            )
        axis.set(xlabel="Batch size", ylabel=label)
        axis.grid(alpha=0.2)
    axes[0].legend(frameon=False, fontsize=8)
    figure.suptitle("Controller settings change operational performance")
    figure.tight_layout()
    data.to_csv(DATA_DIR / "figure_04_data.csv", index=False)
    caption = "S3/B1 designs at load 0.95; endpoints remain separate rather than weighted."
    return _save_figure(figure, "figure_04_control_response"), caption


def _space_figure() -> tuple[Path, str]:
    screen = pd.read_csv("results/phase3_space_guidance/layout_angle_screen.csv")
    data = (
        screen.groupby(["layout", "row_angle_degrees"], as_index=False)
        .agg(
            required_area=(
                "required_waiting_area_m2_at_density_limit",
                "mean",
            ),
            capacity=("acceptable_waiting_capacity", "mean"),
            distance=("mean_movement_distance_m", "mean"),
        )
    )
    footprint = (
        screen.groupby(["footprint_case", "row_angle_degrees"], as_index=False)
        .agg(
            required_area=(
                "required_waiting_area_m2_at_density_limit",
                "mean",
            ),
        )
    )
    figure, axes = plt.subplots(2, 2, figsize=(10, 7.4))
    panels = (
        (axes[0, 0], data, "layout", "required_area", "Required waiting area (m²)"),
        (axes[0, 1], data, "layout", "capacity", "Acceptable waiting capacity"),
        (
            axes[1, 0],
            footprint,
            "footprint_case",
            "required_area",
            "Required waiting area (m²)",
        ),
        (axes[1, 1], data, "layout", "distance", "Mean movement distance (m)"),
    )
    for label, (axis, values, group, column, ylabel) in zip(
        "abcd",
        panels,
        strict=True,
    ):
        for name, subset in values.groupby(group):
            subset = subset.sort_values("row_angle_degrees")
            axis.plot(
                subset["row_angle_degrees"],
                subset[column],
                marker="o",
                label=f"{name} footprint" if group == "footprint_case" else name,
            )
        axis.set(xlabel="Row angle (degrees)", ylabel=ylabel)
        axis.set_title(f"({label})", loc="left", fontsize=10)
        axis.grid(alpha=0.2)
        axis.legend(frameon=False, fontsize=7)
    figure.suptitle("Space requirements depend on geometry, footprint, and orientation")
    figure.tight_layout()
    data.merge(
        footprint.pivot_table(
            index="row_angle_degrees",
            columns="footprint_case",
            values="required_area",
        )
        .add_prefix("required_area_footprint_")
        .reset_index(),
        on="row_angle_degrees",
    ).to_csv(DATA_DIR / "figure_05_data.csv", index=False)
    caption = (
        "Phase 3 generic geometry screen averaged across seeds: (a) required waiting area and "
        "(b) acceptable waiting capacity by layout, averaged across footprint cases; (c) "
        "required waiting area by passenger-footprint case, averaged across layouts; (d) mean "
        "movement distance by layout. Overlapping lines indicate identical values (B1–B4 in b "
        "and d; base and low footprint cases in c). Accessibility minima are model "
        "constraints, not site-compliance certifications."
    )
    return _save_figure(figure, "figure_05_space_geometry"), caption


def _pareto_figure() -> tuple[Path, str]:
    all_designs = pd.read_csv("results/phase7/design_summary.csv")
    frontier = pd.read_csv("results/phase7/pareto_front.csv")
    throughput_min = float(all_designs["throughput_per_hour"].min())
    throughput_range = float(all_designs["throughput_per_hour"].max() - throughput_min)

    def marker_size(values: pd.Series) -> pd.Series:
        return 18 + 72 * (values - throughput_min) / throughput_range

    figure, axes = plt.subplots(
        1,
        2,
        figsize=(12, 5.2),
        gridspec_kw={"width_ratios": [1.35, 1]},
    )
    evaluated = axes[0].scatter(
        all_designs["mean_wait_seconds"],
        all_designs["required_waiting_area_m2_at_density_limit"],
        c=all_designs["mean_movement_starts"],
        s=marker_size(all_designs["throughput_per_hour"]),
        cmap="cividis",
        alpha=0.55,
        marker="o",
        edgecolor="#666666",
        linewidth=0.35,
        label="All evaluated designs",
    )
    axes[0].scatter(
        frontier["mean_wait_seconds"],
        frontier["required_waiting_area_m2_at_density_limit"],
        c=frontier["mean_movement_starts"],
        s=marker_size(frontier["throughput_per_hour"]) + 55,
        cmap=evaluated.cmap,
        norm=evaluated.norm,
        marker="D",
        edgecolor="black",
        linewidth=1.2,
        label="Nondominated designs",
    )
    axes[0].set(
        xlabel="Mean wait (s)",
        ylabel="Required waiting area (m²)",
        title="(a) Evaluated objective space",
    )
    axes[0].legend(frameon=False, loc="upper left")
    axes[0].grid(alpha=0.2)
    figure.colorbar(
        evaluated,
        ax=axes[0],
        label="Modeled movement starts per passenger",
    )

    objective_columns = [
        "mean_wait_seconds",
        "required_waiting_area_m2_at_density_limit",
        "mean_movement_starts",
        "throughput_per_hour",
    ]
    minima = all_designs[objective_columns].min()
    spans = all_designs[objective_columns].max() - minima
    normalized = (frontier[objective_columns] - minima) / spans
    normalized["throughput_per_hour"] = 1 - normalized["throughput_per_hour"]
    image = axes[1].imshow(
        normalized.to_numpy(),
        cmap="cividis",
        vmin=0,
        vmax=1,
        aspect="auto",
    )
    axes[1].set_xticks(
        range(len(objective_columns)),
        ["Wait", "Area", "Starts", "Throughput\nshortfall"],
    )
    axes[1].set_yticks(
        range(len(frontier)),
        [f"P{index}" for index in range(1, len(frontier) + 1)],
    )
    axes[1].set_title("(b) Nondominated objective profiles")
    actual_formats = (".0f", ".1f", ".2f", ".0f")
    for row_index, row in enumerate(
        frontier[objective_columns].itertuples(index=False, name=None)
    ):
        for column_index, (value, value_format) in enumerate(
            zip(row, actual_formats, strict=True)
        ):
            axes[1].text(
                column_index,
                row_index,
                format(value, value_format),
                ha="center",
                va="center",
                color="white" if normalized.iloc[row_index, column_index] > 0.55 else "black",
                fontsize=8,
            )
    figure.colorbar(
        image,
        ax=axes[1],
        label="Normalized burden within evaluated range",
    )
    figure.suptitle("Movement-aware Pareto trade-offs")
    figure.tight_layout()
    figure_data = all_designs[
        [
            "design_id",
            "mean_wait_seconds",
            "required_waiting_area_m2_at_density_limit",
            "mean_movement_starts",
            "throughput_per_hour",
            "pareto_efficient",
        ]
    ].copy()
    figure_data.to_csv(DATA_DIR / "figure_06_data.csv", index=False)
    caption = (
        "All evaluated designs are circles: x is mean wait, y is conditional required "
        "waiting area, monotonic-lightness color is modeled starts/passenger, and marker "
        "area is throughput. The eight nondominated designs are black-edged diamonds and "
        "their normalized objective profiles are shown at right; all share one modeled "
        "start/passenger under the current progression rule."
    )
    return _save_figure(figure, "figure_06_pareto_front"), caption


def _phase_map_figure() -> tuple[Path, str]:
    data = pd.read_csv("results/phase7/design_summary.csv")
    data = data[data["policy"] == "S3"].copy()
    baseline_starts = float(
        pd.read_csv("results/phase7/design_summary.csv")
        .query("policy == 'S0'")["mean_movement_starts"]
        .iloc[0]
    )
    data = data[data["mean_movement_starts"] < baseline_starts]
    phase = data.pivot_table(
        index="downstream_threshold",
        columns="batch_size",
        values="minimum_throughput_relative_lower_bound",
        aggfunc="min",
    )
    figure, axis = plt.subplots(figsize=(6, 4.5))
    image = axis.imshow(phase.values, cmap="coolwarm", aspect="auto")
    axis.set_xticks(range(len(phase.columns)), [str(value) for value in phase.columns])
    axis.set_yticks(range(len(phase.index)), [str(value) for value in phase.index])
    axis.set(xlabel="Batch size", ylabel="Downstream threshold")
    axis.set_title("Worst throughput bound among movement-improving variants")
    for row in range(phase.shape[0]):
        for column in range(phase.shape[1]):
            axis.text(
                column,
                row,
                f"{phase.iloc[row, column]:.2f}",
                ha="center",
                va="center",
                color="black",
            )
    figure.colorbar(image, ax=axis, label="Paired relative lower bound")
    figure.tight_layout()
    phase.to_csv(DATA_DIR / "figure_07_data.csv")
    caption = "All cells improve movement starts; the acceptability threshold is −0.02."
    return _save_figure(figure, "figure_07_phase_map"), caption


def _falsification_figure() -> tuple[Path, str]:
    stress = pd.read_csv("results/phase8/scenario_comparisons.csv")
    flag_columns = [
        "throughput_failure",
        "waiting_failure",
        "space_failure",
        "unfinished_failure",
        "movement_null",
        "staffing_failure",
        "release_surge_failure",
        "conflict_proxy_failure",
    ]
    matrix = (
        stress.groupby("category")[flag_columns]
        .agg(lambda series: (series == "yes").mean())
        .sort_index()
    )
    figure = plt.figure(figsize=(11, 8.2))
    grid = figure.add_gridspec(2, 2, height_ratios=[1.15, 1.0])
    map_axis = figure.add_subplot(grid[0, :])
    image = map_axis.imshow(matrix.values, vmin=0, vmax=1, cmap="magma", aspect="auto")
    map_axis.set_xticks(
        range(len(flag_columns)),
        [
            {
                "release_surge_failure": "release surge (proxy)",
                "conflict_proxy_failure": "conflict (proxy)",
            }.get(value, value.replace("_failure", "").replace("_", " "))
            for value in flag_columns
        ],
        rotation=25,
        ha="right",
    )
    map_axis.set_yticks(range(len(matrix.index)), matrix.index)
    map_axis.set_title("(a) Criteria triggered by stress-test category", loc="left", fontsize=10)
    figure.colorbar(image, ax=map_axis, label="Fraction of scenarios triggering")
    selections = (
        (
            grid[1, 0],
            stress[stress["category"].isin(["arrival_process", "service_variability"])],
            "(b) Arrival process and service variability",
        ),
        (
            grid[1, 1],
            stress[stress["category"].isin(["compliance", "guidance_delay"])],
            "(c) Release compliance and guidance delay",
        ),
    )
    bars = []
    for cell, values, title in selections:
        axis = figure.add_subplot(cell)
        axis.bar(
            values["scenario_id"],
            values["throughput_relative_lower_bound"],
            color="#56B4E9",
        )
        axis.axhline(-0.02, color=COLORS["S3"], ls="--", label="−2% safeguard")
        axis.set(ylabel="Paired relative throughput lower bound")
        axis.set_title(title, loc="left", fontsize=10)
        axis.tick_params(axis="x", rotation=35)
        axis.legend(frameon=False, fontsize=8)
        bars.append(values)
    figure.tight_layout()
    matrix.to_csv(DATA_DIR / "figure_08_data.csv")
    pd.concat(bars)[
        ["scenario_id", "category", "throughput_relative_lower_bound"]
    ].to_csv(DATA_DIR / "figure_08_bars_data.csv", index=False)
    caption = (
        "Prespecified falsification: (a) fraction of S3−S0 stress scenarios triggering each "
        "criterion by category; (b, c) paired relative throughput lower bounds for arrival, "
        "service-variability, compliance, and guidance-delay scenarios against the −2% "
        "safeguard. Release-surge and conflict criteria are unvalidated engineering-proxy "
        "screens, not safety outcomes."
    )
    return _save_figure(figure, "figure_08_falsification"), caption


def _table_document(
    title: str,
    headers: list[str],
    rows: list[list[str]],
    path: Path,
) -> None:
    document = Document()
    document.add_heading(title, level=1)
    table = document.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"
    for cell, value in zip(table.rows[0].cells, headers, strict=True):
        cell.text = value
    for row in rows:
        cells = table.add_row().cells
        for cell, value in zip(cells, row, strict=True):
            cell.text = value
    document.save(path)


def _multi_panel_table_document(
    title: str,
    data: list[dict[str, str]],
    panels: list[tuple[str, list[tuple[str, str]]]],
    path: Path,
) -> None:
    document = Document()
    section = document.sections[0]
    section.left_margin = Inches(0.55)
    section.right_margin = Inches(0.55)
    document.add_heading(title, level=1)
    for panel_title, columns in panels:
        document.add_heading(panel_title, level=2)
        table = document.add_table(rows=1, cols=len(columns))
        table.style = "Table Grid"
        for cell, (_, label) in zip(table.rows[0].cells, columns, strict=True):
            cell.text = label
        for row in data:
            cells = table.add_row().cells
            for cell, (column, _) in zip(cells, columns, strict=True):
                cell.text = row[column]
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    for run in paragraph.runs:
                        run.font.size = Pt(8)
    document.save(path)


def _display_number(value: float, digits: int) -> str:
    rendered = f"{value:.{digits}f}"
    if float(rendered) == 0:
        rendered = rendered.lstrip("-")
    return rendered.replace("-", "−")


def _build_tables() -> None:
    for stale in TABLE_DIR.glob("table_01_parameters_sources.*"):
        stale.unlink()
    parameters = pd.read_csv("references/parameter_sources.csv")
    base = load_config("configs/default.yaml")

    def parameter_row(name: str) -> pd.Series:
        return parameters.loc[parameters["parameter"] == name].iloc[0]

    walking = parameter_row("airport_free_walking_speed")
    startup = parameter_row("pedestrian_startup_delay")
    reaction = parameter_row("pedestrian_reaction_delay")
    slowdown = parameter_row("pedestrian_slowdown_time")
    service = parameter_row("screening_service_rate")
    route_width = parameter_row("accessible_route_clear_width")
    turning = parameter_row("accessible_turning_diameter")
    luggage = parameter_row("luggage_footprint_per_bag")
    luggage_share = parameter_row("luggage_prevalence")
    reduced = parameter_row("reduced_mobility_prevalence")
    service_cv = parameter_row("service_time_cv")
    compliance = parameter_row("release_compliance")
    gate_delay = parameter_row("gate_release_delay")
    for name, configured in (
        ("luggage_prevalence", base.passenger.luggage_prevalence),
        ("reduced_mobility_prevalence", base.passenger.reduced_mobility_prevalence),
        ("service_time_cv", base.service.cv),
        ("release_compliance", base.passenger.release_compliance),
        ("gate_release_delay", base.control.gate_delay_seconds),
        ("airport_free_walking_speed", base.passenger.walking_speed_mps),
    ):
        if abs(float(parameter_row(name).estimate) - configured) > 1e-12:
            raise ValueError(f"Parameter ledger differs from configs/default.yaml: {name}")
    summary_rows = [
        [
            "Demand and screening",
            (
                f"{base.arrival.rate_per_hour:.0f} passengers/h; "
                f"{base.service.servers} lanes; {base.service.mean_seconds:.0f} s mean service"
            ),
            f"{service.lower:.0f}–{service.upper:.0f} passengers/h/lane",
            (
                "Synthetic demand; service range from FAA AC 150/5360-13A and "
                "terminal planning guidance"
            ),
        ],
        [
            "Service and release behavior",
            (
                f"service CV {base.service.cv:.2f}; release compliance "
                f"{base.passenger.release_compliance:.2f}; gate delay "
                f"{base.control.gate_delay_seconds:.2f} s"
            ),
            (
                f"{service_cv.lower:.2f}–{service_cv.upper:.2f}; "
                f"{compliance.lower:.2f}–{compliance.upper:.2f}; "
                f"{gate_delay.lower:.2f}–{gate_delay.upper:.2f} s"
            ),
            "Explicit assumptions; stress tested",
        ],
        [
            "Walking speed",
            f"{base.passenger.walking_speed_mps:.2f} m/s",
            f"{walking.lower:.2f}–{walking.upper:.2f} m/s",
            "Peer-reviewed airport observations{16}",
        ],
        [
            "Stop/start timing",
            (
                f"{startup.estimate:.2f} s startup; {reaction.estimate:.2f} s reaction; "
                f"{slowdown.estimate:.2f} s slowdown"
            ),
            (
                f"{startup.lower:.2f}–{startup.upper:.2f}; "
                f"{reaction.lower:.2f}–{reaction.upper:.2f}; "
                f"{slowdown.lower:.2f}–{slowdown.upper:.2f} s"
            ),
            "Peer-reviewed controlled motion capture{17}",
        ],
        [
            "Passenger heterogeneity",
            (
                f"{base.passenger.luggage_prevalence:.2f} luggage prevalence; "
                f"{base.passenger.reduced_mobility_prevalence:.2f} reduced mobility"
            ),
            (
                f"{luggage_share.lower:.2f}–{luggage_share.upper:.2f}; "
                f"{reduced.lower:.2f}–{reduced.upper:.2f} proportions"
            ),
            "Explicit assumptions informed by luggage literature{15}; stress tested",
        ],
        [
            "Luggage space",
            f"{base.passenger.luggage_footprint_m2_per_bag:.2f} m²/bag",
            f"{luggage.lower:.2f}–{luggage.upper:.2f} m²/bag",
            "Literature-informed engineering assumption{15}",
        ],
        [
            "S3 release rule",
            (
                f"batch {base.control.batch_size}; threshold "
                f"{base.control.downstream_threshold}; maximum hold "
                f"{base.control.maximum_hold_seconds:.0f} s"
            ),
            "Prespecified Phase 7 control grid",
            "Explicit controller design factors",
        ],
        [
            "Configured routes",
            (
                f"S0 {base.geometry.serpentine_distance_m:.0f} m/"
                f"{base.geometry.serpentine_turns} turns; "
                f"stationary {base.geometry.stationary_distance_m:.0f} m/"
                f"{base.geometry.stationary_turns} turns"
            ),
            "Matched short, mid, and long routes",
            "Structural assumptions; matched-route sensitivity",
        ],
        [
            "Spatial constraints",
            (
                f"{base.geometry.accessible_route_width_m:.2f} m route; "
                f"{base.geometry.turning_diameter_m:.2f} m turning; "
                f"{base.geometry.max_waiting_density_per_m2:.2f} passengers/m²"
            ),
            (
                f"minimum {route_width.estimate:.3f} m route and "
                f"{turning.estimate:.3f} m turning"
            ),
            (
                "2010 ADA Standards §403.5.1 and §304.3.1 minima plus engineering "
                "assumptions"
            ),
        ],
    ]
    summary_headers = ["Parameter/group", "Base value", "Range", "Evidence/source"]
    with (TABLE_DIR / "table_01_parameter_summary.csv").open(
        "w",
        newline="",
        encoding="utf-8",
    ) as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(summary_headers)
        writer.writerows(summary_rows)
    _table_document(
        "Table 1. Reader-facing model parameter summary",
        summary_headers,
        summary_rows,
        TABLE_DIR / "table_01_parameter_summary.docx",
    )
    architectures = [
        ["S0", "Conventional switchback", "Continuous/standard release", "B0"],
        ["S1", "Stationary rows", "Full-row batches", "B1–B4"],
        ["S2", "Stationary rows", "Sub-batches", "B1–B4"],
        ["S3", "Stationary rows", "Downstream threshold", "B1–B4"],
        ["S4", "Stationary rows", "Noisy capacity prediction", "B1–B4"],
        ["S5", "Virtual queue benchmark", "Called release", "B3"],
    ]
    with (TABLE_DIR / "table_02_architectures.csv").open(
        "w",
        newline="",
        encoding="utf-8",
    ) as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["Policy", "Waiting architecture", "Control rule", "Layouts"])
        writer.writerows(architectures)
    _table_document(
        "Table 2. Architectures and control policies",
        ["Policy", "Waiting architecture", "Control rule", "Layouts"],
        architectures,
        TABLE_DIR / "table_02_architectures.docx",
    )
    primary_path = Path("results/phase5/primary_results.csv")
    primary = pd.read_csv(primary_path)
    main_endpoints = [
        "mean_movement_distance_m",
        "mean_movement_starts",
        "mean_turning_angle_degrees",
        "required_waiting_area_m2_at_density_limit",
        "throughput_per_hour",
    ]
    endpoint_labels = {
        "mean_movement_distance_m": "Movement distance (m/passenger)",
        "mean_movement_starts": "Modeled movement starts (per passenger)",
        "mean_turning_angle_degrees": "Cumulative turning (degrees/passenger)",
        "required_waiting_area_m2_at_density_limit": "Required waiting area (m²)",
        "throughput_per_hour": "Throughput (passengers/h)",
    }
    endpoint_digits = {
        "mean_movement_distance_m": 1,
        "mean_movement_starts": 1,
        "mean_turning_angle_degrees": 0,
        "required_waiting_area_m2_at_density_limit": 1,
        "throughput_per_hour": 1,
    }
    endpoint_interpretations = {
        "mean_movement_distance_m": "Structural route contrast",
        "mean_movement_starts": "Model-dependent; fewer starts",
        "mean_turning_angle_degrees": "Structural route contrast",
        "required_waiting_area_m2_at_density_limit": (
            "Conditional spatial outcome; lower area"
        ),
        "throughput_per_hour": "Safeguard met: lower CI > −2% of S0",
    }
    table_rows: list[list[str]] = []
    for load in sorted(primary["load_regime"].unique()):
        for endpoint in main_endpoints:
            row = primary[
                (primary["load_regime"] == load)
                & (primary["endpoint"] == endpoint)
            ].iloc[0]
            digits = endpoint_digits[endpoint]
            table_rows.append(
                [
                    f"{load:.2f}",
                    endpoint_labels[endpoint],
                    _display_number(float(row["baseline_mean"]), digits),
                    _display_number(
                        float(row["mean_paired_difference"]),
                        digits,
                    ),
                    (
                        f"{_display_number(float(row['ci95_lower']), digits)} to "
                        f"{_display_number(float(row['ci95_upper']), digits)}"
                    ),
                    endpoint_interpretations[endpoint],
                ]
            )
    table_headers = [
        "Load",
        "Endpoint",
        "S0 mean",
        "S3−S0 difference",
        "95% paired CI",
        "Interpretation/criterion",
    ]
    with (TABLE_DIR / "table_03_primary_outcomes.csv").open(
        "w",
        newline="",
        encoding="utf-8",
    ) as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(table_headers)
        writer.writerows(table_rows)
    _table_document(
        "Table 3. Primary paired outcomes and interpretation",
        table_headers,
        table_rows,
        TABLE_DIR / "table_03_primary_outcomes.docx",
    )
    for stale in TABLE_DIR.glob("table_04_failure_summary.*"):
        stale.unlink()
    structural = pd.read_csv("results/phase13/summary.csv")
    route_labels = {
        "configured_routes": "Configured (S0 switchback; S3 stationary)",
        "matched_short_route": "Matched short",
        "matched_mid_route": "Matched mid",
        "matched_long_route": "Matched long",
    }

    def interval(row: pd.Series, endpoint: str, digits: int) -> str:
        return (
            f"{_display_number(float(row[f'difference_{endpoint}']), digits)} "
            f"({_display_number(float(row[f'ci95_lower_{endpoint}']), digits)} to "
            f"{_display_number(float(row[f'ci95_upper_{endpoint}']), digits)})"
        )

    matched_rows = []
    for _, row in structural.iterrows():
        if row["scenario"] == "configured_routes":
            route = (
                f"S0 {row['s0_mean_movement_distance_m']:.0f} m/"
                f"{row['s0_mean_turning_angle_degrees']:.0f}°; S3 "
                f"{row['s3_mean_movement_distance_m']:.0f} m/"
                f"{row['s3_mean_turning_angle_degrees']:.0f}°"
            )
        else:
            route = (
                f"Both {row['s0_mean_movement_distance_m']:.0f} m/"
                f"{row['s0_mean_turning_angle_degrees']:.0f}°"
            )
        matched_rows.append(
            [
                route_labels[row["scenario"]],
                f"{row['load_regime']:.2f}",
                route,
                interval(row, "throughput_per_hour", 1),
                interval(row, "mean_movement_starts", 2),
                "yes" if row["throughput_acceptable_2pct"] == "yes" else "no",
            ]
        )
    matched_headers = [
        "Route definition",
        "Load",
        "Distance/turning per passenger",
        "Throughput S3−S0, passengers/h (95% CI)",
        "Modeled starts S3−S0 (95% CI)",
        "Safeguard met",
    ]
    with (TABLE_DIR / "table_04_matched_routes.csv").open(
        "w",
        newline="",
        encoding="utf-8",
    ) as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(matched_headers)
        writer.writerows(matched_rows)
    _table_document(
        "Table 4. Configured- and matched-route sensitivity",
        matched_headers,
        matched_rows,
        TABLE_DIR / "table_04_matched_routes.docx",
    )

    robustness = pd.read_csv("results/phase8/scenario_comparisons.csv")
    thresholds = pd.read_csv("results/phase8/proxy_threshold_sensitivity.csv")

    def threshold_profile(column: str) -> str:
        return "; ".join(
            f"{ratio:.2f}: {int(count)}"
            for ratio, count in zip(
                thresholds["ratio_threshold"],
                thresholds[column],
                strict=True,
            )
        )

    criteria = [
        ("Throughput", "throughput_failure", "Operational", "—"),
        ("Waiting", "waiting_failure", "Operational", "—"),
        ("Required area", "space_failure", "Operational", "—"),
        ("Unfinished demand", "unfinished_failure", "Operational", "—"),
        ("Movement null", "movement_null", "Mechanism", "—"),
        ("Staffing", "staffing_failure", "Feasibility", "—"),
        (
            "Release surge",
            "release_surge_failure",
            "Engineering proxy (unvalidated)",
            threshold_profile("release_surge_scenarios"),
        ),
        (
            "Conflict",
            "conflict_proxy_failure",
            "Engineering proxy (unvalidated)",
            threshold_profile("conflict_proxy_scenarios"),
        ),
        ("Any criterion", "failure_detected", "Combined", "—"),
    ]
    falsification_rows = [
        [
            label,
            category,
            f"{int((robustness[column] == 'yes').sum())}/{len(robustness)}",
            profile,
        ]
        for label, column, category, profile in criteria
    ]
    falsification_headers = [
        "Criterion",
        "Criterion type",
        "Scenarios triggering",
        "Flags by proxy ratio threshold",
    ]
    with (TABLE_DIR / "table_05_falsification_summary.csv").open(
        "w",
        newline="",
        encoding="utf-8",
    ) as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(falsification_headers)
        writer.writerows(falsification_rows)
    _table_document(
        "Table 5. Prespecified falsification and proxy-threshold sensitivity",
        falsification_headers,
        falsification_rows,
        TABLE_DIR / "table_05_falsification_summary.docx",
    )

    transfer = pd.read_csv("results/phase9/transferability_comparisons.csv")
    benchmark_rows = []
    for scenario, values in transfer.groupby("scenario_id", sort=True):
        s3 = values[values["policy"] == "S3"].iloc[0]
        s5 = values[values["policy"] == "S5"].iloc[0]
        benchmark_rows.append(
            [
                str(s3["geometry_id"]),
                str(s3["regime_id"]),
                _display_number(100 * float(s3["throughput_relative_lower_bound"]), 1),
                str(s3["throughput_acceptable_2pct"]),
                _display_number(100 * float(s5["throughput_relative_lower_bound"]), 1),
                str(s5["throughput_acceptable_2pct"]),
                _display_number(float(s3["movement_starts_difference"]), 1),
            ]
        )
    benchmark_headers = [
        "Geometry",
        "Regime",
        "S3 lower bound (% of S0)",
        "S3 safeguard",
        "S5 lower bound (% of S0)",
        "S5 safeguard",
        "S3−S0 modeled starts",
    ]
    with (TABLE_DIR / "table_06_geometry_benchmark.csv").open(
        "w",
        newline="",
        encoding="utf-8",
    ) as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(benchmark_headers)
        writer.writerows(benchmark_rows)
    _table_document(
        "Table 6. Generic geometry-regime benchmark",
        benchmark_headers,
        benchmark_rows,
        TABLE_DIR / "table_06_geometry_benchmark.docx",
    )


def _build_deck(main_items: list[tuple[Path, str]]) -> None:
    presentation = Presentation()
    presentation.slide_width = Inches(13.333)
    presentation.slide_height = Inches(7.5)
    items = [
        (f"Figure {number}", path, caption)
        for number, (path, caption) in enumerate(main_items, 1)
    ]
    for label, path, caption in items:
        slide = presentation.slides.add_slide(presentation.slide_layouts[6])
        title = slide.shapes.add_textbox(Inches(0.5), Inches(0.2), Inches(12.3), Inches(0.5))
        title.text_frame.paragraphs[0].text = label
        title.text_frame.paragraphs[0].font.size = Pt(24)
        picture = slide.shapes.add_picture(str(path), Inches(0.6), Inches(0.8), height=Inches(5.9))
        if picture.width > Inches(12.1):
            ratio = Inches(12.1) / picture.width
            picture.width = Inches(12.1)
            picture.height = int(picture.height * ratio)
        picture.left = int((presentation.slide_width - picture.width) / 2)
        box = slide.shapes.add_textbox(Inches(0.6), Inches(6.8), Inches(12.0), Inches(0.45))
        box.text_frame.word_wrap = True
        box.text_frame.paragraphs[0].text = caption
        box.text_frame.paragraphs[0].font.size = Pt(11)
    presentation.save(FIGURE_DIR / "all_figures_editable.pptx")


def main() -> None:
    _prepare()
    main_items = [
        _concept_figure(),
        _trajectory_figure(),
        _movement_load_figures(),
        _control_response_figure(),
        _space_figure(),
        _pareto_figure(),
        _phase_map_figure(),
        _falsification_figure(),
    ]
    _build_tables()
    _build_deck(main_items)
    caption_lines = ["# Figure captions", ""]
    for number, (_, caption) in enumerate(main_items, start=1):
        caption_lines.extend([f"**Figure {number}.** {caption}", ""])
    Path("FIGURE_CAPTIONS.md").write_text(
        "\n".join(caption_lines),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
