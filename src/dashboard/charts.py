"""Plotly figures dengan token warna yang konsisten."""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go

CANVAS = "#181818"
ELEVATED = "#303030"
ROSSO = "#DA291C"
INK = "#FFFFFF"
BODY = "#969696"
MUTED = "#666666"


def _layout(fig: go.Figure, height: int = 360) -> go.Figure:
    fig.update_layout(
        height=height,
        margin=dict(l=18, r=18, t=48, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor=CANVAS,
        font=dict(family="FerrariSans, WC Sans, sans-serif", color=INK),
        hoverlabel=dict(font_family="WC Data, monospace"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    fig.update_xaxes(gridcolor=ELEVATED, zerolinecolor=ELEVATED, linecolor=ELEVATED)
    fig.update_yaxes(gridcolor=ELEVATED, zerolinecolor=ELEVATED, linecolor=ELEVATED)
    return fig


def score_heatmap(match: dict) -> go.Figure:
    score = match["score_90"]
    matrix = np.asarray(score["matrix"], dtype=float) * 100.0
    labels = score["labels"]
    fig = go.Figure(
        go.Heatmap(
            z=matrix,
            x=labels,
            y=labels,
            colorscale=[
                [0.0, CANVAS],
                [0.35, ELEVATED],
                [0.72, "#781A14"],
                [1.0, ROSSO],
            ],
            text=np.vectorize(lambda value: f"{value:.1f}%")(matrix),
            texttemplate="%{text}",
            hovertemplate=(
                f"{match['home_team']} %{{y}} - %{{x}} {match['away_team']}<br>"
                "Probabilitas %{z:.2f}%<extra></extra>"
            ),
            colorbar=dict(
                title="Peluang",
                ticksuffix="%",
                thickness=8,
                outlinewidth=0,
                tickfont=dict(color=BODY),
            ),
        )
    )
    fig.update_xaxes(title=f"Gol {match['away_team']}", side="top", fixedrange=True)
    fig.update_yaxes(title=f"Gol {match['home_team']}", autorange="reversed", fixedrange=True)
    return _layout(fig, 475)


def outcome_chart(match: dict) -> go.Figure:
    outcome = match["outcome_90"]
    labels = [match["home_team"], "Seri", match["away_team"]]
    values = [outcome["home_win"], outcome["draw"], outcome["away_win"]]
    fig = go.Figure(
        go.Bar(
            x=np.asarray(values) * 100,
            y=labels,
            orientation="h",
            marker_color=[INK, MUTED, ROSSO],
            text=[f"{value:.1%}" for value in values],
            textposition="inside",
            hovertemplate="%{y}: %{x:.1f}%<extra></extra>",
        )
    )
    fig.update_xaxes(range=[0, 100], ticksuffix="%", title="Probabilitas 90 menit")
    fig.update_yaxes(autorange="reversed")
    return _layout(fig, 250)


def event_distribution_chart(match: dict, event_name: str) -> go.Figure:
    event = match["events"][event_name]
    fig = go.Figure()
    for side, label, color in (
        ("home", match["home_team"], INK),
        ("away", match["away_team"], ROSSO),
        ("total", "Total laga", BODY),
    ):
        distribution = event[side]
        fig.add_trace(
            go.Scatter(
                x=distribution["labels"],
                y=np.asarray(distribution["probabilities"]) * 100,
                mode="lines+markers",
                name=label,
                line=dict(
                    color=color,
                    width=3 if side == "away" else 2,
                    dash="dot" if side == "total" else "solid",
                ),
                marker=dict(size=6),
                hovertemplate="%{x}: %{y:.1f}%<extra>%{fullData.name}</extra>",
            )
        )
    fig.update_xaxes(title="Jumlah / rentang", fixedrange=True)
    fig.update_yaxes(title="Probabilitas", ticksuffix="%", rangemode="tozero", fixedrange=True)
    return _layout(fig, 360)


def comparison_chart(summary: pd.DataFrame, teams: list[str]) -> go.Figure:
    selected = summary[summary["team"].isin(teams)].copy()
    metrics = {
        "Menang per laga": selected["wins"] / selected["played"].clip(lower=1),
        "Gol per laga": selected["goals_for"] / selected["played"].clip(lower=1),
        "xG per laga": selected["xg_for"] / selected["played"].clip(lower=1),
        "Shot tepat sasaran/laga": selected["shots_on_target"] / selected["played"].clip(lower=1),
        "Possession / 50": selected["avg_possession"] / 50.0,
    }
    fig = go.Figure()
    colors = [ROSSO, INK, BODY, MUTED]
    patterns = ["", "/", "x", "."]
    for index, row in selected.reset_index(drop=True).iterrows():
        fig.add_trace(
            go.Bar(
                name=row["team"],
                x=list(metrics),
                y=[float(series.iloc[index]) for series in metrics.values()],
                marker=dict(
                    color=colors[index % len(colors)],
                    pattern_shape=patterns[index % len(patterns)],
                ),
                hovertemplate="%{x}: %{y:.2f}<extra>%{fullData.name}</extra>",
            )
        )
    fig.update_layout(barmode="group")
    return _layout(fig, 390)


def fold_evaluation_chart(evaluation: dict) -> go.Figure:
    folds = evaluation["score"]["folds"]
    fig = go.Figure()
    for model, color in (
        ("smoothed_baseline", MUTED),
        ("regularized_poisson", INK),
        ("poisson_dc_blend", ROSSO),
        ("dixon_coles", BODY),
    ):
        fig.add_trace(
            go.Scatter(
                x=[fold["fold"] for fold in folds],
                y=[fold["models"][model]["exact_score_log_loss"] for fold in folds],
                mode="lines+markers",
                name=model.replace("_", " "),
                line=dict(
                    color=color,
                    width=3 if model == "poisson_dc_blend" else 2,
                    dash="dash" if model == "smoothed_baseline" else "solid",
                ),
            )
        )
    fig.update_xaxes(title="Chronological fold", dtick=1, fixedrange=True)
    fig.update_yaxes(title="Exact-score log loss (lebih rendah lebih baik)", fixedrange=True)
    return _layout(fig, 380)
