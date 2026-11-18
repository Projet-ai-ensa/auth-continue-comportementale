import pandas as pd


def summarize(df):
    if df.empty:
        return {"windows": 0, "sessions": 0, "participants": 0, "bot_share": 0.0}
    return {
        "windows": len(df),
        "sessions": df["session_id"].nunique(),
        "participants": df["participant_id"].nunique(),
        "bot_share": (df["label"] == "bot").mean() * 100,
    }


def average_by_label(df, feature):
    return df.groupby("label")[feature].mean().reset_index()