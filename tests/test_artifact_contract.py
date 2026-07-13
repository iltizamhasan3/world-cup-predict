from __future__ import annotations

import copy

import pytest

from src.training import validate_artifacts


def _minimal_distribution() -> dict[str, object]:
    return {
        "labels": ["0", "1"],
        "probabilities": [0.8, 0.2],
        "expected": 0.2,
        "interval_80": [0, 1],
        "family": "test",
    }


def _artifacts() -> tuple[dict, dict]:
    event = {
        "home": _minimal_distribution(),
        "away": _minimal_distribution(),
        "total": _minimal_distribution(),
    }
    matches = []
    for match_id, home, away in (
        (101, "France", "Spain"),
        (102, "England", "Argentina"),
    ):
        matches.append(
            {
                "match_id": match_id,
                "home_team": home,
                "away_team": away,
                "score_90": {"matrix": [[0.25, 0.25], [0.25, 0.25]]},
                "outcome_90": {"home_win": 0.4, "draw": 0.3, "away_win": 0.3},
                "advance": {"home": 0.5, "away": 0.5},
                "events": {"red_cards": copy.deepcopy(event)},
            }
        )
    return {"matches": matches}, {"sample_size_90_minutes": 92}


def test_artifact_validator_accepts_normalized_contract() -> None:
    predictions, evaluation = _artifacts()
    validate_artifacts(predictions, evaluation)


def test_artifact_validator_rejects_wrong_orientation() -> None:
    predictions, evaluation = _artifacts()
    predictions["matches"][1]["home_team"] = "Argentina"
    with pytest.raises(ValueError, match="Orientasi semifinal"):
        validate_artifacts(predictions, evaluation)


def test_artifact_validator_rejects_probability_drift() -> None:
    predictions, evaluation = _artifacts()
    predictions["matches"][0]["events"]["red_cards"]["home"]["probabilities"] = [0.8, 0.3]
    with pytest.raises(ValueError, match="tidak berjumlah"):
        validate_artifacts(predictions, evaluation)

