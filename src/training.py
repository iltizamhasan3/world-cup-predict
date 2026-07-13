"""Orkestrasi training, pembuatan artifact, dan validasi kontrak JSON."""

from __future__ import annotations

import json
import platform
from importlib.metadata import version
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from scipy.stats import norm

from .config import ARTIFACT_DIR, DATA_DIR, RANDOM_SEED, SEMIFINAL_MATCH_IDS
from .data import (
    build_event_frame,
    build_match_features,
    load_raw_data,
    orient_match,
)
from .modeling import (
    smoothed_rare_event_rates,
    train_count_models,
    train_possession_model,
    train_score_model,
)
from .probability import (
    advancement_probabilities,
    bernoulli_distribution,
    convolve_count_distributions,
    count_distribution,
)

COUNT_EVENTS = (
    "shots",
    "shots_on_target",
    "corners",
    "fouls",
    "offsides",
    "yellow_cards",
    "saves",
)


def _possession_distribution(expected: float, error_scale: float) -> dict[str, object]:
    edges = np.arange(20.0, 85.0, 5.0)
    sigma = float(np.clip(error_scale * 1.5, 4.0, 14.0))
    probabilities = np.diff(norm.cdf(edges, loc=expected, scale=sigma))
    probabilities[0] += norm.cdf(edges[0], loc=expected, scale=sigma)
    probabilities[-1] += 1.0 - norm.cdf(edges[-1], loc=expected, scale=sigma)
    probabilities = np.clip(probabilities, 0.0, None)
    probabilities /= probabilities.sum()
    return {
        "labels": [f"{int(edges[i])}-{int(edges[i + 1] - 1)}" for i in range(len(edges) - 1)],
        "probabilities": probabilities.tolist(),
        "expected": float(expected),
        "interval_80": [
            float(max(0.0, expected - 1.2816 * sigma)),
            float(min(100.0, expected + 1.2816 * sigma)),
        ],
        "family": "constrained_normal_share",
    }


def _binary_total(home_probability: float, away_probability: float) -> dict[str, object]:
    probabilities = np.array(
        [
            (1.0 - home_probability) * (1.0 - away_probability),
            home_probability * (1.0 - away_probability)
            + away_probability * (1.0 - home_probability),
            home_probability * away_probability,
        ]
    )
    probabilities /= probabilities.sum()
    return {
        "labels": ["0", "1", "2"],
        "probabilities": probabilities.tolist(),
        "expected": float(home_probability + away_probability),
        "interval_80": [0, int(np.searchsorted(np.cumsum(probabilities), 0.9))],
        "family": "independent_beta_binomial_smoothed",
    }


def _validate_distribution(distribution: dict[str, Any], location: str) -> None:
    probabilities = np.asarray(distribution["probabilities"], dtype=float)
    if not np.isfinite(probabilities).all():
        raise ValueError(f"NaN/inf ditemukan pada {location}.")
    if (probabilities < -1e-12).any():
        raise ValueError(f"Probabilitas negatif ditemukan pada {location}.")
    if not np.isclose(probabilities.sum(), 1.0, atol=1e-8):
        raise ValueError(f"Probabilitas {location} tidak berjumlah 100%.")


def validate_artifacts(predictions: dict[str, Any], evaluation: dict[str, Any]) -> None:
    """Tolak artifact yang melanggar orientasi atau kontrak probabilitas."""

    matches = predictions.get("matches", [])
    expected = [(101, "France", "Spain"), (102, "England", "Argentina")]
    observed = [
        (match["match_id"], match["home_team"], match["away_team"])
        for match in matches
    ]
    if observed != expected:
        raise ValueError(f"Orientasi semifinal berubah: {observed}.")
    if evaluation.get("sample_size_90_minutes") != 92:
        raise ValueError("Evaluation harus memakai tepat 92 laga Regular.")
    for match in matches:
        matrix = np.asarray(match["score_90"]["matrix"], dtype=float)
        if not np.isfinite(matrix).all() or (matrix < -1e-12).any():
            raise ValueError(f"Matriks skor invalid untuk match {match['match_id']}.")
        if not np.isclose(matrix.sum(), 1.0, atol=1e-8):
            raise ValueError(f"Matriks skor match {match['match_id']} tidak 100%.")
        if not np.isclose(sum(match["outcome_90"].values()), 1.0, atol=1e-8):
            raise ValueError(f"H/D/A match {match['match_id']} tidak 100%.")
        if not np.isclose(sum(match["advance"].values()), 1.0, atol=1e-8):
            raise ValueError(f"Peluang lolos match {match['match_id']} tidak 100%.")
        for event_name, event in match["events"].items():
            for side in ("home", "away", "total"):
                _validate_distribution(
                    event[side], f"match {match['match_id']} / {event_name} / {side}"
                )


def _match_prediction(
    row: pd.Series,
    score_bundle: Any,
    count_bundles: dict[str, Any],
    possession_bundle: Any,
    rare_rates: dict[str, float],
) -> dict[str, Any]:
    score = score_bundle.predict_distribution(pd.DataFrame([row]))[0]
    home_rate = float(score["expected_goals"]["home"])
    away_rate = float(score["expected_goals"]["away"])
    advancement = advancement_probabilities(home_rate, away_rate, score["outcome_90"])
    home_features = orient_match(row, "home")
    away_features = orient_match(row, "away")
    events: dict[str, Any] = {}
    for event_name in COUNT_EVENTS:
        model = count_bundles[event_name]
        home_mean = float(model.predict(home_features)[0])
        away_mean = float(model.predict(away_features)[0])
        home_distribution = count_distribution(
            home_mean, model.family, model.dispersion
        )
        away_distribution = count_distribution(
            away_mean, model.family, model.dispersion
        )
        events[event_name] = {
            "home": home_distribution,
            "away": away_distribution,
            "total": convolve_count_distributions(
                home_distribution, away_distribution
            ),
            "model": model.selected_model,
            "confidence": "medium" if model.model is not None else "low",
        }

    possession_error = float(
        possession_bundle.evaluation.get("ridge_mae")
        or possession_bundle.evaluation.get("baseline_mae")
        or 8.0
    )
    home_possession, away_possession = possession_bundle.predict_pair(
        home_features, away_features
    )
    events["possession"] = {
        "home": _possession_distribution(home_possession, possession_error),
        "away": _possession_distribution(away_possession, possession_error),
        "total": {
            "labels": ["100"],
            "probabilities": [1.0],
            "expected": 100.0,
            "interval_80": [100.0, 100.0],
            "family": "constrained_total",
        },
        "model": possession_bundle.selected_model,
        "confidence": "medium" if possession_bundle.model is not None else "low",
    }

    red_probability = float(rare_rates["red_card_team_probability"])
    events["red_cards"] = {
        "home": bernoulli_distribution(red_probability),
        "away": bernoulli_distribution(red_probability),
        "total": _binary_total(red_probability, red_probability),
        "model": "beta_smoothed_rate",
        "confidence": "low",
    }
    var_probability = float(rare_rates["var_match_probability"])
    side_var_probability = 1.0 - np.sqrt(1.0 - var_probability)
    events["var_reviews"] = {
        "home": bernoulli_distribution(side_var_probability),
        "away": bernoulli_distribution(side_var_probability),
        "total": bernoulli_distribution(var_probability),
        "model": "beta_smoothed_rate",
        "confidence": "low",
    }

    return {
        "match_id": int(row["match_id"]),
        "stage": row["stage_name"],
        "kickoff_utc": pd.Timestamp(row["kickoff"]).strftime("%Y-%m-%dT%H:%M:00Z"),
        "venue": {"stadium": row["venue_name"], "city": row["venue_city"]},
        "home_team": row["home_team_name"],
        "away_team": row["away_team_name"],
        "score_90": {
            "labels": score["labels"],
            "matrix": score["matrix"],
            "top_exact_scores": score["top_exact_scores"],
            "expected_goals": score["expected_goals"],
            "tail_7_plus_outcome_split": score["tail_7_plus_outcome_split"],
        },
        "outcome_90": score["outcome_90"],
        "advance": {"home": advancement["home"], "away": advancement["away"]},
        "shootout_probability": advancement["shootout_probability"],
        "events": events,
        "confidence": "medium" if score_bundle.selected_model != "smoothed_baseline" else "low",
        "warnings": [
            "Prediksi menggambarkan 90 menit dan bukan kepastian hasil.",
            "Peluang penalti per tim dibagi 50/50 karena sampel shootout terlalu kecil.",
            "Red card dan VAR memakai rate tersmoothing dari masing-masing 13 kejadian.",
            "Sel 7+ pada matriks menggabungkan seluruh skor tujuh atau lebih.",
        ],
    }


def run_training(
    data_dir: Path | str = DATA_DIR,
    artifact_dir: Path | str = ARTIFACT_DIR,
    save_models: bool = True,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Jalankan seluruh pipeline deterministik dan tulis artifact publik yang aman."""

    np.random.seed(RANDOM_SEED)
    raw = load_raw_data(data_dir)
    match_features = build_match_features(raw)
    event_frame = build_event_frame(match_features, raw)
    score_bundle = train_score_model(match_features)
    count_bundles = train_count_models(event_frame)
    possession_bundle = train_possession_model(event_frame)
    rare_rates = smoothed_rare_event_rates(event_frame, raw["events"])
    semifinals = match_features[
        match_features["match_id"].isin(SEMIFINAL_MATCH_IDS)
    ].sort_values("match_id")

    completed = match_features[match_features["status"] == "Completed"]
    predictions = {
        "metadata": {
            "generated_for": "Piala Dunia 2026 - semifinal",
            "random_seed": RANDOM_SEED,
            "data_cutoff": str(completed["date"].max().date()),
            "score_model": score_bundle.selected_model,
            "score_matrix_bins": ["0", "1", "2", "3", "4", "5", "6", "7+"],
            "training_scope": "92 pertandingan Regular untuk target skor 90 menit",
        },
        "matches": [
            _match_prediction(
                row,
                score_bundle,
                count_bundles,
                possession_bundle,
                rare_rates,
            )
            for _, row in semifinals.iterrows()
        ],
    }
    evaluation = {
        "random_seed": RANDOM_SEED,
        "data_cutoff": str(completed["date"].max().date()),
        "sample_size_90_minutes": 92,
        "completed_matches_available": int(len(completed)),
        "excluded_from_score_target": {
            "AET": int((completed["result_type"] == "AET").sum()),
            "Penalties": int((completed["result_type"] == "Penalties").sum()),
        },
        "baseline": "Smoothed tournament-wide home/away scoring rate",
        "score": score_bundle.evaluation,
        "events": {
            name: bundle.evaluation for name, bundle in count_bundles.items()
        },
        "possession": possession_bundle.evaluation,
        "rare_events": {
            **rare_rates,
            "confidence": "low",
            "method": "Beta smoothing; tidak ada estimasi kemampuan individual tim.",
        },
        "versions": {
            "python": platform.python_version(),
            "numpy": version("numpy"),
            "pandas": version("pandas"),
            "scikit_learn": version("scikit-learn"),
            "statsmodels": version("statsmodels"),
        },
        "limitations": [
            "Hanya satu turnamen sintetis/terbatas dengan 92 label skor 90 menit.",
            "Fitur form awal turnamen memakai prior netral karena tidak ada histori sebelum cutoff.",
            "Statistik laga AET/penalti dinormalisasi ke ekuivalen 90 menit untuk rolling form.",
            "Tidak ada model pemain individual atau kekuatan penalti per tim pada versi pertama.",
        ],
    }
    validate_artifacts(predictions, evaluation)

    output = Path(artifact_dir)
    output.mkdir(parents=True, exist_ok=True)
    (output / "predictions.json").write_text(
        json.dumps(predictions, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    (output / "evaluation.json").write_text(
        json.dumps(evaluation, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    metric_rows = [
        {
            "target": "score_90",
            "model": name,
            **metrics,
        }
        for name, metrics in score_bundle.evaluation["aggregate"].items()
    ]
    metric_rows.extend(
        {
            "target": target,
            "model": model,
            "predictive_nll": value,
        }
        for target, bundle in count_bundles.items()
        for model, value in bundle.evaluation["aggregate_nll"].items()
    )
    pd.DataFrame(metric_rows).to_csv(output / "metrics_summary.csv", index=False)
    if save_models:
        model_dir = output / "models"
        model_dir.mkdir(parents=True, exist_ok=True)
        joblib.dump(
            {
                "score": score_bundle,
                "events": count_bundles,
                "possession": possession_bundle,
                "rare_events": rare_rates,
            },
            model_dir / "probabilistic_pipeline.joblib",
        )
    return predictions, evaluation

