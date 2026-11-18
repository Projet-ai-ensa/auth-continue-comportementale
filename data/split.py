import numpy as np
import pandas as pd


def split_by_participant(
    df: pd.DataFrame,
    train: float = 0.6,
    val: float = 0.2,
    test: float = 0.2,
    seed: int = 42,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Split rows into train/val/test so that each participant is in exactly one set.

    Participants are split separately for each label (human / bot), so every
    set contains both classes.
    """
    if abs(train + val + test - 1.0) > 1e-9:
        raise ValueError("train + val + test must equal 1.0")
    for col in ("participant_id", "label"):
        if col not in df.columns:
            raise ValueError(f"missing column: {col}")

    labels_per_participant = df.groupby("participant_id")["label"].nunique()
    if (labels_per_participant > 1).any():
        raise ValueError("a participant has more than one label")

    rng = np.random.default_rng(seed)
    train_ids, val_ids, test_ids = [], [], []

    for label, group in df.groupby("label"):
        ids = np.sort(group["participant_id"].unique())
        rng.shuffle(ids)
        n = len(ids)
        n_test = max(1, round(n * test))
        n_val = max(1, round(n * val))
        n_train = n - n_val - n_test
        if n_train < 1:
            raise ValueError(
                f"not enough participants for label '{label}': {n} "
                "(need at least 3 to fill train, val and test)"
            )
        test_ids += list(ids[:n_test])
        val_ids += list(ids[n_test:n_test + n_val])
        train_ids += list(ids[n_test + n_val:])

    return (
        df[df["participant_id"].isin(train_ids)].copy(),
        df[df["participant_id"].isin(val_ids)].copy(),
        df[df["participant_id"].isin(test_ids)].copy(),
    )