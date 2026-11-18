import json
from pathlib import Path

import pandas as pd
import pytest

from data.payload import payload_to_row
from data.reader import FEATURE_COLUMNS

EXAMPLE = Path("tests/fixtures/observation_example.json")


def load():
    return json.loads(EXAMPLE.read_text(encoding="utf-8"))


def test_example_keys_match_feature_columns():
    assert list(load()["browser_features"]) == FEATURE_COLUMNS


def test_row_has_ids_and_all_features():
    row = payload_to_row(load())
    assert row["session_id"] == "session-pseudonyme"
    assert row["window_id"] == "window-0001"
    assert all(c in row for c in FEATURE_COLUMNS)


def test_null_feature_becomes_nan():
    payload = load()
    payload["browser_features"]["click_interval_mean_ms"] = None
    row = pd.DataFrame([payload_to_row(payload)])
    assert row["click_interval_mean_ms"].isna().all()


def test_unknown_feature_raises():
    payload = load()
    payload["browser_features"]["key_count"] = 5
    with pytest.raises(ValueError):
        payload_to_row(payload)