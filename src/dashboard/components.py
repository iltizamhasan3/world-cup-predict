"""Controlled HTML surfaces that avoid inherited Streamlit widget styling."""

from __future__ import annotations

from html import escape
from typing import Iterable

import pandas as pd
import streamlit as st


def _display(value: object) -> str:
    if pd.isna(value):
        return "—"
    if isinstance(value, float):
        return f"{value:,.2f}".rstrip("0").rstrip(".")
    return str(value)


def telemetry_specs(
    items: Iterable[tuple[str, object, str | None, bool]],
    *,
    key: str | None = None,
) -> None:
    """Render sharp, high-contrast spec cells independent of st.metric."""

    cells = []
    for label, value, note, accent in items:
        accent_class = " is-accent" if accent else ""
        note_html = f'<span class="spec-note">{escape(note)}</span>' if note else ""
        cells.append(
            f'<div class="telemetry-spec{accent_class}">'
            f'<span class="spec-label">{escape(label)}</span>'
            f'<strong class="spec-value">{escape(_display(value))}</strong>'
            f"{note_html}</div>"
        )
    html = f'<div class="telemetry-spec-grid">{"".join(cells)}</div>'
    if key:
        with st.container(key=key):
            st.markdown(html, unsafe_allow_html=True)
    else:
        st.markdown(html, unsafe_allow_html=True)


def telemetry_table(
    frame: pd.DataFrame,
    *,
    max_rows: int | None = None,
    empty_message: str = "Tidak ada data.",
) -> None:
    """Render a dark editorial table with explicit text contrast."""

    if frame.empty:
        st.markdown(
            f'<div class="telemetry-empty">{escape(empty_message)}</div>',
            unsafe_allow_html=True,
        )
        return
    shown = frame.head(max_rows) if max_rows else frame
    header = "".join(f"<th>{escape(str(column))}</th>" for column in shown.columns)
    body_rows = []
    for _, row in shown.iterrows():
        cells = "".join(f"<td>{escape(_display(value))}</td>" for value in row)
        body_rows.append(f"<tr>{cells}</tr>")
    overflow = ""
    if max_rows and len(frame) > max_rows:
        overflow = (
            f'<div class="table-overflow">Menampilkan {max_rows} dari {len(frame):,} baris. '
            "Gunakan filter untuk mempersempit hasil.</div>"
        )
    html = (
        '<div class="telemetry-table-wrap" role="region" '
        'aria-label="Tabel data" tabindex="0">'
        '<table class="telemetry-table">'
        f"<thead><tr>{header}</tr></thead>"
        f"<tbody>{''.join(body_rows)}</tbody>"
        f"</table></div>{overflow}"
    )
    st.markdown(html, unsafe_allow_html=True)


def telemetry_label(text: str, detail: str | None = None) -> None:
    detail_html = f"<span>{escape(detail)}</span>" if detail else ""
    st.markdown(
        f'<div class="telemetry-label"><strong>{escape(text)}</strong>{detail_html}</div>',
        unsafe_allow_html=True,
    )
