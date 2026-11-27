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


def filter_windows(df, labels, bot_types):
    # Keep only the chosen labels (human, bot)
    keep = df["label"].isin(labels)
    # For bots, keep only the chosen bot types.
    # Humans have no bot type, so this filter never removes them.
    is_bot = df["label"] == "bot"
    keep = keep & (~is_bot | df["bot_config"].isin(bot_types))
    return df[keep]