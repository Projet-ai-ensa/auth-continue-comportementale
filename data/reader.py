"""Lecteur du CSV de features (contrat v0.1)."""
import pandas as pd

ID_COLUMNS = ["user_id", "session_id", "window_id"]
FEATURE_COLUMNS = [
    "key_count",
    "hold_mean_ms",
    "interkey_mean_ms",
    "mouse_distance_px",
    "mouse_speed_mean_px_s",
    "click_count",
]
EXPECTED_COLUMNS = ID_COLUMNS + FEATURE_COLUMNS


def read_features(path):
    """Lit le CSV et vérifie les colonnes (noms, ordre, nombre).

    Les cellules vides restent NaN : donnée absente, jamais 0.
    """
    df = pd.read_csv(path)
    columns = list(df.columns)

    if columns != EXPECTED_COLUMNS:
        missing = [c for c in EXPECTED_COLUMNS if c not in columns]
        extra = [c for c in columns if c not in EXPECTED_COLUMNS]
        if missing or extra:
            raise ValueError(f"Colonnes invalides. Manquantes: {missing}, en trop: {extra}")
        raise ValueError(f"Mauvais ordre des colonnes. Attendu: {EXPECTED_COLUMNS}")

    for col in FEATURE_COLUMNS:
        df[col] = pd.to_numeric(df[col], errors="raise")
    return df