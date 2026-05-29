import math
import pandas as pd
import streamlit as st
import altair as alt

from metrics import TEAM_METRIC_GROUPS


# ---------------------------------------------------------
# FORMAT HELPERS
# ---------------------------------------------------------

def format_number(value):
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return ""
    try:
        v = float(value)
        if v.is_integer():
            return str(int(v))
        return f"{v:.1f}"
    except Exception:
        return str(value)


def format_percentage(value):
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return ""
    try:
        v = float(value)
        if v <= 1:
            v = v * 100.0
        if v.is_integer():
            return f"{int(v)}%"
        return f"{v:.1f}%"
    except Exception:
        return ""


def is_percentage_metric(name: str) -> bool:
    if not name:
        return False
    n = name.lower()
    return ("percent" in n) or ("%" in n) or ("rate" in n)


# ---------------------------------------------------------
# THEME‑AWARE ALTAIR CHART BUILDER
# ---------------------------------------------------------

def altair_metric_chart(df, metric, title):
    # Detect Streamlit theme
    theme = st.get_option("theme.base") or "dark"

    if theme == "dark":
        text_color = "#F7E733"        # bright yellow
        axis_color = "#FAFAFA"        # white
        title_color = "#FAFAFA"
        team_label_color = "#FFFFFF"  # white team names
    else:
        text_color = "black"
        axis_color = "black"
        title_color = "black"
        team_label_color = "black"

    base = alt.Chart(df).encode(
        x=alt.X(
            "Team:N",
            sort="-y",
            title="Team",
            axis=alt.Axis(
                labelFont="Garamond",
                labelColor=team_label_color,
                labelFontSize=14,
                labelFontWeight="bold",
                titleColor=axis_color
            )
        ),
        y=alt.Y(
            f"{metric}:Q",
            title=metric,
            axis=alt.Axis(
                labelColor=axis_color,
                titleColor=axis_color
            )
        )
    )

    bars = base.mark_bar(
        color="#2ecc71",
        cornerRadiusTopLeft=4,
        cornerRadiusTopRight=4
    )

    text = base.mark_text(
        align="center",
        baseline="middle",
        dy=-10,
        font="Garamond",
        fontSize=14,
        fontWeight="bold",
        color=text_color
    ).encode(
        text=alt.Text(f"{metric}:Q", format=".1f")
    )

    chart = (
        (bars + text)
        .properties(
            width="container",
            height=350,
            title=title
        )
        .configure_title(
            font="Garamond",
            color=title_color,
            fontSize=20
        )
        .configure_view(
            strokeOpacity=0
        )
    )

    return chart


# ---------------------------------------------------------
# TEAM PROFILE PAGE
# ---------------------------------------------------------

def render_team_profile(df: pd.DataFrame) -> None:
    st.subheader("🏉 Team Profile")

    # -----------------------------
    # FILTER CARD
    # -----------------------------
    with st.container():
        st.markdown("<div class='neon-card'>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)

        leagues = sorted(df["League"].dropna().unique())
        league_choice = c1.selectbox("League", leagues)

        league_df = df[df["League"] == league_choice].copy()

        teams = sorted(league_df["Team"].dropna().unique())
        team_choice = c2.selectbox("Team", teams)

        per_game = c3.checkbox("Per Game Averages", value=False)

        st.markdown("</div>", unsafe_allow_html=True)

    if not team_choice:
        st.info("Select a team.")
        return

    # -----------------------------
    # GET TEAM ROW
    # -----------------------------
    team_row = league_df[league_df["Team"] == team_choice].iloc[0]
    games_played = int(team_row.get("Games Played", 0))

    # Apply per-game logic to ALL non-percentage metrics
    row = team_row.copy()

    if per_game and games_played > 0:
        for group_name, group_metrics in TEAM_METRIC_GROUPS.items():
            for metric in group_metrics:
                if metric not in row:
                    continue
                if is_percentage_metric(metric):
                    continue
                try:
                    row[metric] = row[metric] / games_played
                except Exception:
                    pass

    st.markdown("<hr>", unsafe_allow_html=True)

    # -----------------------------
    # PROFILE CARD
    # -----------------------------
    with st.container():
        st.markdown("<div class='neon-card'>", unsafe_allow_html=True)

        st.markdown(f"### {team_choice} – {league_choice}")
        st.write(f"**Games Played:** {games_played}")

        tab_names = list(TEAM_METRIC_GROUPS.keys())
        tabs = st.tabs(tab_names)

        for tab, group_name in zip(tabs, tab_names):
            with tab:
                st.markdown(f"#### {group_name}")

                metrics = TEAM_METRIC_GROUPS[group_name]
                existing_metrics = [m for m in metrics if m in row.index]

                cols = st.columns(4)
                idx = 0

                for metric in existing_metrics:
                    val = row.get(metric)

                    if is_percentage_metric(metric):
                        display_val = format_percentage(val)
                    else:
                        display_val = format_number(val)

                    cols[idx % 4].metric(metric, display_val)
                    idx += 1

        # -----------------------------
        # ALTAIR VISUALISATION SECTION
        # -----------------------------
        st.markdown("<hr>", unsafe_allow_html=True)
        st.subheader("📈 Metric Visualisation")

        metric_choice = st.selectbox(
            "Select a metric to visualise",
            [m for group in TEAM_METRIC_GROUPS.values() for m in group]
        )

        chart_df = league_df[["Team", metric_choice, "Games Played"]].copy()

        if per_game and not is_percentage_metric(metric_choice):
            chart_df[metric_choice] = chart_df[metric_choice] / chart_df["Games Played"]

        st.altair_chart(
            altair_metric_chart(chart_df, metric_choice, f"{metric_choice} Comparison"),
            use_container_width=True
        )

        st.markdown("</div>", unsafe_allow_html=True)
