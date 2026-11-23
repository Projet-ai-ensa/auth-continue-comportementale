from fastapi import FastAPI  # type: ignore[import-not-found]

from api.schemas import Observation
from models.interface import MODEL_VERSION, PredictInput, predict

app = FastAPI()


@app.post("/v1/observations")
def receive_observation(observation: Observation):
    features = observation.browser_features
    has_activity = (
        features.click_count > 0
        or features.scroll_event_count > 0
        or features.mouse_distance_px > 0
    )

    # A window without observed activity has insufficient evidence to classify.
    # Keep the ML interface separate from the HTTP endpoint.
    model_result = None
    if has_activity:
        model_input = PredictInput.model_validate(observation.model_dump(mode="json"))
        model_result = predict(model_input)

    return {
        "session_id": observation.session_id,
        "window_id": observation.window_id,
        "prediction": model_result.prediction if model_result else None,
        "risk_level": "LOW" if model_result and model_result.prediction == "HUMAN" else None,
        "model_version": model_result.model_version if model_result else MODEL_VERSION,
        "data_quality": "SUFFICIENT" if has_activity else "INSUFFICIENT",
    }
