"""Pemuatan data dan rekonstruksi fitur pre-match tanpa melihat masa depan."""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

from .config import DATA_DIR, FORBIDDEN_MODEL_COLUMNS, ROLLING_DEFAULTS

REQUIRED_FILES = {
    "matches": "matches.csv",
    "teams": "teams.csv",
    "stages": "tournament_stages.csv",
    "venues": "venues.csv",
    "referees": "referees.csv",
    "squads": "squads_and_players.csv",
    "stats": "match_team_stats.csv",
    "events": "match_events.csv",
    "players": "player_stats.csv",
}

CONTEXT_FEATURES = [
    "stage_order",
    "is_knockout",
    "venue_capacity",
    "venue_elevation",
    "referee_avg_cards",
    "home_is_host",
    "away_is_host",
]

STATIC_SUFFIXES = [
    "fifa_rank",
    "elo",
    "squad_avg_age",
    "squad_total_caps",
    "squad_total_value_log",
    "squad_avg_value_log",
    "rest_days",
]

FORM_SUFFIXES = [f"form_{name}" for name in ROLLING_DEFAULTS]

FEATURE_COLUMNS = (
    CONTEXT_FEATURES
    + [f"home_{name}" for name in STATIC_SUFFIXES + FORM_SUFFIXES]
    + [f"away_{name}" for name in STATIC_SUFFIXES + FORM_SUFFIXES]
)

ORIENTED_FEATURE_COLUMNS = (
    ["is_home"]
    + CONTEXT_FEATURES
    + [f"team_{name}" for name in STATIC_SUFFIXES + FORM_SUFFIXES]
    + [f"opponent_{name}" for name in STATIC_SUFFIXES + FORM_SUFFIXES]
)

EVENT_TARGET_COLUMNS = [
    "shots",
    "shots_on_target",
    "corners",
    "fouls",
    "offsides",
    "yellow_cards",
    "saves",
    "red_cards",
]


@dataclass
class TeamHistory:
    """State yang hanya diperbarui setelah sebuah pertandingan selesai."""

    elo: float
    last_date: pd.Timestamp | None = None
    values: dict[str, deque[float]] = field(
        default_factory=lambda: {
            name: deque(maxlen=5) for name in ROLLING_DEFAULTS
        }
    )

    def mean(self, name: str) -> float:
        history = self.values[name]
        return float(np.mean(history)) if history else float(ROLLING_DEFAULTS[name])


def load_raw_data(data_dir: Path | str = DATA_DIR) -> dict[str, pd.DataFrame]:
    """Muat tabel sumber dan beri pesan yang dapat ditindaklanjuti bila tidak ada."""

    root = Path(data_dir)
    missing = [filename for filename in REQUIRED_FILES.values() if not (root / filename).exists()]
    if missing:
        names = ", ".join(sorted(missing))
        raise FileNotFoundError(
            f"Raw data belum lengkap di {root}. File yang belum ada: {names}."
        )
    return {
        key: pd.read_csv(root / filename)
        for key, filename in REQUIRED_FILES.items()
    }


def _squad_summary(squads: pd.DataFrame) -> pd.DataFrame:
    frame = squads.copy()
    frame["date_of_birth"] = pd.to_datetime(frame["date_of_birth"], errors="coerce")
    cutoff = pd.Timestamp("2026-06-11")
    frame["age"] = (cutoff - frame["date_of_birth"]).dt.days / 365.2425
    summary = frame.groupby("team_id", as_index=False).agg(
        squad_avg_age=("age", "mean"),
        squad_total_caps=("caps", "sum"),
        squad_total_value=("market_value_eur", "sum"),
        squad_avg_value=("market_value_eur", "mean"),
    )
    summary["squad_total_value_log"] = np.log1p(summary["squad_total_value"])
    summary["squad_avg_value_log"] = np.log1p(summary["squad_avg_value"])
    return summary.drop(columns=["squad_total_value", "squad_avg_value"])


def _event_counts(events: pd.DataFrame) -> dict[tuple[int, int], dict[str, float]]:
    mapping: dict[tuple[int, int], dict[str, float]] = defaultdict(
        lambda: {"yellow_cards": 0.0, "red_cards": 0.0}
    )
    for row in events.itertuples(index=False):
        if pd.isna(row.team_id):
            continue
        key = (int(row.match_id), int(row.team_id))
        if row.event_type == "Yellow Card":
            mapping[key]["yellow_cards"] += 1.0
        elif row.event_type == "Red Card":
            mapping[key]["red_cards"] += 1.0
    return mapping


def _team_static(teams: pd.DataFrame, squads: pd.DataFrame) -> pd.DataFrame:
    frame = teams.merge(_squad_summary(squads), on="team_id", how="left")
    frame = frame.rename(columns={"fifa_ranking_pre_tournament": "fifa_rank"})
    defaults = {
        "squad_avg_age": frame["squad_avg_age"].median(),
        "squad_total_caps": frame["squad_total_caps"].median(),
        "squad_total_value_log": frame["squad_total_value_log"].median(),
        "squad_avg_value_log": frame["squad_avg_value_log"].median(),
    }
    return frame.fillna(defaults).set_index("team_id")


def _rest_days(history: TeamHistory, date: pd.Timestamp) -> float:
    if history.last_date is None:
        return 7.0
    return float(np.clip((date - history.last_date).days, 2, 30))


def _side_features(
    prefix: str,
    team_id: int,
    date: pd.Timestamp,
    static: pd.DataFrame,
    history: TeamHistory,
) -> dict[str, float]:
    team = static.loc[team_id]
    values = {
        f"{prefix}_fifa_rank": float(team["fifa_rank"]),
        f"{prefix}_elo": float(history.elo),
        f"{prefix}_squad_avg_age": float(team["squad_avg_age"]),
        f"{prefix}_squad_total_caps": float(team["squad_total_caps"]),
        f"{prefix}_squad_total_value_log": float(team["squad_total_value_log"]),
        f"{prefix}_squad_avg_value_log": float(team["squad_avg_value_log"]),
        f"{prefix}_rest_days": _rest_days(history, date),
    }
    values.update(
        {f"{prefix}_form_{name}": history.mean(name) for name in ROLLING_DEFAULTS}
    )
    return values


def _update_elo(home: TeamHistory, away: TeamHistory, home_score: float, away_score: float) -> None:
    expected = 1.0 / (1.0 + 10.0 ** ((away.elo - home.elo) / 400.0))
    actual = 1.0 if home_score > away_score else 0.0 if home_score < away_score else 0.5
    change = 24.0 * (actual - expected)
    home.elo += change
    away.elo -= change


def _observed_values(
    match: pd.Series,
    team_id: int,
    opponent_id: int,
    is_home: bool,
    stats: dict[tuple[int, int], dict[str, float]],
    event_counts: dict[tuple[int, int], dict[str, float]],
) -> dict[str, float]:
    match_id = int(match["match_id"])
    side = stats.get((match_id, team_id), {})
    opponent = stats.get((match_id, opponent_id), {})
    goals_for = float(match["home_score"] if is_home else match["away_score"])
    goals_against = float(match["away_score"] if is_home else match["home_score"])
    xg_for = float(match["home_xg"] if is_home else match["away_xg"])
    xg_against = float(match["away_xg"] if is_home else match["home_xg"])
    factor = 0.75 if match["result_type"] in {"AET", "Penalties"} else 1.0
    counts = event_counts[(match_id, team_id)]
    return {
        "goals_for": goals_for * factor,
        "goals_against": goals_against * factor,
        "xg_for": xg_for * factor,
        "xg_against": xg_against * factor,
        "possession": float(side.get("possession_pct", ROLLING_DEFAULTS["possession"])),
        "shots": float(side.get("total_shots", ROLLING_DEFAULTS["shots"])) * factor,
        "shots_on_target": float(side.get("shots_on_target", ROLLING_DEFAULTS["shots_on_target"])) * factor,
        "corners": float(side.get("corners", ROLLING_DEFAULTS["corners"])) * factor,
        "fouls": float(side.get("fouls", ROLLING_DEFAULTS["fouls"])) * factor,
        "offsides": float(side.get("offsides", ROLLING_DEFAULTS["offsides"])) * factor,
        "saves": float(side.get("saves", ROLLING_DEFAULTS["saves"])) * factor,
        "yellow_cards": counts["yellow_cards"] * factor,
        "red_cards": counts["red_cards"] * factor,
    }


def build_match_features(raw: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Bangun satu baris pre-match per pertandingan dalam urutan kickoff."""

    matches = raw["matches"].copy()
    matches["date"] = pd.to_datetime(matches["date"])
    matches["kickoff"] = pd.to_datetime(
        matches["date"].dt.strftime("%Y-%m-%d")
        + " "
        + matches["kickoff_time_utc"].fillna("00:00")
    )
    matches = matches.dropna(subset=["home_team_id", "away_team_id"]).copy()
    matches[["home_team_id", "away_team_id"]] = matches[
        ["home_team_id", "away_team_id"]
    ].astype(int)

    stages = raw["stages"].copy()
    stages["stage_order"] = stages["stage_id"].rank(method="dense").astype(int)
    matches = matches.merge(stages, on="stage_id", how="left")
    matches = matches.merge(raw["venues"], on="venue_id", how="left")
    matches = matches.merge(
        raw["referees"][["referee_id", "avg_cards_per_game"]],
        on="referee_id",
        how="left",
    )
    static = _team_static(raw["teams"], raw["squads"])
    stats_frame = raw["stats"].copy()
    stats = {
        (int(row.match_id), int(row.team_id)): row._asdict()
        for row in stats_frame.itertuples(index=False)
    }
    event_counts = _event_counts(raw["events"])
    histories = {
        int(team_id): TeamHistory(float(team["elo_rating"]))
        for team_id, team in static.iterrows()
    }

    records: list[dict[str, object]] = []
    team_names = static["team_name"].to_dict()
    team_codes = static["fifa_code"].to_dict()
    referee_default = float(raw["referees"]["avg_cards_per_game"].median())

    for _, match in matches.sort_values(["kickoff", "match_id"]).iterrows():
        home_id = int(match["home_team_id"])
        away_id = int(match["away_team_id"])
        home_history = histories[home_id]
        away_history = histories[away_id]
        country = str(match.get("country", ""))
        record: dict[str, object] = {
            "match_id": int(match["match_id"]),
            "date": match["date"],
            "kickoff": match["kickoff"],
            "status": match["status"],
            "result_type": match["result_type"],
            "home_team_id": home_id,
            "away_team_id": away_id,
            "home_team_name": team_names[home_id],
            "away_team_name": team_names[away_id],
            "stage_name": match["stage_name"],
            "venue_name": match["stadium_name"],
            "venue_city": match["city"],
            "home_score": match["home_score"],
            "away_score": match["away_score"],
            "stage_order": float(match["stage_order"]),
            "is_knockout": float(str(match["is_knockout"]).lower() == "true" or bool(match["is_knockout"])),
            "venue_capacity": float(match["capacity"]),
            "venue_elevation": float(match["elevation_meters"]),
            "referee_avg_cards": float(match.get("avg_cards_per_game", referee_default) or referee_default),
            "home_is_host": float(team_codes[home_id] == country),
            "away_is_host": float(team_codes[away_id] == country),
        }
        record.update(_side_features("home", home_id, match["date"], static, home_history))
        record.update(_side_features("away", away_id, match["date"], static, away_history))
        records.append(record)

        if match["status"] == "Completed" and pd.notna(match["home_score"]):
            home_values = _observed_values(
                match, home_id, away_id, True, stats, event_counts
            )
            away_values = _observed_values(
                match, away_id, home_id, False, stats, event_counts
            )
            for name, value in home_values.items():
                home_history.values[name].append(value)
            for name, value in away_values.items():
                away_history.values[name].append(value)
            home_history.last_date = match["date"]
            away_history.last_date = match["date"]
            _update_elo(
                home_history,
                away_history,
                float(match["home_score"]),
                float(match["away_score"]),
            )

    frame = pd.DataFrame.from_records(records).sort_values(["kickoff", "match_id"])
    frame[FEATURE_COLUMNS] = frame[FEATURE_COLUMNS].replace([np.inf, -np.inf], np.nan)
    frame[FEATURE_COLUMNS] = frame[FEATURE_COLUMNS].fillna(frame[FEATURE_COLUMNS].median())
    assert not (set(FEATURE_COLUMNS) & FORBIDDEN_MODEL_COLUMNS)
    return frame.reset_index(drop=True)


def build_event_frame(
    match_features: pd.DataFrame, raw: dict[str, pd.DataFrame]
) -> pd.DataFrame:
    """Ubah pertandingan selesai menjadi dua baris berorientasi tim."""

    stats = raw["stats"].copy()
    stat_lookup = stats.set_index(["match_id", "team_id"]).to_dict("index")
    event_counts = _event_counts(raw["events"])
    records: list[dict[str, object]] = []
    for row in match_features.itertuples(index=False):
        if row.status != "Completed":
            continue
        for side, opponent in (("home", "away"), ("away", "home")):
            team_id = int(getattr(row, f"{side}_team_id"))
            target = stat_lookup[(int(row.match_id), team_id)]
            record: dict[str, object] = {
                "match_id": int(row.match_id),
                "date": row.date,
                "team_id": team_id,
                "is_home": float(side == "home"),
                **{name: float(getattr(row, name)) for name in CONTEXT_FEATURES},
            }
            for suffix in STATIC_SUFFIXES + FORM_SUFFIXES:
                record[f"team_{suffix}"] = float(getattr(row, f"{side}_{suffix}"))
                record[f"opponent_{suffix}"] = float(
                    getattr(row, f"{opponent}_{suffix}")
                )
            record.update(
                {
                    "shots": float(target["total_shots"]),
                    "shots_on_target": float(target["shots_on_target"]),
                    "corners": float(target["corners"]),
                    "fouls": float(target["fouls"]),
                    "offsides": float(target["offsides"]),
                    "saves": float(target["saves"]),
                    "possession": float(target["possession_pct"]),
                    **event_counts[(int(row.match_id), team_id)],
                }
            )
            records.append(record)
    return pd.DataFrame.from_records(records).sort_values(
        ["date", "match_id", "is_home"], ascending=[True, True, False]
    ).reset_index(drop=True)


def orient_match(row: pd.Series, side: str) -> pd.DataFrame:
    """Bentuk fitur satu tim untuk model event tanpa memakai identitas."""

    if side not in {"home", "away"}:
        raise ValueError("side harus 'home' atau 'away'")
    opponent = "away" if side == "home" else "home"
    record = {
        "is_home": float(side == "home"),
        **{name: float(row[name]) for name in CONTEXT_FEATURES},
    }
    for suffix in STATIC_SUFFIXES + FORM_SUFFIXES:
        record[f"team_{suffix}"] = float(row[f"{side}_{suffix}"])
        record[f"opponent_{suffix}"] = float(row[f"{opponent}_{suffix}"])
    return pd.DataFrame([record], columns=ORIENTED_FEATURE_COLUMNS)


def chronological_folds(
    frame: pd.DataFrame, n_splits: int = 3, minimum_train: int = 44
) -> Iterable[tuple[np.ndarray, np.ndarray]]:
    """Expanding-window folds; seluruh tanggal train mendahului validation."""

    ordered = frame.sort_values(["date", "match_id"]).reset_index(drop=True)
    n_rows = len(ordered)
    if n_rows <= minimum_train + n_splits:
        raise ValueError("Sampel terlalu kecil untuk chronological cross-validation.")
    remaining = n_rows - minimum_train
    fold_size = max(1, remaining // n_splits)
    for fold in range(n_splits):
        train_end = minimum_train + fold * fold_size
        valid_end = n_rows if fold == n_splits - 1 else train_end + fold_size
        train = np.arange(0, train_end)
        valid = np.arange(train_end, valid_end)
        if len(valid):
            yield train, valid

