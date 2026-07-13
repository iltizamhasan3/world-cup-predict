"""Loader artifact dan agregasi statistik untuk halaman tim/pemain."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


def load_json(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(path)
    return json.loads(path.read_text(encoding="utf-8"))


def raw_data_available(data_dir: Path) -> bool:
    required = (
        "matches.csv",
        "teams.csv",
        "match_team_stats.csv",
        "match_events.csv",
        "squads_and_players.csv",
        "player_stats.csv",
    )
    return all((data_dir / name).exists() for name in required)


def load_dashboard_data(data_dir: Path) -> dict[str, pd.DataFrame]:
    if not raw_data_available(data_dir):
        missing = [
            name
            for name in (
                "matches.csv",
                "teams.csv",
                "match_team_stats.csv",
                "match_events.csv",
                "squads_and_players.csv",
                "player_stats.csv",
            )
            if not (data_dir / name).exists()
        ]
        raise FileNotFoundError(", ".join(missing))
    return {
        "matches": pd.read_csv(data_dir / "matches.csv"),
        "teams": pd.read_csv(data_dir / "teams.csv"),
        "stats": pd.read_csv(data_dir / "match_team_stats.csv"),
        "events": pd.read_csv(data_dir / "match_events.csv"),
        "squads": pd.read_csv(data_dir / "squads_and_players.csv"),
        "players": pd.read_csv(data_dir / "player_stats.csv"),
    }


def build_team_summary(raw: dict[str, pd.DataFrame]) -> pd.DataFrame:
    teams = raw["teams"].copy()
    matches = raw["matches"].query("status == 'Completed'").copy()
    stats = raw["stats"].copy()
    squads = raw["squads"].groupby("team_id", as_index=False).agg(
        squad_value_eur=("market_value_eur", "sum"),
        squad_avg_age=(
            "date_of_birth",
            lambda values: (
                pd.Timestamp("2026-06-11") - pd.to_datetime(values)
            ).dt.days.mean()
            / 365.2425,
        ),
        squad_caps=("caps", "sum"),
    )
    event_counts = (
        raw["events"]
        .query("event_type in ['Yellow Card', 'Red Card']")
        .pivot_table(
            index="team_id", columns="event_type", values="event_id", aggfunc="count", fill_value=0
        )
        .reset_index()
        .rename(columns={"Yellow Card": "yellow_cards", "Red Card": "red_cards"})
    )
    records = []
    for team in teams.itertuples(index=False):
        team_id = int(team.team_id)
        team_matches = matches[
            (matches["home_team_id"] == team_id) | (matches["away_team_id"] == team_id)
        ].sort_values(["date", "kickoff_time_utc"])
        wins = draws = losses = goals_for = goals_against = 0
        xg_for = xg_against = 0.0
        for match in team_matches.itertuples(index=False):
            is_home = int(match.home_team_id) == team_id
            scored = int(match.home_score if is_home else match.away_score)
            conceded = int(match.away_score if is_home else match.home_score)
            goals_for += scored
            goals_against += conceded
            xg_for += float(match.home_xg if is_home else match.away_xg)
            xg_against += float(match.away_xg if is_home else match.home_xg)
            if scored > conceded:
                wins += 1
            elif scored == conceded:
                draws += 1
            else:
                losses += 1
        team_stats = stats[stats["team_id"] == team_id]
        records.append(
            {
                "team_id": team_id,
                "team": team.team_name,
                "code": team.fifa_code,
                "group": team.group_letter,
                "confederation": team.confederation,
                "ranking": int(team.fifa_ranking_pre_tournament),
                "elo": int(team.elo_rating),
                "played": len(team_matches),
                "wins": wins,
                "draws": draws,
                "losses": losses,
                "goals_for": goals_for,
                "goals_against": goals_against,
                "xg_for": xg_for,
                "xg_against": xg_against,
                "shots": float(team_stats["total_shots"].sum()),
                "shots_on_target": float(team_stats["shots_on_target"].sum()),
                "avg_possession": float(team_stats["possession_pct"].mean()),
                "corners": float(team_stats["corners"].sum()),
                "fouls": float(team_stats["fouls"].sum()),
                "offsides": float(team_stats["offsides"].sum()),
                "saves": float(team_stats["saves"].sum()),
            }
        )
    summary = pd.DataFrame(records)
    summary = summary.merge(squads, on="team_id", how="left").merge(
        event_counts, on="team_id", how="left"
    )
    for column in ("yellow_cards", "red_cards"):
        summary[column] = summary[column].fillna(0).astype(int)
    return summary.sort_values(["ranking", "team"]).reset_index(drop=True)


def team_form(raw: dict[str, pd.DataFrame], team_id: int) -> pd.DataFrame:
    matches = raw["matches"].query("status == 'Completed'").copy()
    teams = raw["teams"].set_index("team_id")["team_name"].to_dict()
    selected = matches[
        (matches["home_team_id"] == team_id) | (matches["away_team_id"] == team_id)
    ].sort_values(["date", "kickoff_time_utc"]).tail(5)
    records = []
    for match in selected.itertuples(index=False):
        is_home = int(match.home_team_id) == team_id
        opponent_id = int(match.away_team_id if is_home else match.home_team_id)
        scored = int(match.home_score if is_home else match.away_score)
        conceded = int(match.away_score if is_home else match.home_score)
        result = "M" if scored > conceded else "S" if scored == conceded else "K"
        records.append(
            {
                "tanggal": match.date,
                "lawan": teams[opponent_id],
                "venue": "Home" if is_home else "Away",
                "skor": f"{scored}-{conceded}",
                "hasil": result,
                "gol": scored,
                "kebobolan": conceded,
            }
        )
    return pd.DataFrame(records)


def build_player_frame(raw: dict[str, pd.DataFrame]) -> pd.DataFrame:
    squads = raw["squads"].copy()
    stats = raw["players"].copy()
    teams = raw["teams"][["team_id", "team_name", "fifa_code"]]
    frame = squads.merge(
        stats,
        on=["player_id", "team_id", "player_name", "position"],
        how="left",
        suffixes=("_career", "_tournament"),
    ).merge(teams, on="team_id", how="left")
    frame["date_of_birth"] = pd.to_datetime(frame["date_of_birth"])
    frame["age"] = (
        pd.Timestamp("2026-07-13") - frame["date_of_birth"]
    ).dt.days / 365.2425
    frame = frame.rename(
        columns={
            "goals_career": "international_goals",
            "goals_tournament": "tournament_goals",
        }
    )
    numeric = [
        "matches_played",
        "matches_started",
        "minutes_played",
        "tournament_goals",
        "assists",
        "yellow_cards",
        "red_cards",
        "clean_sheets",
        "saves",
        "goals_conceded",
    ]
    frame[numeric] = frame[numeric].fillna(0)
    return frame.sort_values(["team_name", "position", "player_name"]).reset_index(drop=True)


def format_eur(value: float) -> str:
    if pd.isna(value):
        return "Tidak tersedia"
    if value >= 1_000_000_000:
        return f"EUR {value / 1_000_000_000:.2f} miliar"
    return f"EUR {value / 1_000_000:.1f} juta"

