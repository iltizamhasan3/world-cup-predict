from __future__ import annotations

import numpy as np

from src.probability import (
    advancement_probabilities,
    bernoulli_distribution,
    convolve_count_distributions,
    count_distribution,
    score_distribution,
)


def test_score_matrix_and_derived_probabilities_are_normalized() -> None:
    result = score_distribution(1.7, 1.2, rho=-0.04)
    matrix = np.asarray(result["matrix"])

    assert matrix.shape == (8, 8)
    assert np.isclose(matrix.sum(), 1.0, atol=1e-10)
    assert (matrix >= 0).all()
    assert np.isclose(sum(result["outcome_90"].values()), 1.0, atol=1e-10)
    assert len(result["top_exact_scores"]) == 5


def test_advancement_and_shootout_contract() -> None:
    score = score_distribution(1.4, 1.3)
    advance = advancement_probabilities(1.4, 1.3, score["outcome_90"])

    assert np.isclose(advance["home"] + advance["away"], 1.0)
    assert 0 <= advance["shootout_probability"] <= score["outcome_90"]["draw"]


def test_event_distributions_are_normalized() -> None:
    home = count_distribution(12.3, "negative_binomial", 0.25)
    away = count_distribution(9.4)
    total = convolve_count_distributions(home, away)
    binary = bernoulli_distribution(0.08)

    for distribution in (home, away, total, binary):
        probabilities = np.asarray(distribution["probabilities"])
        assert (probabilities >= 0).all()
        assert np.isclose(probabilities.sum(), 1.0, atol=1e-10)

