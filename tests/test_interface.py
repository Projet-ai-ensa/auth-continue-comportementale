import pytest
from pydantic import ValidationError

from data.reader import FEATURE_COLUMNS
from models.interface import FEATURE_ORDER, PredictInput, SessionFeatures, predict

NULLABLE = ["mouse_speed_mean_px_s", "mouse_speed_std_px_s", "click_interval_mean_ms"]
NOT_NULLABLE = [c for c in FEATURE_COLUMNS if c not in NULLABLE]

EXAMPLE_FEATURES = {
    "mouse_distance_px": 1200.0,
    "mouse_speed_mean_px_s": 180.0,
    "mouse_speed_std_px_s": 55.0,
    "direction_change_count": 8,
    "click_count": 4,
    "click_interval_mean_ms": 850.0,
    "scroll_event_count": 6,
    "scroll_distance_px": 720.0,
}


def make_input(features=None):
    return PredictInput(
        session_id="s1",
        window_id="w1",
        window_started_at="2026-11-21T10:00:00Z",
        window_duration_ms=30000,
        collector_version="0.1.0",
        browser_features=features if features is not None else EXAMPLE_FEATURES,
    )


def with_value(name, value):
    return {**EXAMPLE_FEATURES, name: value}


def without_key(name):
    return {k: v for k, v in EXAMPLE_FEATURES.items() if k != name}


def test_output_is_simulated():
    out = predict(make_input())
    assert out.model_version == "mock-v0"
    assert out.prediction == "HUMAN"


def test_output_has_only_prediction_and_model_version():
    out = predict(make_input())
    assert set(out.model_dump().keys()) == {"prediction", "model_version"}


def test_feature_order_matches_data_reader():
    assert list(SessionFeatures.model_fields) == FEATURE_COLUMNS
    assert FEATURE_ORDER == FEATURE_COLUMNS
    assert len(FEATURE_ORDER) == 8


@pytest.mark.parametrize("name", NULLABLE)
def test_nullable_feature_accepts_none(name):
    data = make_input(with_value(name, None))
    assert getattr(data.browser_features, name) is None


@pytest.mark.parametrize("name", NOT_NULLABLE)
def test_non_nullable_feature_rejects_none(name):
    with pytest.raises(ValidationError):
        make_input(with_value(name, None))


@pytest.mark.parametrize("name", FEATURE_COLUMNS)
def test_missing_key_is_rejected(name):
    with pytest.raises(ValidationError):
        make_input(without_key(name))


def test_unknown_key_is_rejected():
    with pytest.raises(ValidationError):
        make_input({**EXAMPLE_FEATURES, "typing_speed": 3.0})


def test_zero_stays_zero():
    data = make_input(with_value("click_count", 0))
    assert data.browser_features.click_count == 0