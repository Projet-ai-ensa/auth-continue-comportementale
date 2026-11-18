import pandas as pd
import pytest

from data.reader import EXPECTED_COLUMNS, FEATURE_COLUMNS, read_features

CSV_PATH = "data/synthetic_features.csv"


def test_valid_file_is_read():
    df = read_features(CSV_PATH)
    assert list(df.columns) == EXPECTED_COLUMNS
    assert len(FEATURE_COLUMNS) == 6
    assert len(df) == 6


def test_missing_values_stay_nan_not_zero():
    df = read_features(CSV_PATH)
    assert df["mouse_distance_px"].isna().sum() == 1
    assert df["key_count"].isna().sum() == 1


def test_wrong_column_name_is_rejected(tmp_path):
    bad = pd.read_csv(CSV_PATH).rename(columns={"key_count": "keys"})
    f = tmp_path / "bad.csv"
    bad.to_csv(f, index=False)
    with pytest.raises(ValueError):
        read_features(f)


def test_missing_column_is_rejected(tmp_path):
    bad = pd.read_csv(CSV_PATH).drop(columns=["click_count"])
    f = tmp_path / "bad.csv"
    bad.to_csv(f, index=False)
    with pytest.raises(ValueError):
        read_features(f)


def test_reordered_columns_are_rejected(tmp_path):
    df = pd.read_csv(CSV_PATH)
    bad = df[list(reversed(df.columns))]
    f = tmp_path / "bad.csv"
    bad.to_csv(f, index=False)
    with pytest.raises(ValueError):
        read_features(f)