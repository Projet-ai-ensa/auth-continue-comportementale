from typing import Annotated, Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

Count = Annotated[int, Field(strict=True, ge=0)]
Measurement = Annotated[float, Field(strict=True, ge=0, allow_inf_nan=False)]


class BrowserFeatures(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mouse_distance_px: Measurement
    mouse_speed_mean_px_s: Measurement | None
    mouse_speed_std_px_s: Measurement | None
    direction_change_count: Count
    click_count: Count
    click_interval_mean_ms: Measurement | None
    scroll_event_count: Count
    scroll_distance_px: Measurement


class Observation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"]
    session_id: Annotated[str, Field(min_length=1)]
    window_id: Annotated[str, Field(min_length=1)]
    window_started_at: AwareDatetime
    window_duration_ms: Annotated[int, Field(strict=True, gt=0)]
    collector_version: Annotated[str, Field(min_length=1)]
    browser_features: BrowserFeatures