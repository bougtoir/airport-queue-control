from pathlib import Path

import pandas as pd
import pytest
import yaml
from pptx import Presentation

ROOT = Path(__file__).resolve().parents[1]


def test_phase10_main_figure_outputs_exist():
    pngs = sorted((ROOT / "figures").glob("figure_*.png"))
    svgs = sorted((ROOT / "figures").glob("figure_*.svg"))
    pdfs = sorted((ROOT / "figures").glob("figure_*.pdf"))
    assert len(pngs) == 8
    assert len(svgs) == 8
    assert len(pdfs) == 8
    assert all(path.stat().st_size > 10_000 for path in pngs)
    deck = ROOT / "figures" / "all_figures_editable.pptx"
    assert deck.stat().st_size > 10_000
    assert len(Presentation(deck).slides) == 8
    assert (ROOT / "FIGURE_CAPTIONS.md").exists()


def test_phase10_tables_exist_without_separate_supplement():
    assert len(list((ROOT / "tables").glob("table_*.csv"))) == 6
    assert len(list((ROOT / "tables").glob("table_*.docx"))) == 6
    assert not (ROOT / "supplementary_figures").exists()
    assert not (ROOT / "supplementary_tables").exists()


def test_parameter_ledger_matches_simulator_configuration():
    ledger = pd.read_csv(ROOT / "references" / "parameter_sources.csv").set_index("parameter")
    config = yaml.safe_load((ROOT / "configs" / "default.yaml").read_text(encoding="utf-8"))
    assert float(ledger.loc["reduced_mobility_prevalence", "estimate"]) == pytest.approx(
        config["passenger"]["reduced_mobility_prevalence"]
    )
    assert float(ledger.loc["release_compliance", "estimate"]) == pytest.approx(
        config["passenger"]["release_compliance"]
    )
    assert float(ledger.loc["service_time_cv", "estimate"]) == pytest.approx(
        config["service"]["cv"]
    )
    table_1 = pd.read_csv(ROOT / "tables" / "table_01_parameter_summary.csv")
    heterogeneity = table_1.loc[table_1["Parameter/group"] == "Passenger heterogeneity"]
    assert "0.04 reduced mobility" in heterogeneity["Base value"].iloc[0]
