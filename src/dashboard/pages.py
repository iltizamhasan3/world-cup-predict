"""Empat halaman dashboard berbahasa Indonesia."""

from __future__ import annotations

from html import escape
from pathlib import Path

import pandas as pd
import streamlit as st

from .charts import (
    comparison_chart,
    event_distribution_chart,
    fold_evaluation_chart,
    outcome_chart,
    score_heatmap,
)
from .components import telemetry_specs, telemetry_table
from .data_access import (
    build_player_frame,
    build_team_summary,
    format_eur,
    team_form,
)

PLOT_CONFIG = {"displayModeBar": False, "responsive": True}

EVENT_LABELS = {
    "shots": "Shots",
    "shots_on_target": "Shots tepat sasaran",
    "corners": "Corners",
    "fouls": "Foul",
    "offsides": "Offside",
    "yellow_cards": "Kartu kuning",
    "saves": "Saves",
    "possession": "Possession",
    "red_cards": "Kartu merah",
    "var_reviews": "VAR review",
}


def _header(kicker: str, title: str, description: str) -> None:
    st.markdown(
        f"""
        <div class="broadcast-header">
          <div class="broadcast-kicker">{escape(kicker)}</div>
          <h1>{escape(title)}</h1>
          <p>{escape(description)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def artifact_missing(path: Path) -> None:
    _header(
        "Artifact belum tersedia",
        "Jalankan training terlebih dahulu",
        "Dashboard prediksi memerlukan artifact lokal yang sudah melewati pemeriksaan kontrak.",
    )
    st.error(f"File tidak ditemukan: {path}")
    st.code(".venv/bin/jupyter nbconvert --to notebook --execute --inplace notebooks/01_training.ipynb")


def raw_data_missing(data_dir: Path) -> None:
    st.info(
        "Raw CSV tidak tersedia di instalasi ini. Letakkan file sumber lokal di folder "
        f"`{data_dir}` untuk membuka statistik tim dan pemain. File tersebut sengaja tidak dipublikasikan."
    )


def render_prediction(predictions: dict) -> None:
    _header(
        "Model room / Semifinal",
        "Meja analisis 90 menit",
        "Baca matriks skor sebagai rentang kemungkinan, lalu gunakan H/D/A, peluang lolos, dan distribusi event untuk melihat struktur pertandingan.",
    )
    match_options = {
        f"{match['home_team']} vs {match['away_team']}": match
        for match in predictions["matches"]
    }
    selected_label = st.radio(
        "Pilih semifinal",
        options=list(match_options),
        horizontal=True,
        label_visibility="collapsed",
    )
    match = match_options[selected_label]
    st.markdown(
        f"""
        <div class="match-strip">
          <div class="team">{escape(match['home_team'])}</div>
          <div class="versus">VS / 90 MENIT</div>
          <div class="team">{escape(match['away_team'])}</div>
        </div>
        <div class="match-meta">{escape(match['kickoff_utc'])} · {escape(match['venue']['stadium'])} · {escape(match['venue']['city'])}</div>
        """,
        unsafe_allow_html=True,
    )

    home, center, away = st.columns([1.05, 2.35, 1.05], gap="medium")
    with home:
        st.markdown(
            f"""
            <div class="team-panel">
              <div class="name">{escape(match['home_team'])}</div>
              <div class="number">{match['score_90']['expected_goals']['home']:.2f}</div>
              <div class="label">expected goals</div>
              <div class="number">{match['advance']['home']:.1%}</div>
              <div class="label">peluang lolos</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with center:
        st.plotly_chart(
            score_heatmap(match),
            width="stretch",
            config=PLOT_CONFIG,
            key=f"score-{match['match_id']}",
        )
    with away:
        st.markdown(
            f"""
            <div class="team-panel away">
              <div class="name">{escape(match['away_team'])}</div>
              <div class="number">{match['score_90']['expected_goals']['away']:.2f}</div>
              <div class="label">expected goals</div>
              <div class="number">{match['advance']['away']:.1%}</div>
              <div class="label">peluang lolos</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.subheader("Lima skor paling mungkin")
    chips = "".join(
        f"<span class='score-chip'><strong>{escape(item['score'])}</strong>"
        f"<span>{item['probability']:.1%}</span></span>"
        for item in match["score_90"]["top_exact_scores"]
    )
    st.markdown(chips, unsafe_allow_html=True)

    st.markdown('<div class="section-rule"></div>', unsafe_allow_html=True)
    st.subheader("Hasil 90 menit dan jalan menuju final")
    chart_column, metric_column = st.columns([2.2, 1], gap="large")
    with chart_column:
        st.plotly_chart(
            outcome_chart(match),
            width="stretch",
            config=PLOT_CONFIG,
            key=f"outcome-{match['match_id']}",
        )
    with metric_column:
        telemetry_specs(
            (
                (
                    "Masuk adu penalti",
                    f"{match['shootout_probability']:.1%}",
                    "Seri 90 menit × seri setelah simulasi extra time 30 menit",
                    True,
                ),
                (
                    "Confidence",
                    match["confidence"].upper(),
                    "Batas keyakinan model probabilistik",
                    False,
                ),
            )
        )

    st.markdown('<div class="section-rule"></div>', unsafe_allow_html=True)
    st.subheader("Distribusi kejadian pertandingan")
    selected_event_label = st.selectbox(
        "Pilih statistik",
        options=[EVENT_LABELS[name] for name in match["events"]],
    )
    event_name = next(
        name for name, label in EVENT_LABELS.items() if label == selected_event_label
    )
    event = match["events"][event_name]
    suffix = "%" if event_name == "possession" else ""
    event_specs = []
    for side, label in zip(
        ("home", "away", "total"),
        (match["home_team"], match["away_team"], "Total laga"),
        strict=True,
    ):
        low, high = event[side]["interval_80"]
        event_specs.append(
            (
                label,
                f"{event[side]['expected']:.1f}{suffix}",
                f"Interval 80%: {low:g}–{high:g}",
                side == "away",
            )
        )
    telemetry_specs(event_specs)
    st.plotly_chart(
        event_distribution_chart(match, event_name),
        width="stretch",
        config=PLOT_CONFIG,
        key=f"event-{match['match_id']}-{event_name}",
    )
    confidence = event.get("confidence", "low")
    st.caption(f"Model: {event.get('model', 'tidak tersedia')} · confidence {confidence}")
    if confidence == "low":
        st.markdown(
            '<span class="confidence-low">INTERPRETASIKAN DENGAN HATI-HATI</span>',
            unsafe_allow_html=True,
        )

    with st.expander("Batas interpretasi pertandingan ini"):
        for warning in match["warnings"]:
            st.write(f"- {warning}")


def render_teams(raw: dict[str, pd.DataFrame] | None, data_dir: Path) -> None:
    _header(
        "48 tim / Satu turnamen",
        "Ruang statistik tim",
        "Bandingkan performa turnamen, kekuatan pra-turnamen, form lima laga, serta indikator disiplin untuk seluruh peserta.",
    )
    if raw is None:
        raw_data_missing(data_dir)
        return
    summary = build_team_summary(raw)
    focus = [name for name in ("France", "Spain", "England", "Argentina") if name in set(summary["team"])]
    selected = st.multiselect(
        "Tim untuk dibandingkan",
        options=summary["team"].tolist(),
        default=focus,
        max_selections=4,
    )
    if selected:
        st.plotly_chart(
            comparison_chart(summary, selected),
            width="stretch",
            config=PLOT_CONFIG,
            key="team-comparison",
        )

    profile_name = st.selectbox("Buka profil tim", options=summary["team"].tolist())
    profile = summary.loc[summary["team"] == profile_name].iloc[0]
    telemetry_specs(
        (
            ("Form", f"{profile.wins}M {profile.draws}S {profile.losses}K", "Menang · Seri · Kalah", True),
            ("Gol / xG", f"{profile.goals_for:.0f} / {profile.xg_for:.1f}", "Produksi turnamen", False),
            ("Shots", f"{profile.shots:.0f}", "Total percobaan", False),
            ("Possession", f"{profile.avg_possession:.1f}%", "Rata-rata penguasaan", False),
            ("Ranking FIFA", f"#{profile.ranking}", "Pra-turnamen", False),
            ("Corners", f"{profile.corners:.0f}", "Total turnamen", False),
            ("Foul", f"{profile.fouls:.0f}", "Total pelanggaran", False),
            ("Offside", f"{profile.offsides:.0f}", "Total offside", False),
            ("Kartu", f"{profile.yellow_cards:.0f}K / {profile.red_cards:.0f}M", "Kuning / Merah", False),
            ("Nilai skuad", format_eur(float(profile.squad_value_eur)), "Estimasi pasar", True),
        )
    )

    st.subheader("Form lima laga terakhir")
    form = team_form(raw, int(profile.team_id))
    telemetry_table(
        form[["tanggal", "lawan", "venue", "skor", "hasil"]].rename(
            columns={
                "tanggal": "Tanggal",
                "lawan": "Lawan",
                "venue": "Venue",
                "skor": "Skor",
                "hasil": "Hasil",
            }
        )
    )

    st.subheader("Seluruh tim")
    display = summary[
        [
            "team",
            "code",
            "ranking",
            "played",
            "wins",
            "draws",
            "losses",
            "goals_for",
            "goals_against",
            "avg_possession",
            "yellow_cards",
            "red_cards",
        ]
    ].rename(
        columns={
            "team": "Tim",
            "code": "Kode",
            "ranking": "Ranking",
            "played": "Main",
            "wins": "M",
            "draws": "S",
            "losses": "K",
            "goals_for": "GF",
            "goals_against": "GA",
            "avg_possession": "Possession",
            "yellow_cards": "Kuning",
            "red_cards": "Merah",
        }
    )
    telemetry_table(display, max_rows=48)


def render_players(raw: dict[str, pd.DataFrame] | None, data_dir: Path) -> None:
    _header(
        "1.248 pemain / Statistik aktual",
        "Direktori pemain",
        "Cari profil turnamen berdasarkan tim, posisi, klub, caps, nilai pasar, menit, kontribusi, dan statistik goalkeeper. Halaman ini tidak membuat prediksi pemain.",
    )
    if raw is None:
        raw_data_missing(data_dir)
        return
    players = build_player_frame(raw)
    filters = st.columns([2, 1, 1])
    search = filters[0].text_input("Cari nama atau klub", placeholder="Ketik nama pemain atau klub")
    team = filters[1].selectbox("Tim", ["Semua"] + sorted(players["team_name"].unique().tolist()))
    position = filters[2].selectbox("Posisi", ["Semua"] + sorted(players["position"].unique().tolist()))
    filtered = players.copy()
    if search:
        mask = (
            filtered["player_name"].str.contains(search, case=False, na=False)
            | filtered["club_team"].str.contains(search, case=False, na=False)
        )
        filtered = filtered[mask]
    if team != "Semua":
        filtered = filtered[filtered["team_name"] == team]
    if position != "Semua":
        filtered = filtered[filtered["position"] == position]
    st.caption(f"{len(filtered):,} pemain cocok".replace(",", "."))
    if filtered.empty:
        st.warning("Tidak ada pemain yang cocok. Ubah pencarian atau filter.")
        return

    labels = {
        int(row.player_id): f"{row.player_name} · {row.team_name} · {row.position}"
        for row in filtered.itertuples(index=False)
    }
    player_id = st.selectbox(
        "Buka profil pemain",
        options=list(labels),
        format_func=lambda value: labels[value],
    )
    player = filtered.loc[filtered["player_id"] == player_id].iloc[0]
    st.subheader(player.player_name)
    st.caption(f"{player.team_name} · {player.position} · {player.club_team}")
    telemetry_specs(
        (
            ("Usia", f"{player.age:.0f}", "Tahun", False),
            ("Caps", f"{player.caps:.0f}", "Penampilan internasional", False),
            ("Nilai", format_eur(float(player.market_value_eur)), "Estimasi pasar", True),
            ("Menit", f"{player.minutes_played:.0f}", "Menit turnamen", False),
            ("Starter", f"{player.matches_started:.0f}", "Masuk starting XI", False),
            ("Gol", f"{player.tournament_goals:.0f}", "Kontribusi turnamen", True),
            ("Assist", f"{player.assists:.0f}", "Kontribusi turnamen", False),
            ("Shots", f"{player.shots:.0f}" if pd.notna(player.shots) else "—", "Total percobaan", False),
            ("Kuning", f"{player.yellow_cards:.0f}", "Disiplin", False),
            ("Merah", f"{player.red_cards:.0f}", "Disiplin", False),
        )
    )
    if player.position == "GK":
        st.subheader("Catatan goalkeeper")
        telemetry_specs(
            (
                ("Clean sheets", f"{player.clean_sheets:.0f}", "Laga tanpa kebobolan", True),
                ("Saves", f"{player.saves:.0f}", "Penyelamatan", False),
                ("Gol kebobolan", f"{player.goals_conceded:.0f}", "Total turnamen", False),
            )
        )

    st.subheader("Daftar hasil filter")
    display = filtered[
        [
            "player_name",
            "team_name",
            "position",
            "club_team",
            "age",
            "caps",
            "market_value_eur",
            "minutes_played",
            "matches_started",
            "tournament_goals",
            "assists",
            "yellow_cards",
            "red_cards",
        ]
    ].copy()
    display["age"] = display["age"].round(0)
    display["market_value_eur"] = display["market_value_eur"].apply(
        lambda value: format_eur(float(value))
    )
    display = display.rename(
        columns={
            "player_name": "Pemain",
            "team_name": "Tim",
            "position": "Posisi",
            "club_team": "Klub",
            "age": "Usia",
            "caps": "Caps",
            "market_value_eur": "Nilai EUR",
            "minutes_played": "Menit",
            "matches_started": "Starter",
            "tournament_goals": "Gol",
            "assists": "Assist",
            "yellow_cards": "Kuning",
            "red_cards": "Merah",
        }
    )
    telemetry_table(display, max_rows=60)


def render_evaluation(evaluation: dict) -> None:
    _header(
        "Audit model / Data cutoff",
        "Evaluasi dan batas model",
        "Model dinilai dengan expanding-window validation. Setiap fold hanya melihat pertandingan yang kickoff sebelum validation fold dimulai.",
    )
    score = evaluation["score"]
    selected = score["selected_model"]
    baseline_loss = score["aggregate"]["smoothed_baseline"]["exact_score_log_loss"]
    selected_loss = score["aggregate"][selected]["exact_score_log_loss"]
    telemetry_specs(
        (
            ("Data cutoff", evaluation["data_cutoff"], "Batas data training", False),
            ("Label 90 menit", evaluation["sample_size_90_minutes"], "Laga Regular", False),
            ("Model skor", selected.replace("_", " "), "Dipilih via OOF kronologis", True),
            (
                "Perbaikan log loss",
                f"{(baseline_loss - selected_loss) / baseline_loss:.1%}",
                "Dibanding baseline tersmoothing",
                True,
            ),
        )
    )
    st.caption(
        f"Dikeluarkan dari target skor: {evaluation['excluded_from_score_target']['AET']} AET dan "
        f"{evaluation['excluded_from_score_target']['Penalties']} penalti."
    )
    st.plotly_chart(
        fold_evaluation_chart(evaluation),
        width="stretch",
        config=PLOT_CONFIG,
        key="evaluation-folds",
    )

    st.subheader("Metrik agregat model skor")
    score_table = pd.DataFrame(score["aggregate"]).T.reset_index(names="model")
    score_table["dipilih"] = (score_table["model"] == selected).map(
        {True: "Ya", False: "Tidak"}
    )
    telemetry_table(score_table)

    st.subheader("Kalibrasi")
    st.write(
        "Exact-score log loss dan outcome log loss menilai ketajaman sekaligus menghukum "
        "probabilitas yang terlalu yakin. Dengan 92 label, reliability bins per kelas akan "
        "sangat jarang; dashboard karena itu tidak menampilkan kurva kalibrasi yang tampak "
        "presisi tetapi rapuh. Confidence dibatasi pada medium dan rare events selalu low."
    )
    st.caption(
        "Outcome log loss model terpilih: "
        f"{score['aggregate'][selected]['outcome_log_loss']:.3f}; baseline "
        f"{score['aggregate']['smoothed_baseline']['outcome_log_loss']:.3f}."
    )

    st.subheader("Model event dan fallback")
    event_table = pd.DataFrame(
        [
            {
                "target": EVENT_LABELS.get(target, target),
                "model": result["selected_model"],
                "fallback": "Ya" if result["fallback_used"] else "Tidak",
                "alasan": result.get("fallback_reason") or "Mengungguli baseline",
            }
            for target, result in evaluation["events"].items()
        ]
    )
    telemetry_table(event_table)
    st.write(
        f"Possession: ridge MAE {evaluation['possession']['ridge_mae']:.2f} poin vs "
        f"baseline {evaluation['possession']['baseline_mae']:.2f} poin. Prediksi dua tim "
        "dinormalisasi agar selalu berjumlah 100%."
    )

    st.subheader("Keterbatasan yang harus dibawa ke interpretasi")
    for limitation in evaluation["limitations"]:
        st.write(f"- {limitation}")
    st.warning(
        "Red card dan VAR masing-masing hanya memiliki 13 kejadian. Angka tersebut memakai "
        "Beta smoothing dan bukan estimasi kekuatan khusus tim."
    )
