from pathlib import Path

from pptx import Presentation

ROOT = Path(__file__).resolve().parents[1]


def test_phase10_main_figure_outputs_exist():
    pngs = sorted((ROOT / "figures").glob("figure_*.png"))
    svgs = sorted((ROOT / "figures").glob("figure_*.svg"))
    pdfs = sorted((ROOT / "figures").glob("figure_*.pdf"))
    assert len(pngs) == 7
    assert len(svgs) == 7
    assert len(pdfs) == 7
    assert all(path.stat().st_size > 10_000 for path in pngs)
    deck = ROOT / "figures" / "all_figures_editable.pptx"
    assert deck.stat().st_size > 10_000
    assert len(Presentation(deck).slides) == 14
    assert (ROOT / "FIGURE_CAPTIONS.md").exists()


def test_phase10_supplement_and_tables_exist():
    assert len(list((ROOT / "supplementary_figures").glob("*.png"))) == 7
    assert len(list((ROOT / "supplementary_figures").glob("*.svg"))) == 7
    assert len(list((ROOT / "supplementary_figures").glob("*.pdf"))) == 7
    assert len(list((ROOT / "tables").glob("table_*.csv"))) == 4
    assert len(list((ROOT / "tables").glob("table_*.docx"))) == 4
    assert len(list((ROOT / "supplementary_tables").glob("table_*.csv"))) == 3
    assert len(list((ROOT / "supplementary_tables").glob("table_*.docx"))) == 3
