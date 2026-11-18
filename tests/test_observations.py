import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from api.main import app

OBSERVATION_URL = "/v1/observations"


@pytest.fixture
def observation():
    fixture_path = Path(__file__).parent / "fixtures" / "observation_valid.json"
    return json.loads(fixture_path.read_text(encoding="utf-8"))


def test_accepts_valid_observation(observation):
    with TestClient(app) as client:
        response = client.post(OBSERVATION_URL, json=observation)

    assert response.status_code == 200
    result = response.json()
    assert result["session_id"] == observation["session_id"]
    assert result["window_id"] == observation["window_id"]
    assert result["model_version"] == "mock-v0"


def test_rejects_missing_window_id(observation):
    del observation["window_id"]

    with TestClient(app) as client:
        response = client.post(OBSERVATION_URL, json=observation)

    assert response.status_code == 422
    assert ["body", "window_id"] in [
        error["loc"] for error in response.json()["detail"]
    ]


def test_rejects_negative_click_count(observation):
    observation["browser_features"]["click_count"] = -1

    with TestClient(app) as client:
        response = client.post(OBSERVATION_URL, json=observation)

    assert response.status_code == 422
    assert ["body", "browser_features", "click_count"] in [
        error["loc"] for error in response.json()["detail"]
    ]