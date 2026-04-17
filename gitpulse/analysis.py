"""Pandas-based analysis of raw GitHub payloads.

All functions take the lists returned by ``github_client`` and
return tidy DataFrames ready for plotting. Kept pure (no I/O) so
the Streamlit layer can cache them freely.
"""

from __future__ import annotations

import pandas as pd


def commits_to_dataframe(commits: list[dict]) -> pd.DataFrame:
    """Flatten GitHub's commit payloads into a tidy DataFrame.

    Picks out the handful of fields the charts actually need and
    parses the ISO-8601 author date into a tz-aware Timestamp.
    """
    rows = []
    for commit in commits:
        author = (commit.get("commit") or {}).get("author") or {}
        login = ((commit.get("author") or {}) or {}).get("login")
        date_str = author.get("date")
        if not date_str:
            continue
        rows.append(
            {
                "sha": commit.get("sha"),
                "author_login": login or author.get("name") or "unknown",
                "author_date": pd.to_datetime(date_str, utc=True),
                "message": (author.get("name") and commit.get("commit", {}).get("message")) or "",
            }
        )
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    return df.sort_values("author_date").reset_index(drop=True)


def weekly_activity(commits_df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate commits into ISO-week buckets.

    Returns a DataFrame with one row per week between the first and
    last commit, zero-filled, so the chart renders as a continuous
    line even when there are quiet periods.
    """
    if commits_df.empty:
        return pd.DataFrame(columns=["week", "commits"])

    weekly = (
        commits_df.set_index("author_date")
        .resample("W-MON")
        .size()
        .rename("commits")
        .to_frame()
    )

    full_range = pd.date_range(
        start=weekly.index.min(),
        end=weekly.index.max(),
        freq="W-MON",
    )
    weekly = weekly.reindex(full_range, fill_value=0)
    weekly.index.name = "week"
    return weekly.reset_index()


def commits_by_weekday(commits_df: pd.DataFrame) -> pd.DataFrame:
    """Count commits bucketed by day-of-week.

    Used to surface 'weekend warrior' vs 'nine-to-five' patterns.
    Days with zero commits are still present so the chart is stable.
    """
    order = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    if commits_df.empty:
        return pd.DataFrame({"weekday": order, "commits": [0] * 7})

    weekdays = commits_df["author_date"].dt.day_name().str[:3]
    counts = weekdays.value_counts()
    return pd.DataFrame(
        {"weekday": order, "commits": [int(counts.get(d, 0)) for d in order]}
    )
