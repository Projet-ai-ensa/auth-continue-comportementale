import pandas as pd
from data.reader import FEATURE_COLUMNS

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


# --- Model results ---

def predict_windows(df, predict_one):
    # Ask the model for each window and add its answer in a "prediction" column.
    # predict_one(session_id, window_id, features) must return "HUMAN" or "BOT".
    predictions = []
    for row in df.to_dict("records"):
        # Empty cells (NaN) become None, as the API expects
        features = {c: (None if pd.isna(row[c]) else row[c]) for c in FEATURE_COLUMNS}
        predictions.append(predict_one(row["session_id"], row["window_id"], features))
    return df.assign(prediction=predictions)


def confusion_counts(df):
    # Compare the truth ("label") with the model's answer ("prediction")
    is_bot = df["label"] == "bot"
    said_bot = df["prediction"] == "BOT"
    return {
        "bots_caught": int((is_bot & said_bot).sum()),
        "bots_missed": int((is_bot & ~said_bot).sum()),
        "humans_flagged": int((~is_bot & said_bot).sum()),
        "humans_ok": int((~is_bot & ~said_bot).sum()),
    }


def detection_rates(counts):
    # Percentages, or None when there is nothing to divide by
    bots = counts["bots_caught"] + counts["bots_missed"]
    humans = counts["humans_flagged"] + counts["humans_ok"]
    return {
        "bots_caught_pct": counts["bots_caught"] / bots * 100 if bots else None,
        "humans_flagged_pct": counts["humans_flagged"] / humans * 100 if humans else None,
    }