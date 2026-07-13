from __future__ import annotations

import numpy as np
import pytest

from src.config import DATA_DIR, SEMIFINAL_MATCH_IDS
from src.data import build_match_features, load_raw_data
from src.modeling import train_score_model

pytestmark = pytest.mark.skipif(
    not (DATA_DIR / "matches.csv").exists(), reason="raw CSV hanya tersedia lokal"
)


def test_score_model_trains_and_predicts_semifinals() -> None:
    features = build_match_features(load_raw_data())
    bundle = train_score_model(features)
    semifinals = features[features["match_id"].isin(SEMIFINAL_MATCH_IDS)]
    predictions = bundle.predict_distribution(semifinals)

    assert bundle.evaluation["sample_size"] == 92
    assert len(bundle.evaluation["folds"]) == 3
    assert len(predictions) == 2
    for prediction in predictions:
        assert np.isclose(np.asarray(prediction["matrix"]).sum(), 1.0)
        assert np.isclose(sum(prediction["outcome_90"].values()), 1.0)

