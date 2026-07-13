"""Konstanta pipeline yang sengaja dijaga kecil dan eksplisit."""

from pathlib import Path

RANDOM_SEED = 20260713
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
ARTIFACT_DIR = PROJECT_ROOT / "artifacts"

SEMIFINAL_MATCH_IDS = (101, 102)
REGULAR_RESULT_TYPE = "Regular"

FORBIDDEN_MODEL_COLUMNS = {
    "home_score",
    "away_score",
    "result_type",
    "home_xg",
    "away_xg",
    "match_result",
    "home_team_id",
    "away_team_id",
    "home_team_name",
    "away_team_name",
    "match_id",
    "venue_id",
    "referee_id",
    "stage_id",
}

ROLLING_DEFAULTS = {
    "goals_for": 1.35,
    "goals_against": 1.35,
    "xg_for": 1.35,
    "xg_against": 1.35,
    "possession": 50.0,
    "shots": 12.0,
    "shots_on_target": 4.2,
    "corners": 4.5,
    "fouls": 11.0,
    "offsides": 1.6,
    "saves": 3.2,
    "yellow_cards": 1.25,
    "red_cards": 0.07,
}

