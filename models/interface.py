from pathlib import Path
from typing import Optional

import joblib
import pandas as pd
from pydantic import BaseModel

from data.reader import FEATURE_COLUMNS

SCHEMA_VERSION = "1.0"
MODEL_VERSION = "mock-v0"
MODEL_PATH = Path(__file__).parent / "baseline_fake.joblib"

FEATURE_ORDER = FEATURE_COLUMNS

_artifact = None


class SessionFeatures(BaseModel):
    mouse_distance_px: Optional[float] = None
    mouse_speed_mean_px_s: Optional[float] = None
    mouse_speed_std_px_s: Optional[float] = None
    direction_change_count: Optional[int] = None
    click_count: Optional[int] = None
    click_interval_mean_ms: Optional[float] = None
    scroll_event_count: Optional[int] = None
    scroll_distance_px: Optional[float] = None


class PredictInput(BaseModel):
    schema_version: str = SCHEMA_VERSION
    session_id: str
    window_id: str
    window_started_at: str
    window_duration_ms: int
    collector_version: str
    browser_features: SessionFeatures


class PredictOutput(BaseModel):
    prediction: str
    model_version: str = MODEL_VERSION


def _load_artifact():
    """Charge le modèle entraîné une seule fois, s'il existe."""
    global _artifact
    if _artifact is None and MODEL_PATH.exists():
        _artifact = joblib.load(MODEL_PATH)
    return _artifact


def predict(data: PredictInput) -> PredictOutput:
    artifact = _load_artifact()

    # Pas de modèle entraîné : on garde la réponse simulée.
    if artifact is None:
        return PredictOutput(prediction="HUMAN", model_version=MODEL_VERSION)

    features = data.browser_features.model_dump()
    order = artifact["feature_order"]
    row = pd.DataFrame([[features[c] for c in order]], columns=order).astype(float)

    label = artifact["pipeline"].predict(row)[0]
    return PredictOutput(
        prediction=str(label).upper(),
        model_version=artifact["model_version"],
    )