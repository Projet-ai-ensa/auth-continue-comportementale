import pandas as pd
import pytest

from data.split import split_by_participant


def make_df(n_humans=10, n_bots=10, windows=3) -> pd.DataFrame:
    rows = []
    for label, prefix, n in (("human", "p", n_humans), ("bot", "b", n_bots)):
        for i in range(n):
            for w in range(windows):
                rows.append(
                    {
                        "participant_id": f"{prefix}{i:02d}",
                        "session_id": f"{prefix}{i:02d}_s0",
                        "label": label,
                        "window_id": f"w{w}",
                    }
                )
    return pd.DataFrame(rows)


def ids(df):
    return set(df["participant_id"])


def test_no_participant_in_two_sets():
    tr, va, te = split_by_participant(make_df())
    assert not ids(tr) & ids(va)
    assert not ids(tr) & ids(te)
    assert not ids(va) & ids(te)


def test_all_rows_kept():
    df = make_df()
    tr, va, te = split_by_participant(df)
    assert len(tr) + len(va) + len(te) == len(df)


def test_every_set_has_both_classes():
    for part in split_by_participant(make_df()):
        assert set(part["label"]) == {"human", "bot"}


def test_same_seed_same_split():
    a = split_by_participant(make_df(), seed=1)
    b = split_by_participant(make_df(), seed=1)
    for x, y in zip(a, b):
        assert ids(x) == ids(y)


def test_too_few_participants_raises():
    with pytest.raises(ValueError):
        split_by_participant(make_df(n_humans=2))


def test_mixed_label_participant_raises():
    df = make_df()
    df.loc[0, "label"] = "bot"  # p00 now has two labels
    with pytest.raises(ValueError):
        split_by_participant(df)


def test_bad_fractions_raise():
    with pytest.raises(ValueError):
        split_by_participant(make_df(), train=0.5, val=0.2, test=0.2)

def test_no_session_in_two_sets():
    tr, va, te = split_by_participant(make_df())
    s = lambda d: set(d["session_id"])
    assert not s(tr) & s(va)
    assert not s(tr) & s(te)
    assert not s(va) & s(te)


def test_session_shared_by_two_participants_raises():
    df = make_df()
    df.loc[df["participant_id"] == "p01", "session_id"] = "p00_s0"
    with pytest.raises(ValueError):
        split_by_participant(df)   