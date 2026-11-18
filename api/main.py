from fastapi import FastAPI  # type: ignore[import-not-found]

from api.schemas import Observation

app = FastAPI()


@app.post("/v1/observations")
def receive_observation(observation: Observation):
    features = observation.browser_features
    has_activity = (
        features.click_count > 0
        or features.scroll_event_count > 0
        or features.mouse_distance_px > 0
    )

    return {
        "session_id": observation.session_id,
        "window_id": observation.window_id,
        "prediction": "HUMAN" if has_activity else None,
        "risk_level": "LOW" if has_activity else None,
        "model_version": "mock-v0",
        "data_quality": "SUFFICIENT" if has_activity else "INSUFFICIENT",
    }