"""Regression tests for the FastAPI-to-model integration boundary."""

import json
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from api.main import app
from models.interface import PredictOutput


def sample_observation():
    path = Path(__file__).parent / "fixtures" / "observation_valid.json"
    return json.loads(path.read_text(encoding="utf-8"))


def test_active_observation_calls_model_once():
    observation = sample_observation()
    with patch("api.main.predict", return_value=PredictOutput(
        prediction="BOT", model_version="mock-v0"
    )) as mock_predict:
        with TestClient(app) as client:
            response = client.post("/v1/observations", json=observation)

    assert response.status_code == 200
    assert mock_predict.call_count == 1
    sent_to_model = mock_predict.call_args.args[0]
    assert sent_to_model.session_id == observation["session_id"]
    assert sent_to_model.browser_features.click_count == observation["browser_features"]["click_count"]

    result = response.json()
    assert result["prediction"] == "BOT"
    assert result["model_version"] == "mock-v0"
    assert result["risk_level"] is None
    assert result["data_quality"] == "SUFFICIENT"


def test_inactive_observation_does_not_call_model():
    observation = sample_observation()
    observation["browser_features"].update({
        "mouse_distance_px": 0.0,
        "click_count": 0,
        "scroll_event_count": 0,
    })
    with patch("api.main.predict") as mock_predict:
        with TestClient(app) as client:
            response = client.post("/v1/observations", json=observation)

    assert response.status_code == 200
    mock_predict.assert_not_called()
    result = response.json()
    assert result["prediction"] is None
    assert result["risk_level"] is None
    assert result["model_version"] == "mock-v0"
    assert result["data_quality"] == "INSUFFICIENT"


def test_invalid_observation_rejected_before_model():
    observation = sample_observation()
    observation["browser_features"]["click_count"] = -1
    with patch("api.main.predict") as mock_predict:
        with TestClient(app) as client:
            response = client.post("/v1/observations", json=observation)

    assert response.status_code == 422
    mock_predict.assert_not_called()
