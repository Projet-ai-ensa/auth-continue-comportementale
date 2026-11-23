from pathlib import Path

import pytest
from pydantic import ValidationError

import models.interface as interface
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

BOT_FEATURES = {
    "mouse_distance_px": 2400.0,
    "mouse_speed_mean_px_s": 400.0,
    "mouse_speed_std_px_s": 4.0,
    "direction_change_count": 0,
    "click_count": 10,
    "click_interval_mean_ms": 100.0,
    "scroll_event_count": 0,
    "scroll_distance_px": 0.0,
}

NO_MOUSE_FEATURES = {
    "mouse_distance_px": 0.0,
    "mouse_speed_mean_px_s": None,
    "mouse_speed_std_px_s": None,
    "direction_change_count": 0,
    "click_count": 0,
    "click_interval_mean_ms": None,
    "scroll_event_count": 12,
    "scroll_distance_px": 1200.0,
}

needs_model = pytest.mark.skipif(
    not interface.MODEL_PATH.exists(),
    reason="modèle entraîné absent (normal en CI)",
)


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


# ---------- Contrat d'entrée et de sortie (indépendant du modèle) ----------

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


# ---------- Tests avec le vrai modèle (ignorés s'il est absent) ----------

@needs_model
def test_obvious_human_is_human():
    assert predict(make_input()).prediction == "HUMAN"


@needs_model
def test_obvious_bot_is_bot():
    assert predict(make_input(BOT_FEATURES)).prediction == "BOT"


@needs_model
def test_missing_values_do_not_crash():
    out = predict(make_input(NO_MOUSE_FEATURES))
    assert out.prediction in {"HUMAN", "BOT"}