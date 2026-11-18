from pathlib import Path
import pandas as pd
import pytest
from data.reader import (ALL_COLUMNS, FEATURE_COLUMNS, METADATA_COLUMNS,
                         read_features, validate_columns)

CSV = Path("data/synthetic_features.csv")


def test_csv_loads_with_expected_columns():
    assert list(read_features(CSV).columns) == ALL_COLUMNS


def test_features_are_the_eight_contract_names():
    assert len(FEATURE_COLUMNS) == 8
    assert not set(FEATURE_COLUMNS) & set(METADATA_COLUMNS)


def test_missing_column_raises():
    df = read_features(CSV).drop(columns=["scroll_distance_px"])
    with pytest.raises(ValueError):
        validate_columns(df)


def test_wrong_order_raises():
    df = read_features(CSV)[ALL_COLUMNS[::-1]]
    with pytest.raises(ValueError):
        validate_columns(df)


def test_invalid_label_raises():
    df = read_features(CSV)
    df.loc[0, "label"] = "robot"
    with pytest.raises(ValueError):
        validate_columns(df)


def test_missing_values_are_nan_not_zero():
    df = read_features(CSV)
    no_clicks = df[df["click_count"] == 0]
    assert no_clicks["click_interval_mean_ms"].isna().all()