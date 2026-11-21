from pathlib import Path

import pytest

import models.interface as interface
from data.reader import FEATURE_COLUMNS
from models.interface import FEATURE_ORDER, PredictInput, predict

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


needs_model = pytest.mark.skipif(
    not interface.MODEL_PATH.exists(),
    reason="modèle entraîné absent (normal en CI)",
)


# ---------- Tests qui ne dépendent pas du fichier du modèle ----------

def test_output_is_simulated_without_model(monkeypatch):
    # on force l'absence de modèle : on teste la réponse simulée
    monkeypatch.setattr(interface, "MODEL_PATH", Path("absent.joblib"))
    monkeypatch.setattr(interface, "_artifact", None)
    out = predict(make_input())
    assert out.model_version == "mock-v0"
    assert out.prediction == "HUMAN"


def test_output_has_only_prediction_and_model_version():
    out = predict(make_input())
    assert set(out.model_dump().keys()) == {"prediction", "model_version"}


def test_feature_order_matches_data_reader():
    assert FEATURE_ORDER == FEATURE_COLUMNS
    assert len(FEATURE_ORDER) == 8


def test_input_accepts_missing_features():
    data = make_input({"click_count": 0})
    assert data.browser_features.mouse_distance_px is None
    assert data.browser_features.click_count == 0


# ---------- Tests qui utilisent le vrai modèle (ignorés s'il est absent) ----------

@needs_model
def test_obvious_human_is_human():
    out = predict(make_input())
    assert out.prediction == "HUMAN"


@needs_model
def test_obvious_bot_is_bot():
    out = predict(make_input({
        "mouse_distance_px": 2400.0,
        "mouse_speed_mean_px_s": 400.0,
        "mouse_speed_std_px_s": 4.0,
        "direction_change_count": 0,
        "click_count": 10,
        "click_interval_mean_ms": 100.0,
        "scroll_event_count": 0,
        "scroll_distance_px": 0.0,
    }))
    assert out.prediction == "BOT"


@needs_model
def test_missing_values_do_not_crash():
    out = predict(make_input({
        "mouse_distance_px": 0.0,
        "mouse_speed_mean_px_s": None,
        "mouse_speed_std_px_s": None,
        "direction_change_count": 0,
        "click_count": 0,
        "click_interval_mean_ms": None,
        "scroll_event_count": 12,
        "scroll_distance_px": 1200.0,
    }))
    assert out.prediction in {"HUMAN", "BOT"}