import re
from pathlib import Path
from typing import Optional

import pandas as pd


def parse_league_from_filename(path: str) -> str:
    """
    Extract league name from filename.

    Example:
    TeamReport_GALLAGHER PREM-R1-16_201_2026_EN.xlsx
    -> GALLAGHER PREM
    """
    name = Path(path).name
    m = re.search(r"TeamReport_(.+?)-R", name)
    if m:
        return m.group(1).strip()
    return "UNKNOWN"


def load_team_file(path: str) -> pd.DataFrame:
    """
    Load a single TeamReport_*.xlsx file.

    - Total sheet: all metrics (one row per team)
    - Round sheet: used ONLY to compute Games Played per team
    - Adds: League, Games Played
    """
    league = parse_league_from_filename(path)

    xls = pd.ExcelFile(path)

    total_df = pd.read_excel(xls, sheet_name="Total")
    round_df = pd.read_excel(xls, sheet_name="Round")

    # Ensure 'Team' column exists
    if "Team" not in total_df.columns:
        raise ValueError(f"'Team' column not found in Total sheet of {path}")
    if "Team" not in round_df.columns:
        raise ValueError(f"'Team' column not found in Round sheet of {path}")

    # Compute Games Played from Round sheet: count rows per team
    games_played = (
        round_df
        .dropna(subset=["Team"])
        .groupby("Team")
        .size()
        .rename("Games Played")
        .reset_index()
    )

    # Merge Games Played into Total metrics
    merged = total_df.merge(games_played, on="Team", how="left")

    # Add League column
    merged["League"] = league

    return merged


def load_all_teams(root_folder: str = "data/opta") -> pd.DataFrame:
    """
    Load all TeamReport_*.xlsx files under data/opta and return a single DataFrame.
    """
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
        raise RuntimeError("No valid team files loaded.")

    all_teams = pd.concat(frames, ignore_index=True)

    # Optional: ensure Games Played is integer
    if "Games Played" in all_teams.columns:
        all_teams["Games Played"] = all_teams["Games Played"].fillna(0).astype(int)

    return all_teams
