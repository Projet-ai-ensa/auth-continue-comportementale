from data.reader import FEATURE_COLUMNS


def payload_to_row(payload: dict) -> dict:
    """Flatten an API payload into a dataset row (features + session_id/window_id).

    participant_id, label and bot_config are not in the payload; the dataset
    builder adds them from the collection protocol.
    """
    features = payload["browser_features"]
    missing = [c for c in FEATURE_COLUMNS if c not in features]
    extra = [k for k in features if k not in FEATURE_COLUMNS]
    if missing or extra:
        raise ValueError(f"missing features: {missing}; unexpected features: {extra}")
    row = {"session_id": payload["session_id"], "window_id": payload["window_id"]}
    row.update({c: features[c] for c in FEATURE_COLUMNS})
    return row