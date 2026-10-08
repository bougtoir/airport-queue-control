import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _rows(name: str) -> list[dict[str, str]]:
    with (ROOT / "results" / "phase13" / name).open(
        newline="",
        encoding="utf-8",
    ) as handle:
        return list(csv.DictReader(handle))


def test_phase13_route_sensitivity_complete():
    replications = _rows("replications.csv")
    summary = _rows("summary.csv")
    assert len(replications) == 4 * 2 * 50 * 2
    assert len(summary) == 4 * 2
    assert all(int(row["replications"]) == 50 for row in summary)


def test_matched_routes_remove_distance_and_turning_contrasts():
    rows = [row for row in _rows("summary.csv") if row["scenario"] != "configured_routes"]
    assert all(abs(float(row["difference_mean_movement_distance_m"])) < 1e-12 for row in rows)
    assert all(abs(float(row["difference_mean_turning_angle_degrees"])) < 1e-12 for row in rows)
