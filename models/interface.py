from typing import Optional

from pydantic import BaseModel, ConfigDict

from data.reader import FEATURE_COLUMNS

SCHEMA_VERSION = "1.0"
MODEL_VERSION = "mock-v0"

FEATURE_ORDER = FEATURE_COLUMNS


class SessionFeatures(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # Même ordre que FEATURE_COLUMNS (data/reader.py).
    # Optional[float] sans "= None" : la clé doit être présente, la valeur peut être null.
    mouse_distance_px: float
    mouse_speed_mean_px_s: Optional[float]
    mouse_speed_std_px_s: Optional[float]
    direction_change_count: int
    click_count: int
    click_interval_mean_ms: Optional[float]
    scroll_event_count: int
    scroll_distance_px: float


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


def predict(data: PredictInput) -> PredictOutput:
    """Return a placeholder prediction until the ML model is integrated."""

    return PredictOutput(
        prediction="HUMAN",
        model_version=MODEL_VERSION,
    )