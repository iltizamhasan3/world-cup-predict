from __future__ import annotations

import pytest
from streamlit.testing.v1 import AppTest

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
    navigation = app.sidebar.radio[0]

    for page in ("Tim", "Pemain", "Evaluasi", "Prediksi"):
        app = navigation.set_value(page).run(timeout=30)
        assert not app.exception
        navigation = app.sidebar.radio[0]

