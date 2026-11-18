from pathlib import Path
import pandas as pd

FEATURE_COLUMNS = [
    "mouse_distance_px",
    "mouse_speed_mean_px_s",
    "mouse_speed_std_px_s",
    "direction_change_count",
    "click_count",
    "click_interval_mean_ms",
    "scroll_event_count",
    "scroll_distance_px",
]
METADATA_COLUMNS = ["participant_id", "session_id", "window_id", "label", "bot_config"]
ALL_COLUMNS = METADATA_COLUMNS + FEATURE_COLUMNS
VALID_LABELS = {"human", "bot"}


def validate_columns(df: pd.DataFrame) -> None:
    missing = [c for c in ALL_COLUMNS if c not in df.columns]
    extra = [c for c in df.columns if c not in ALL_COLUMNS]
    if missing or extra:
        raise ValueError(f"missing columns: {missing}; unexpected columns: {extra}")
    if list(df.columns) != ALL_COLUMNS:
        raise ValueError(f"column order must be {ALL_COLUMNS}")
    bad = set(df["label"].dropna().unique()) - VALID_LABELS
    if bad:
        raise ValueError(f"invalid labels: {sorted(bad)}")


def read_features(path) -> pd.DataFrame:
    df = pd.read_csv(Path(path))
    validate_columns(df)
    return df