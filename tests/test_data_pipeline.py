from __future__ import annotations

import numpy as np
import pytest

from src.config import DATA_DIR, FORBIDDEN_MODEL_COLUMNS, SEMIFINAL_MATCH_IDS
from src.data import (
    FEATURE_COLUMNS,
    build_match_features,
    chronological_folds,
    load_raw_data,
)

pytestmark = pytest.mark.skipif(
    not (DATA_DIR / "matches.csv").exists(), reason="raw CSV hanya tersedia lokal"
)


def test_feature_contract_and_match_orientation() -> None:
    frame = build_match_features(load_raw_data())
    regular = frame.query("status == 'Completed' and result_type == 'Regular'")
    semifinals = frame[frame["match_id"].isin(SEMIFINAL_MATCH_IDS)]

    assert len(frame) == 102
    assert len(regular) == 92
    assert not (set(FEATURE_COLUMNS) & FORBIDDEN_MODEL_COLUMNS)
    assert np.isfinite(frame[FEATURE_COLUMNS].to_numpy()).all()
    assert list(
        semifinals[["home_team_name", "away_team_name"]].itertuples(
            index=False, name=None
        )
    ) == [("France", "Spain"), ("England", "Argentina")]


def test_each_fold_uses_only_earlier_matches() -> None:
    frame = build_match_features(load_raw_data())
    regular = frame.query("status == 'Completed' and result_type == 'Regular'").reset_index(
        drop=True
    )
    for train, valid in chronological_folds(regular):
        assert regular.iloc[train]["kickoff"].max() < regular.iloc[valid]["kickoff"].min()


def test_future_observation_does_not_change_its_own_prematch_features() -> None:
    raw = load_raw_data()
    original = build_match_features(raw)
    changed = {name: table.copy(deep=True) for name, table in raw.items()}
    mask = changed["stats"]["match_id"] == 100
    changed["stats"].loc[mask, "total_shots"] = 999
    rebuilt = build_match_features(changed)

    before_future = original["match_id"] <= 100
    np.testing.assert_allclose(
        original.loc[before_future, FEATURE_COLUMNS],
        rebuilt.loc[before_future, FEATURE_COLUMNS],
    )

