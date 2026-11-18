import sys
from pathlib import Path

import pandas as pd
import pytest

# Make `data/` importable whether or not it is a package
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "data"))

from explore_cmu import to_v0_keyboard_features  # noqa: E402


@pytest.fixture
def fake_cmu() -> pd.DataFrame:
    """Two fake CMU rows. Values are in SECONDS, like the real dataset."""
    return pd.DataFrame(
        {
            "subject": ["s002", "s002"],
            "sessionIndex": [1, 2],
            "rep": [1, 1],
            "H.a": [0.10, 0.20],
            "H.b": [0.20, 0.40],
            "DD.a.b": [0.30, 0.50],
            "UD.a.b": [0.99, 0.99],  # must NOT be used for interkey_mean_ms
        }
    )


def test_output_columns(fake_cmu):
    out = to_v0_keyboard_features(fake_cmu)
    assert list(out.columns) == [
        "user_id",
        "session_id",
        "hold_mean_ms",
        "interkey_mean_ms",
    ]


def test_row_count_preserved(fake_cmu):
    out = to_v0_keyboard_features(fake_cmu)
    assert len(out) == len(fake_cmu)


def test_hold_mean_converted_to_ms(fake_cmu):
    out = to_v0_keyboard_features(fake_cmu)
    # row 0: mean(0.10, 0.20) = 0.15 s -> 150 ms
    # row 1: mean(0.20, 0.40) = 0.30 s -> 300 ms
    assert out["hold_mean_ms"].tolist() == pytest.approx([150.0, 300.0])


def test_interkey_uses_dd_columns_only(fake_cmu):
    out = to_v0_keyboard_features(fake_cmu)
    # DD values 0.30 and 0.50 s -> 300 and 500 ms (UD = 990 ms would be wrong)
    assert out["interkey_mean_ms"].tolist() == pytest.approx([300.0, 500.0])


def test_session_id_format(fake_cmu):
    out = to_v0_keyboard_features(fake_cmu)
    assert out["session_id"].tolist() == ["s002_s1", "s002_s2"]
    assert out["user_id"].tolist() == ["s002", "s002"]


def test_input_dataframe_not_modified(fake_cmu):
    before = fake_cmu.copy(deep=True)
    to_v0_keyboard_features(fake_cmu)
    pd.testing.assert_frame_equal(fake_cmu, before)


def test_missing_columns_raises():
    bad = pd.DataFrame({"subject": ["s002"], "sessionIndex": [1], "rep": [1]})
    with pytest.raises(ValueError):
        to_v0_keyboard_features(bad)