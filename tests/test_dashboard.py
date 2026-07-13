from __future__ import annotations

import pytest
from streamlit.testing.v1 import AppTest
from pathlib import Path

from src.config import DATA_DIR
from src.dashboard.data_access import (
    build_player_frame,
    build_team_summary,
    load_dashboard_data,
)


@pytest.mark.skipif(
    not (DATA_DIR / "matches.csv").exists(), reason="raw CSV hanya tersedia lokal"
)
def test_dashboard_aggregates_all_teams_and_players() -> None:
    raw = load_dashboard_data(DATA_DIR)
    teams = build_team_summary(raw)
    players = build_player_frame(raw)

    assert len(teams) == 48
    assert len(players) == 1_248
    assert {"France", "Spain", "England", "Argentina"}.issubset(set(teams["team"]))


def test_streamlit_all_pages_smoke() -> None:
    app = AppTest.from_file("app.py", default_timeout=30).run()
    assert not app.exception
    navigation = app.radio[0]

    for page in ("Tim", "Pemain", "Evaluasi", "Prediksi"):
        app = navigation.set_value(page).run(timeout=30)
        assert not app.exception
        navigation = app.radio[0]


def test_ferrari_design_tokens_are_installed_and_applied() -> None:
    root = Path(__file__).resolve().parents[1]
    design = (root / "DESIGN.md").read_text(encoding="utf-8")
    styles = (root / "src" / "dashboard" / "styles.py").read_text(encoding="utf-8")
    charts = (root / "src" / "dashboard" / "charts.py").read_text(encoding="utf-8")

    assert "name: Ferrari-design-analysis" in design
    for token in ("#181818", "#303030", "#da291c"):
        assert token.lower() in styles.lower()
        assert token.lower() in charts.lower()
    assert "top-navigation" in styles


def test_dashboard_uses_controlled_dark_telemetry_surfaces() -> None:
    root = Path(__file__).resolve().parents[1]
    pages = (root / "src" / "dashboard" / "pages.py").read_text(encoding="utf-8")
    components = (root / "src" / "dashboard" / "components.py").read_text(
        encoding="utf-8"
    )
    styles = (root / "src" / "dashboard" / "styles.py").read_text(encoding="utf-8")

    assert "st.metric(" not in pages
    assert ".metric(" not in pages
    assert "st.dataframe(" not in pages
    assert "telemetry_specs" in pages
    assert "telemetry_table" in pages
    assert "telemetry-spec-grid" in components
    assert "telemetry-table-wrap" in components
    assert "--canvas-root: #101010" in styles
    assert '[data-testid="stMainBlockContainer"]' in styles
    assert ".stAppDeployButton" in styles
