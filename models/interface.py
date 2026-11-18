
from typing import Optional
from pydantic import BaseModel

from data.reader import FEATURE_COLUMNS

SCHEMA_VERSION = "1.0"
MODEL_VERSION = "mock-v0"

FEATURE_ORDER = FEATURE_COLUMNS


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
    session_id: str
    window_id: str
    prediction: str
    risk_level: str
    model_version: str = MODEL_VERSION
    data_quality: str = "SUFFICIENT"


def predict(data: PredictInput) -> PredictOutput:
    """Return a placeholder prediction until the ML model is integrated."""

    return PredictOutput(
        session_id=data.session_id,
        window_id=data.window_id,
        prediction="HUMAN",
        risk_level="LOW",
        model_version=MODEL_VERSION,
        data_quality="SUFFICIENT",
    )
