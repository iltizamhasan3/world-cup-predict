"""Entry point dashboard lokal World Cup Predict."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from src.dashboard.data_access import load_dashboard_data, load_json, raw_data_available
from src.dashboard.pages import (
    artifact_missing,
    render_evaluation,
    render_players,
    render_prediction,
    render_teams,
)
from src.dashboard.styles import dashboard_css

ROOT = Path(__file__).resolve().parent
ARTIFACT_DIR = ROOT / "artifacts"
DATA_DIR = ROOT / "data"

st.set_page_config(
    page_title="World Cup Predict",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="collapsed",
)
st.markdown(dashboard_css(ROOT), unsafe_allow_html=True)

with st.container(key="top-navigation"):
    st.markdown(
        """
        <div class="brand-lockup">
          <span class="brand-mark">WCP</span>
          <span class="brand-name">WORLD CUP PREDICT</span>
          <span class="brand-meta">MODEL ROOM · 2026</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    page = st.radio(
        "Navigasi",
        ("Prediksi", "Tim", "Pemain", "Evaluasi"),
        horizontal=True,
        label_visibility="collapsed",
    )

predictions_path = ARTIFACT_DIR / "predictions.json"
evaluation_path = ARTIFACT_DIR / "evaluation.json"
predictions = load_json(predictions_path) if predictions_path.exists() else None
evaluation = load_json(evaluation_path) if evaluation_path.exists() else None

raw = None
if page in {"Tim", "Pemain"} and raw_data_available(DATA_DIR):
    raw = load_dashboard_data(DATA_DIR)

if page == "Prediksi":
    if predictions is None:
        artifact_missing(predictions_path)
    else:
        render_prediction(predictions)
elif page == "Tim":
    render_teams(raw, DATA_DIR)
elif page == "Pemain":
    render_players(raw, DATA_DIR)
else:
    if evaluation is None:
        artifact_missing(evaluation_path)
    else:
        render_evaluation(evaluation)

st.markdown(
    """
    <footer class="site-footer">
      <span>WORLD CUP PREDICT</span>
      <span>90 MENIT · EXTRA TIME · SHOOTOUT · EVENT DISTRIBUTIONS</span>
      <span>LOCAL-FIRST / DATA CUTOFF 12.07.2026</span>
    </footer>
    """,
    unsafe_allow_html=True,
)
