"""Model probabilistik skor, count event, dan possession."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from scipy.optimize import minimize_scalar
from scipy.stats import nbinom, poisson
from sklearn.linear_model import PoissonRegressor, Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from .config import RANDOM_SEED, REGULAR_RESULT_TYPE
from .data import (
    EVENT_TARGET_COLUMNS,
    FEATURE_COLUMNS,
    ORIENTED_FEATURE_COLUMNS,
    chronological_folds,
)
from .probability import exact_score_probability, score_distribution


def _safe_log_loss(probabilities: np.ndarray) -> float:
    return float(-np.log(np.clip(probabilities, 1e-15, 1.0)).mean())


def _score_outcome(home: int, away: int) -> str:
    return "home_win" if home > away else "away_win" if home < away else "draw"


def _score_model(alpha: float = 2.0) -> Any:
    return make_pipeline(
        StandardScaler(),
        PoissonRegressor(alpha=alpha, max_iter=2_000, tol=1e-8),
    )


def _fit_rho(
    home_goals: np.ndarray,
    away_goals: np.ndarray,
    home_rate: np.ndarray,
    away_rate: np.ndarray,
) -> float:
    def objective(rho: float) -> float:
        probabilities = [
            exact_score_probability(int(h), int(a), lh, la, rho)
            for h, a, lh, la in zip(
                home_goals, away_goals, home_rate, away_rate, strict=True
            )
        ]
        return _safe_log_loss(np.asarray(probabilities))

    result = minimize_scalar(objective, bounds=(-0.18, 0.18), method="bounded")
    return float(result.x if result.success else 0.0)


def _mix_score_distribution(
    poisson_result: dict[str, object], dc_result: dict[str, object], dc_weight: float
) -> dict[str, object]:
    if dc_weight <= 0.0:
        return poisson_result
    if dc_weight >= 1.0:
        return dc_result
    result = dict(poisson_result)
    matrix = (
        (1.0 - dc_weight) * np.asarray(poisson_result["matrix"])
        + dc_weight * np.asarray(dc_result["matrix"])
    )
    result["matrix"] = matrix.tolist()
    result["outcome_90"] = {
        key: float(
            (1.0 - dc_weight) * poisson_result["outcome_90"][key]
            + dc_weight * dc_result["outcome_90"][key]
        )
        for key in ("home_win", "draw", "away_win")
    }
    scores = []
    for h in range(7):
        for a in range(7):
            scores.append({"score": f"{h}-{a}", "probability": float(matrix[h, a])})
    result["top_exact_scores"] = sorted(
        scores, key=lambda item: item["probability"], reverse=True
    )[:5]
    return result


@dataclass
class ScoreModelBundle:
    selected_model: str
    dc_weight: float
    rho: float
    home_model: Any | None
    away_model: Any | None
    baseline_home_rate: float
    baseline_away_rate: float
    evaluation: dict[str, object]

    def predict_rates(self, frame: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
        if self.selected_model == "smoothed_baseline":
            n = len(frame)
            return (
                np.full(n, self.baseline_home_rate),
                np.full(n, self.baseline_away_rate),
            )
        home = np.clip(self.home_model.predict(frame[FEATURE_COLUMNS]), 0.05, 6.0)
        away = np.clip(self.away_model.predict(frame[FEATURE_COLUMNS]), 0.05, 6.0)
        return home, away

    def predict_distribution(self, frame: pd.DataFrame) -> list[dict[str, object]]:
        home_rates, away_rates = self.predict_rates(frame)
        results = []
        for home_rate, away_rate in zip(home_rates, away_rates, strict=True):
            independent = score_distribution(home_rate, away_rate)
            corrected = score_distribution(home_rate, away_rate, self.rho)
            results.append(
                _mix_score_distribution(independent, corrected, self.dc_weight)
            )
        return results


def train_score_model(match_features: pd.DataFrame) -> ScoreModelBundle:
    """Bandingkan baseline, regularized Poisson, DC, dan blend secara kronologis."""

    regular = match_features.loc[
        (match_features["status"] == "Completed")
        & (match_features["result_type"] == REGULAR_RESULT_TYPE)
    ].sort_values(["date", "match_id"]).reset_index(drop=True)
    if len(regular) != 92:
        raise ValueError(f"Target Regular harus 92 laga, ditemukan {len(regular)}.")

    candidates = {
        "smoothed_baseline": 0.0,
        "regularized_poisson": 0.0,
        "poisson_dc_blend": 0.5,
        "dixon_coles": 1.0,
    }
    fold_records: list[dict[str, object]] = []
    aggregate: dict[str, list[float]] = {
        name: [] for name in candidates
    }
    outcome_aggregate: dict[str, list[float]] = {
        name: [] for name in candidates
    }

    for fold_number, (train_idx, valid_idx) in enumerate(
        chronological_folds(regular), start=1
    ):
        train = regular.iloc[train_idx]
        valid = regular.iloc[valid_idx]
        home_model = _score_model().fit(
            train[FEATURE_COLUMNS], train["home_score"].astype(int)
        )
        away_model = _score_model().fit(
            train[FEATURE_COLUMNS], train["away_score"].astype(int)
        )
        train_home_rate = np.clip(home_model.predict(train[FEATURE_COLUMNS]), 0.05, 6.0)
        train_away_rate = np.clip(away_model.predict(train[FEATURE_COLUMNS]), 0.05, 6.0)
        rho = _fit_rho(
            train["home_score"].to_numpy(int),
            train["away_score"].to_numpy(int),
            train_home_rate,
            train_away_rate,
        )
        valid_home_rate = np.clip(home_model.predict(valid[FEATURE_COLUMNS]), 0.05, 6.0)
        valid_away_rate = np.clip(away_model.predict(valid[FEATURE_COLUMNS]), 0.05, 6.0)
        baseline_home = float((train["home_score"].sum() + 5 * 1.35) / (len(train) + 5))
        baseline_away = float((train["away_score"].sum() + 5 * 1.20) / (len(train) + 5))

        fold_metrics: dict[str, object] = {
            "fold": fold_number,
            "train_matches": len(train),
            "validation_matches": len(valid),
            "train_end": str(train["date"].max().date()),
            "validation_start": str(valid["date"].min().date()),
            "rho": rho,
            "models": {},
        }
        for name, dc_weight in candidates.items():
            exact_probabilities = []
            outcome_probabilities = []
            for row_number, row in enumerate(valid.itertuples(index=False)):
                if name == "smoothed_baseline":
                    home_rate, away_rate = baseline_home, baseline_away
                    weight = 0.0
                else:
                    home_rate = float(valid_home_rate[row_number])
                    away_rate = float(valid_away_rate[row_number])
                    weight = dc_weight
                independent_probability = exact_score_probability(
                    int(row.home_score), int(row.away_score), home_rate, away_rate
                )
                corrected_probability = exact_score_probability(
                    int(row.home_score), int(row.away_score), home_rate, away_rate, rho
                )
                exact_probabilities.append(
                    (1.0 - weight) * independent_probability
                    + weight * corrected_probability
                )
                independent = score_distribution(home_rate, away_rate)["outcome_90"]
                corrected = score_distribution(home_rate, away_rate, rho)["outcome_90"]
                observed = _score_outcome(int(row.home_score), int(row.away_score))
                outcome_probabilities.append(
                    (1.0 - weight) * independent[observed]
                    + weight * corrected[observed]
                )
            exact_loss = _safe_log_loss(np.asarray(exact_probabilities))
            outcome_loss = _safe_log_loss(np.asarray(outcome_probabilities))
            aggregate[name].append(exact_loss)
            outcome_aggregate[name].append(outcome_loss)
            fold_metrics["models"][name] = {
                "exact_score_log_loss": exact_loss,
                "outcome_log_loss": outcome_loss,
            }
        fold_records.append(fold_metrics)

    mean_metrics = {
        name: {
            "exact_score_log_loss": float(np.mean(losses)),
            "outcome_log_loss": float(np.mean(outcome_aggregate[name])),
        }
        for name, losses in aggregate.items()
    }
    best_model = min(
        (name for name in candidates if name != "smoothed_baseline"),
        key=lambda name: mean_metrics[name]["exact_score_log_loss"],
    )
    baseline_loss = mean_metrics["smoothed_baseline"]["exact_score_log_loss"]
    improvement = baseline_loss - mean_metrics[best_model]["exact_score_log_loss"]
    selected = best_model if improvement > 1e-4 else "smoothed_baseline"

    final_home_model = _score_model().fit(
        regular[FEATURE_COLUMNS], regular["home_score"].astype(int)
    )
    final_away_model = _score_model().fit(
        regular[FEATURE_COLUMNS], regular["away_score"].astype(int)
    )
    final_home_rate = np.clip(final_home_model.predict(regular[FEATURE_COLUMNS]), 0.05, 6.0)
    final_away_rate = np.clip(final_away_model.predict(regular[FEATURE_COLUMNS]), 0.05, 6.0)
    rho = _fit_rho(
        regular["home_score"].to_numpy(int),
        regular["away_score"].to_numpy(int),
        final_home_rate,
        final_away_rate,
    )
    baseline_home = float((regular["home_score"].sum() + 5 * 1.35) / (len(regular) + 5))
    baseline_away = float((regular["away_score"].sum() + 5 * 1.20) / (len(regular) + 5))
    evaluation = {
        "sample_size": len(regular),
        "folds": fold_records,
        "aggregate": mean_metrics,
        "selected_model": selected,
        "candidate_winner": best_model,
        "improvement_vs_baseline": float(improvement),
        "fallback_used": selected == "smoothed_baseline",
        "fallback_reason": (
            "Model kandidat tidak mengungguli baseline pada exact-score log loss."
            if selected == "smoothed_baseline"
            else None
        ),
    }
    return ScoreModelBundle(
        selected_model=selected,
        dc_weight=candidates[selected],
        rho=rho if selected != "smoothed_baseline" else 0.0,
        home_model=final_home_model if selected != "smoothed_baseline" else None,
        away_model=final_away_model if selected != "smoothed_baseline" else None,
        baseline_home_rate=baseline_home,
        baseline_away_rate=baseline_away,
        evaluation=evaluation,
    )


def _negative_binomial_alpha(values: np.ndarray) -> float:
    mean = max(float(np.mean(values)), 1e-6)
    variance = float(np.var(values, ddof=1)) if len(values) > 1 else mean
    return float(np.clip((variance - mean) / (mean * mean), 0.02, 2.5))


def _count_nll(values: np.ndarray, means: np.ndarray, family: str, alpha: float) -> float:
    means = np.clip(means, 0.01, 80.0)
    if family == "negative_binomial":
        size = 1.0 / alpha
        probability = size / (size + means)
        likelihood = nbinom.pmf(values, size, probability)
    else:
        likelihood = poisson.pmf(values, means)
    return _safe_log_loss(np.asarray(likelihood))


@dataclass
class CountModelBundle:
    target: str
    selected_model: str
    family: str
    dispersion: float
    model: Any | None
    baseline_mean: float
    evaluation: dict[str, object]

    def predict(self, frame: pd.DataFrame) -> np.ndarray:
        if self.model is None:
            return np.full(len(frame), self.baseline_mean)
        return np.clip(self.model.predict(frame[ORIENTED_FEATURE_COLUMNS]), 0.01, 80.0)


def _event_folds(frame: pd.DataFrame):
    matches = frame[["match_id", "date"]].drop_duplicates().sort_values(["date", "match_id"])
    for train_matches, valid_matches in chronological_folds(matches, minimum_train=48):
        train_ids = set(matches.iloc[train_matches]["match_id"])
        valid_ids = set(matches.iloc[valid_matches]["match_id"])
        yield (
            np.flatnonzero(frame["match_id"].isin(train_ids).to_numpy()),
            np.flatnonzero(frame["match_id"].isin(valid_ids).to_numpy()),
        )


def train_count_models(event_frame: pd.DataFrame) -> dict[str, CountModelBundle]:
    """Pilih Poisson/NB berdasarkan chronological predictive likelihood."""

    bundles: dict[str, CountModelBundle] = {}
    for target in [name for name in EVENT_TARGET_COLUMNS if name != "red_cards"]:
        fold_metrics = []
        aggregate = {"baseline": [], "poisson": [], "negative_binomial": []}
        for fold_number, (train_idx, valid_idx) in enumerate(_event_folds(event_frame), start=1):
            train = event_frame.iloc[train_idx]
            valid = event_frame.iloc[valid_idx]
            model = _score_model(alpha=3.0).fit(
                train[ORIENTED_FEATURE_COLUMNS], train[target]
            )
            predicted = np.clip(
                model.predict(valid[ORIENTED_FEATURE_COLUMNS]), 0.01, 80.0
            )
            baseline_mean = float((train[target].sum() + 10 * train[target].mean()) / (len(train) + 10))
            baseline = np.full(len(valid), baseline_mean)
            alpha = _negative_binomial_alpha(train[target].to_numpy(float))
            values = valid[target].to_numpy(int)
            metrics = {
                "baseline": _count_nll(values, baseline, "poisson", alpha),
                "poisson": _count_nll(values, predicted, "poisson", alpha),
                "negative_binomial": _count_nll(
                    values, predicted, "negative_binomial", alpha
                ),
            }
            for name, value in metrics.items():
                aggregate[name].append(value)
            fold_metrics.append({"fold": fold_number, **metrics})
        means = {name: float(np.mean(values)) for name, values in aggregate.items()}
        candidate_family = min(
            ("poisson", "negative_binomial"), key=lambda name: means[name]
        )
        improves = means[candidate_family] < means["baseline"] - 1e-4
        final_model = _score_model(alpha=3.0).fit(
            event_frame[ORIENTED_FEATURE_COLUMNS], event_frame[target]
        )
        baseline_mean = float(event_frame[target].mean())
        alpha = _negative_binomial_alpha(event_frame[target].to_numpy(float))
        bundles[target] = CountModelBundle(
            target=target,
            selected_model=(f"regularized_{candidate_family}" if improves else "smoothed_baseline"),
            family=candidate_family if improves else "poisson",
            dispersion=alpha if improves and candidate_family == "negative_binomial" else 0.0,
            model=final_model if improves else None,
            baseline_mean=baseline_mean,
            evaluation={
                "folds": fold_metrics,
                "aggregate_nll": means,
                "selected_model": f"regularized_{candidate_family}" if improves else "smoothed_baseline",
                "fallback_used": not improves,
                "fallback_reason": (
                    "Regresi count tidak mengungguli baseline likelihood."
                    if not improves
                    else None
                ),
            },
        )
    return bundles


@dataclass
class PossessionModelBundle:
    selected_model: str
    model: Any | None
    evaluation: dict[str, object]

    def predict_pair(self, home: pd.DataFrame, away: pd.DataFrame) -> tuple[float, float]:
        if self.model is None:
            return 50.0, 50.0
        raw_home = float(np.clip(self.model.predict(home[ORIENTED_FEATURE_COLUMNS])[0], 20, 80))
        raw_away = float(np.clip(self.model.predict(away[ORIENTED_FEATURE_COLUMNS])[0], 20, 80))
        home_share = 100.0 * raw_home / (raw_home + raw_away)
        return float(home_share), float(100.0 - home_share)


def train_possession_model(event_frame: pd.DataFrame) -> PossessionModelBundle:
    fold_metrics = []
    ridge_errors = []
    baseline_errors = []
    for fold_number, (train_idx, valid_idx) in enumerate(_event_folds(event_frame), start=1):
        train = event_frame.iloc[train_idx]
        valid = event_frame.iloc[valid_idx]
        model = make_pipeline(StandardScaler(), Ridge(alpha=25.0)).fit(
            train[ORIENTED_FEATURE_COLUMNS], train["possession"]
        )
        predicted = np.clip(model.predict(valid[ORIENTED_FEATURE_COLUMNS]), 20, 80)
        ridge_mae = float(np.mean(np.abs(valid["possession"].to_numpy() - predicted)))
        baseline_mae = float(np.mean(np.abs(valid["possession"].to_numpy() - 50.0)))
        ridge_errors.append(ridge_mae)
        baseline_errors.append(baseline_mae)
        fold_metrics.append(
            {"fold": fold_number, "ridge_mae": ridge_mae, "baseline_mae": baseline_mae}
        )
    improves = np.mean(ridge_errors) < np.mean(baseline_errors) - 1e-4
    final_model = make_pipeline(StandardScaler(), Ridge(alpha=25.0)).fit(
        event_frame[ORIENTED_FEATURE_COLUMNS], event_frame["possession"]
    )
    return PossessionModelBundle(
        selected_model="constrained_ridge" if improves else "equal_possession_baseline",
        model=final_model if improves else None,
        evaluation={
            "folds": fold_metrics,
            "ridge_mae": float(np.mean(ridge_errors)),
            "baseline_mae": float(np.mean(baseline_errors)),
            "fallback_used": not improves,
            "fallback_reason": (
                "Ridge tidak mengungguli baseline 50/50 pada MAE."
                if not improves
                else None
            ),
        },
    )


def smoothed_rare_event_rates(event_frame: pd.DataFrame, raw_events: pd.DataFrame) -> dict[str, float]:
    """Beta smoothing konservatif untuk red card per tim dan VAR per laga."""

    red_total = float(event_frame["red_cards"].sum())
    red_trials = float(len(event_frame))
    completed_matches = float(event_frame["match_id"].nunique())
    var_total = float((raw_events["event_type"] == "VAR Review").sum())
    return {
        "red_card_team_probability": (red_total + 1.0) / (red_trials + 20.0),
        "var_match_probability": (var_total + 1.0) / (completed_matches + 10.0),
        "observed_red_cards": int(red_total),
        "observed_var_reviews": int(var_total),
    }

