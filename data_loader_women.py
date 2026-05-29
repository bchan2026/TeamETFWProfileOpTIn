import re
from pathlib import Path
import pandas as pd


def parse_league_from_filename(path: str) -> str:
    """
    Extract league name from filename.

    Examples:
    TeamReport_CELTIC CHALLENGE-R1-12_865_2026_EN.xlsx
    -> CELTIC CHALLENGE

    TeamReport_PREMIERSHIP WOMENS RUGBY-R1-16_340_2026_EN.xlsx
    -> PREMIERSHIP WOMENS RUGBY
    """
    name = Path(path).name
    m = re.search(r"TeamReport_(.+?)-R", name)
    if m:
        return m.group(1).strip()
    return "UNKNOWN"


def load_team_file(path: str) -> pd.DataFrame:
    league = parse_league_from_filename(path)

    xls = pd.ExcelFile(path)

    total_df = pd.read_excel(xls, sheet_name="Total")
    round_df = pd.read_excel(xls, sheet_name="Round")

    if "Team" not in total_df.columns:
        raise ValueError(f"'Team' column not found in Total sheet of {path}")
    if "Team" not in round_df.columns:
        raise ValueError(f"'Team' column not found in Round sheet of {path}")

    games_played = (
        round_df
        .dropna(subset=["Team"])
        .groupby("Team")
        .size()
        .rename("Games Played")
        .reset_index()
    )

    merged = total_df.merge(games_played, on="Team", how="left")
    merged["League"] = league

    return merged


def load_all_womens_teams(root_folder: str = "data/opta/women") -> pd.DataFrame:
    root = Path(root_folder)
    files = sorted(root.glob("*.xlsx"))

    if not files:
        raise FileNotFoundError(f"No .xlsx files found in {root_folder}")

    frames = []
    for f in files:
        try:
            df = load_team_file(str(f))
            frames.append(df)
        except Exception as e:
            print(f"Error loading {f}: {e}")

    if not frames:
        raise RuntimeError("No valid women team files loaded.")

    all_teams = pd.concat(frames, ignore_index=True)

    if "Games Played" in all_teams.columns:
        all_teams["Games Played"] = all_teams["Games Played"].fillna(0).astype(int)

    return all_teams
