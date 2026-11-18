from pathlib import Path
import pandas as pd

CMU_PATH = Path("data/raw/DSL-StrongPasswordData.csv")

def load_cmu(path: Path = CMU_PATH) -> pd.DataFrame:
    return pd.read_csv(path)

def summarize(df: pd.DataFrame) -> None:
    print("Shape:", df.shape)
    print("Users:", df["subject"].nunique())
    print("Sessions per user:", df.groupby("subject")["sessionIndex"].nunique().unique())
    print("Reps per session:", df["rep"].max())
    print("Missing values:", int(df.isna().sum().sum()))
    print("Columns:", list(df.columns))

if __name__ == "__main__":
    summarize(load_cmu())

def to_v0_keyboard_features(df: pd.DataFrame) -> pd.DataFrame:
    hold_cols = [c for c in df.columns if c.startswith("H.")]
    dd_cols = [c for c in df.columns if c.startswith("DD.")]
    return pd.DataFrame({
        "user_id": df["subject"],
        "session_id": df["subject"] + "_s" + df["sessionIndex"].astype(str),
        "hold_mean_ms": df[hold_cols].mean(axis=1) * 1000,
        "interkey_mean_ms": df[dd_cols].mean(axis=1) * 1000,
    })

def to_v0_keyboard_features(df: pd.DataFrame) -> pd.DataFrame:
    hold_cols = [c for c in df.columns if c.startswith("H.")]
    dd_cols = [c for c in df.columns if c.startswith("DD.")]
    if not hold_cols or not dd_cols:
        raise ValueError("Expected H.* and DD.* columns in CMU data")
    return pd.DataFrame({
        "user_id": df["subject"],
        "session_id": df["subject"] + "_s" + df["sessionIndex"].astype(str),
        "hold_mean_ms": df[hold_cols].mean(axis=1) * 1000,
        "interkey_mean_ms": df[dd_cols].mean(axis=1) * 1000,
    })