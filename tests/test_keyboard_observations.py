import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from api.main import app

URL = "/v1/keyboard-observations"


@pytest.fixture
def observation():
    path = Path(__file__).parent / "fixtures" / "keyboard_observation_provisional.json"
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_accepts_signed_aggregates_without_inference(client, observation, monkeypatch):
    def unexpected_prediction(*args, **kwargs):
        pytest.fail("Keyboard validation must not call predict")

    monkeypatch.setattr("api.main.predict", unexpected_prediction)
    response = client.post(URL, json=observation)

    assert response.status_code == 200
    assert response.json() == {"status": "validated", "collection_status": "collected"}


@pytest.mark.parametrize("has_hold", [False, True])
def test_accepts_empty_and_hold_only_windows(client, observation, has_hold):
    features = observation["keyboard_features"]
    quality = observation["quality"]
    features.update(hold_count=int(has_hold), hold_mean_ms=90 if has_hold else None)
    features.update(flight_count=0, flight_mean_ms=None, flight_min_ms=None)
    status = "collected" if has_hold else "no_data"
    quality.update(hold_count=int(has_hold), flight_count=0, expired_hold_count=1, status=status)

    response = client.post(URL, json=observation)

    assert response.status_code == 200
    assert response.json() == {"status": "validated", "collection_status": status}


@pytest.mark.parametrize(
    ("group", "field", "value"),
    [
        (None, "schema_version", "1.0"),
        (None, "window_id", 1),
        (None, "window_started_at", 0),
        (None, "window_started_at", "2026-11-23T12:00:00"),
        (None, "window_duration_ms", -1),
        (None, "window_duration_ms", 0),
        (None, "window_duration_ms", 30000.0),
        (None, "text", "fixture-only"),
        ("keyboard_features", "key_events", ["fixture-only"]),
        ("keyboard_features", "hold_count", -1),
        ("keyboard_features", "hold_count", True),
        ("keyboard_features", "hold_mean_ms", -1),
        ("keyboard_features", "hold_mean_ms", None),
        ("keyboard_features", "flight_min_ms", 600),
        ("keyboard_features", "flight_mean_ms", "520.45"),
        ("quality", "key", "fixture-only"),
        ("quality", "expired_hold_count", -1),
        ("quality", "flight_count", 9),
        ("quality", "status", "no_data"),
    ],
)
def test_rejects_invalid_payload_without_echoing_input(client, observation, group, field, value):
    target = observation if group is None else observation[group]
    target[field] = value
    response = client.post(URL, json=observation)

    assert response.status_code == 422
    assert response.json() == {"detail": "Invalid keyboard observation."}


@pytest.mark.parametrize("number", ["NaN", "Infinity", "-Infinity"])
def test_rejects_nonfinite_numbers(client, observation, number):
    body = json.dumps(observation).replace("-26.42", number)
    response = client.post(URL, content=body, headers={"Content-Type": "application/json"})

    assert response.status_code == 422
    assert response.json() == {"detail": "Invalid keyboard observation."}


def test_rejects_malformed_json_without_echoing_input(client):
    response = client.post(
        URL, content='{"text": "fixture-only"', headers={"Content-Type": "application/json"}
    )

    assert response.status_code == 422
    assert response.json() == {"detail": "Invalid keyboard observation."}
