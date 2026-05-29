import streamlit as st

# MEN MODULES
from data_loader import load_all_teams
from team_profile import render_team_profile
from team_compare import render_team_compare

# WOMEN MODULES
from data_loader_women import load_all_womens_teams
from team_profile_women import render_team_profile_women
from team_compare_women import render_team_compare_women


# ---------------------------------------------------------
# PAGE CONFIG + THEME
# ---------------------------------------------------------

st.set_page_config(
    page_title="OPTA Team Profiles & Comparison",
    layout="wide",
)

st.markdown("""
<style>
html, body, [class*="css"]  {
    font-family: 'Garamond', serif;
    font-weight: 600;
    color: #FAFAFA;
}
:root {
    --primary: #006400;
    --bg-dark: #050608;
    --bg-card: #111318;
    --text-light: #FAFAFA;
}
body {
    background-color: var(--bg-dark);
    color: var(--text-light);
}
section.main > div {
    background: var(--bg-dark);
}
.block-container {
    padding-top: 1.5rem;
}
.neon-card {
    background: var(--bg-card);
    padding: 20px;
    border-radius: 12px;
    border: 1px solid rgba(255, 255, 255, 0.15);
}
h1.neon-title {
    text-align: center;
    letter-spacing: 1px;
    color: var(--primary);
}
[data-testid="stMetricValue"] {
    color: var(--primary) !important;
    font-weight: 700;
}
div[data-testid="stMetricLabel"] {
    color: var(--text-light);
}
hr {
    border: 1px solid rgba(255,255,255,0.15);
}
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------
# LOAD DATA
# ---------------------------------------------------------

@st.cache_data
def get_men_data():
    return load_all_teams("data/opta/men")

@st.cache_data
def get_women_data():
    return load_all_womens_teams("data/opta/women")


df_men = get_men_data()
df_women = get_women_data()


# ---------------------------------------------------------
# HEADER
# ---------------------------------------------------------

st.markdown(
    "<h1 class='neon-title' style='font-size:42px; text-align:center;'>OPTA TEAM PROFILES & COMPARISON</h1>",
    unsafe_allow_html=True,
)
st.markdown("<hr>", unsafe_allow_html=True)


# ---------------------------------------------------------
# NAVIGATION (4‑PAGE STRUCTURE)
# ---------------------------------------------------------

st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Page",
    [
        "Team Profile (Men)",
        "Team Profile (Women)",
        "Team Comparison (Men)",
        "Team Comparison (Women)",
    ],
)


# ---------------------------------------------------------
# ROUTING
# ---------------------------------------------------------

if page == "Team Profile (Men)":
    render_team_profile(df_men)

elif page == "Team Profile (Women)":
    render_team_profile_women(df_women)

elif page == "Team Comparison (Men)":
    render_team_compare(df_men)

elif page == "Team Comparison (Women)":
    render_team_compare_women(df_women)
