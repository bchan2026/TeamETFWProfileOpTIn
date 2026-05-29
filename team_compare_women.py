import math
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from metrics_women import TEAM_METRIC_GROUPS_WOMEN as TEAM_METRIC_GROUPS

LOWER_IS_BETTER = [
    "Turnover Conceded",
    "Penalty Conceded",
    "Yellow Card",
    "Red Card",
]


def is_percentage_metric(name: str) -> bool:
    if not name:
        return False
    n = name.lower()
    return ("percent" in n) or ("%" in n) or ("rate" in n)


def format_raw_value(metric: str, v):
    if pd.isna(v):
        return ""
    if is_percentage_metric(metric):
        try:
            v = float(v)
            if v <= 1:
                v = v * 100
            return str(int(round(v)))
        except Exception:
            return ""
    try:
        v = float(v)
        if v.is_integer():
            return str(int(v))
        return f"{v:.1f}"
    except Exception:
        return str(v)


def render_team_compare_women(df: pd.DataFrame) -> None:
    st.subheader("📊 Women's Team Comparison")

    # -----------------------------------------------------
    # FILTER CARD
    # -----------------------------------------------------
    with st.container():
        st.markdown("<div class='neon-card'>", unsafe_allow_html=True)

        c1, c2 = st.columns([1, 5])

        leagues = sorted(df["League"].dropna().unique())

        # SAFELY HANDLE SESSION STATE FOR WOMEN
        if "compare_league_women" not in st.session_state or st.session_state.compare_league_women not in leagues:
            st.session_state.compare_league_women = leagues[0]

        st.session_state.compare_league_women = c1.selectbox(
            "League",
            leagues,
            index=leagues.index(st.session_state.compare_league_women),
            key="league_selector_women"
        )

        league_df = df[df["League"] == st.session_state.compare_league_women].copy()
        league_df = league_df.drop_duplicates(subset=["Team"], keep="first")

        team_list = ["None"] + sorted(league_df["Team"].dropna().unique())

        # Persistent team slots (WOMEN)
        if "compare_slots_women" not in st.session_state:
            st.session_state.compare_slots_women = ["None"] * 6

        cols = c2.columns(6)
        new_slots = []

        for i in range(6):
            current = st.session_state.compare_slots_women[i]
            options = team_list if current in team_list else team_list + [current]

            new_val = cols[i].selectbox(
                f"Team {i+1}",
                options,
                index=options.index(current) if current in options else 0,
                key=f"team_slot_women_{i}",
            )
            new_slots.append(new_val)

        st.session_state.compare_slots_women = new_slots

        per_game = st.checkbox("Per Game Averages", value=False, key="per_game_women")

        st.markdown("</div>", unsafe_allow_html=True)

    # -----------------------------------------------------
    # SELECTED TEAMS
    # -----------------------------------------------------
    selected_teams = [t for t in st.session_state.compare_slots_women if t != "None"]

    if len(selected_teams) < 2:
        st.info("Select at least two teams.")
        return

    if len(selected_teams) > 6:
        selected_teams = selected_teams[:6]

    # -----------------------------------------------------
    # APPLY PER-GAME LOGIC
    # -----------------------------------------------------
    work_df = df.copy()
    work_df = work_df.drop_duplicates(subset=["Team"], keep="first")

    if per_game:
        all_metrics = sorted(
            {m for group in TEAM_METRIC_GROUPS.values() for m in group}
        )
        for metric in all_metrics:
            if metric not in work_df.columns:
                continue
            if is_percentage_metric(metric):
                continue
            work_df[metric] = np.where(
                work_df["Games Played"] > 0,
                work_df[metric] / work_df["Games Played"],
                work_df[metric],
            )

    sel_df = work_df[work_df["Team"].isin(selected_teams)].set_index("Team")

    # -----------------------------------------------------
    # RADAR CHART
    # -----------------------------------------------------
    st.subheader("Radar Chart")

    radar_metrics = []
    for group_metrics in TEAM_METRIC_GROUPS.values():
        for m in group_metrics:
            if m not in radar_metrics:
                radar_metrics.append(m)

    fig = go.Figure()
    colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b"]

    for idx, name in enumerate(selected_teams):
        row = sel_df.loc[name]
        if isinstance(row, pd.DataFrame):
            row = row.iloc[0]

        league = str(row["League"])
        league_group = work_df[work_df["League"] == league]

        pct_list = []
        for metric in radar_metrics:
            if metric not in row or metric not in league_group.columns:
                pct_list.append(0)
                continue

            series = league_group[metric].dropna()
            if series.empty:
                pct_list.append(0)
                continue

            val = row[metric]
            try:
                pct = (series < val).mean() * 100
            except Exception:
                pct = 0
            pct_list.append(pct)

        fig.add_trace(
            go.Scatterpolar(
                r=pct_list,
                theta=radar_metrics,
                fill="toself",
                name=name,
                line=dict(color=colors[idx % len(colors)], width=3),
            )
        )

    league_avg = [50] * len(radar_metrics)
    fig.add_trace(
        go.Scatterpolar(
            r=league_avg,
            theta=radar_metrics,
            fill="toself",
            name="League Avg",
            line=dict(color="white", width=2, dash="dot"),
        )
    )

    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        paper_bgcolor="#0E1117",
        font=dict(color="#FAFAFA", family="Garamond"),
        height=700,
    )

    st.plotly_chart(fig, use_container_width=True)

    # -----------------------------------------------------
    # COMPARISON TABLE
    # -----------------------------------------------------
    st.subheader("Comparison Table (Raw Values Only)")

    all_metrics = []
    for group_metrics in TEAM_METRIC_GROUPS.values():
        for m in group_metrics:
            if m not in all_metrics:
                all_metrics.append(m)

    table = pd.DataFrame(index=all_metrics)

    for name in selected_teams:
        row = sel_df.loc[name]
        if isinstance(row, pd.DataFrame):
            row = row.iloc[0]

        table[name] = [
            format_raw_value(metric, row.get(metric, np.nan)) for metric in all_metrics
        ]

    style_map = pd.DataFrame("", index=table.index, columns=table.columns)
    green_count = {name: 0 for name in selected_teams}

    for metric in all_metrics:
        values = {}
        for name in selected_teams:
            row = sel_df.loc[name]
            if isinstance(row, pd.DataFrame):
                row = row.iloc[0]
            raw_val = row.get(metric, np.nan)
            if pd.notna(raw_val):
                try:
                    values[name] = float(raw_val)
                except Exception:
                    continue

        if len(values) < 2:
            continue

        if metric in LOWER_IS_BETTER:
            ranked = sorted(values.items(), key=lambda x: x[1])
        else:
            ranked = sorted(values.items(), key=lambda x: x[1], reverse=True)

        if len(ranked) >= 1:
            best = ranked[0][0]
            style_map.loc[metric, best] = "color:#2ecc71; font-weight:700;"
            green_count[best] += 1

        if len(ranked) >= 2:
            second = ranked[1][0]
            style_map.loc[metric, second] = "color:#e67e22; font-weight:700;"

        if len(ranked) >= 3:
            third = ranked[2][0]
            style_map.loc[metric, third] = "color:#e74c3c; font-weight:700;"

    max_greens = max(green_count.values()) if green_count else 0
    renamed_cols = {}
    for name in table.columns:
        base = name.replace("🌟 ", "")
        if green_count.get(base, 0) == max_greens and max_greens > 0:
            renamed_cols[name] = f"🌟 {base}"
    if renamed_cols:
        table.rename(columns=renamed_cols, inplace=True)
        style_map.rename(columns=renamed_cols, inplace=True)

    st.dataframe(
        table.style.apply(lambda row: style_map.loc[row.name], axis=1),
        use_container_width=True,
    )
