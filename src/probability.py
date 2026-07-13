"""Utilitas distribusi yang menjaga massa probabilitas secara eksplisit."""

from __future__ import annotations

import numpy as np
from scipy.stats import nbinom, poisson


def _dc_tau(home_goals: int, away_goals: int, home_rate: float, away_rate: float, rho: float) -> float:
    if home_goals == 0 and away_goals == 0:
        return 1.0 - home_rate * away_rate * rho
    if home_goals == 0 and away_goals == 1:
        return 1.0 + home_rate * rho
    if home_goals == 1 and away_goals == 0:
        return 1.0 + away_rate * rho
    if home_goals == 1 and away_goals == 1:
        return 1.0 - rho
    return 1.0


def exact_score_probability(
    home_goals: int,
    away_goals: int,
    home_rate: float,
    away_rate: float,
    rho: float = 0.0,
) -> float:
    """Probabilitas satu skor; dipakai oleh evaluasi log loss."""

    base = poisson.pmf(home_goals, home_rate) * poisson.pmf(away_goals, away_rate)
    tau = max(1e-9, _dc_tau(home_goals, away_goals, home_rate, away_rate, rho))
    return float(max(base * tau, 1e-15))


def score_distribution(
    home_rate: float,
    away_rate: float,
    rho: float = 0.0,
    explicit_max: int = 6,
    compute_max: int = 24,
) -> dict[str, object]:
    """Matriks 0-6/7+ beserta pemisahan outcome pada sel tail-tail."""

    home_rate = float(np.clip(home_rate, 0.05, 8.0))
    away_rate = float(np.clip(away_rate, 0.05, 8.0))
    values = np.arange(compute_max + 1)
    full = np.outer(poisson.pmf(values, home_rate), poisson.pmf(values, away_rate))
    full[0, 0] *= max(1e-9, _dc_tau(0, 0, home_rate, away_rate, rho))
    full[0, 1] *= max(1e-9, _dc_tau(0, 1, home_rate, away_rate, rho))
    full[1, 0] *= max(1e-9, _dc_tau(1, 0, home_rate, away_rate, rho))
    full[1, 1] *= max(1e-9, _dc_tau(1, 1, home_rate, away_rate, rho))
    full /= full.sum()

    size = explicit_max + 2
    matrix = np.zeros((size, size), dtype=float)
    for home_goals in range(compute_max + 1):
        h_bin = min(home_goals, explicit_max + 1)
        for away_goals in range(compute_max + 1):
            a_bin = min(away_goals, explicit_max + 1)
            matrix[h_bin, a_bin] += full[home_goals, away_goals]
    matrix /= matrix.sum()

    home_win = float(np.tril(full, -1).sum())
    draw = float(np.trace(full))
    away_win = float(np.triu(full, 1).sum())
    outcome = np.array([home_win, draw, away_win], dtype=float)
    outcome /= outcome.sum()

    tail_start = explicit_max + 1
    tail = full[tail_start:, tail_start:]
    tail_split = {
        "home_win": float(np.tril(tail, -1).sum()),
        "draw": float(np.trace(tail)),
        "away_win": float(np.triu(tail, 1).sum()),
    }
    labels = [str(value) for value in range(explicit_max + 1)] + [f"{explicit_max + 1}+"]
    top_scores = []
    for h in range(explicit_max + 1):
        for a in range(explicit_max + 1):
            top_scores.append(
                {"score": f"{h}-{a}", "probability": float(matrix[h, a])}
            )
    top_scores.sort(key=lambda item: item["probability"], reverse=True)
    return {
        "labels": labels,
        "matrix": matrix.tolist(),
        "top_exact_scores": top_scores[:5],
        "outcome_90": {
            "home_win": float(outcome[0]),
            "draw": float(outcome[1]),
            "away_win": float(outcome[2]),
        },
        "tail_7_plus_outcome_split": tail_split,
        "expected_goals": {"home": home_rate, "away": away_rate},
    }


def advancement_probabilities(
    home_rate: float,
    away_rate: float,
    regular_outcome: dict[str, float] | None = None,
) -> dict[str, float]:
    """Simulasi analitik extra time 30 menit dan shootout netral 50/50."""

    extra = score_distribution(home_rate / 3.0, away_rate / 3.0, compute_max=18)[
        "outcome_90"
    ]
    regular = regular_outcome or score_distribution(home_rate, away_rate)["outcome_90"]
    draw_90 = float(regular["draw"])
    shootout = float(draw_90 * extra["draw"])
    home = regular["home_win"] + draw_90 * (extra["home_win"] + 0.5 * extra["draw"])
    away = regular["away_win"] + draw_90 * (extra["away_win"] + 0.5 * extra["draw"])
    total = home + away
    return {
        "home": float(home / total),
        "away": float(away / total),
        "shootout_probability": shootout,
        "extra_time_draw_given_draw_90": float(extra["draw"]),
    }


def count_distribution(
    mean: float,
    family: str = "poisson",
    dispersion: float = 0.0,
    tail_probability: float = 0.005,
) -> dict[str, object]:
    """Distribusi count terpotong dengan satu bin tail yang menyerap sisa massa."""

    mean = float(max(mean, 0.01))
    if family == "negative_binomial":
        alpha = float(max(dispersion, 1e-6))
        size = 1.0 / alpha
        probability = size / (size + mean)
        distribution = nbinom(size, probability)
    else:
        distribution = poisson(mean)
    cutoff = int(np.clip(distribution.ppf(1.0 - tail_probability), 2, 80))
    values = np.arange(cutoff + 1)
    probabilities = distribution.pmf(values)
    tail = max(0.0, 1.0 - float(probabilities.sum()))
    all_probabilities = np.append(probabilities, tail)
    all_probabilities /= all_probabilities.sum()
    low, high = distribution.ppf([0.1, 0.9])
    return {
        "labels": [str(value) for value in values] + [f"{cutoff + 1}+"],
        "probabilities": all_probabilities.tolist(),
        "expected": mean,
        "interval_80": [int(low), int(high)],
        "family": family,
        "dispersion": float(dispersion),
    }


def convolve_count_distributions(home: dict[str, object], away: dict[str, object]) -> dict[str, object]:
    """Distribusi total dari mean/family kedua tim."""

    home_mean = float(home["expected"])
    away_mean = float(away["expected"])
    family = (
        "negative_binomial"
        if "negative_binomial" in {home["family"], away["family"]}
        else "poisson"
    )
    if family == "poisson":
        return count_distribution(home_mean + away_mean)
    weighted_alpha = (
        float(home.get("dispersion", 0.0)) * home_mean**2
        + float(away.get("dispersion", 0.0)) * away_mean**2
    ) / max((home_mean + away_mean) ** 2, 1e-9)
    return count_distribution(
        home_mean + away_mean,
        family="negative_binomial",
        dispersion=max(weighted_alpha, 1e-6),
    )


def bernoulli_distribution(probability: float) -> dict[str, object]:
    probability = float(np.clip(probability, 0.0, 1.0))
    return {
        "labels": ["Tidak", "Ya"],
        "probabilities": [1.0 - probability, probability],
        "expected": probability,
        "interval_80": [0, int(probability >= 0.1)],
        "family": "beta_binomial_smoothed",
    }
