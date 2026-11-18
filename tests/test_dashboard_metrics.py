import pandas as pd

from dashboard.metrics import average_by_label, summarize
from data.reader import read_features


def make_df():
    # A tiny fake table: 2 human windows + 1 bot window
    return pd.DataFrame({
        "participant_id": ["p01", "p01", "b01"],
        "session_id": ["s1", "s1", "s2"],
        "label": ["human", "human", "bot"],
        "mouse_speed_mean_px_s": [100.0, 200.0, None],
    })


def test_summary_counts():
    s = summarize(make_df())
    assert s["windows"] == 3
    assert s["sessions"] == 2
    assert s["participants"] == 2


def test_empty_data_does_not_crash():
    s = summarize(make_df().iloc[0:0])
    assert s["windows"] == 0


def test_average_of_humans():
    avg = average_by_label(make_df(), "mouse_speed_mean_px_s").set_index("label")
    assert avg.loc["human", "mouse_speed_mean_px_s"] == 150.0


def test_summary_on_team_csv():
    s = summarize(read_features("data/synthetic_features.csv"))
    assert s["windows"] == 6
    assert s["bot_share"] == 50.0