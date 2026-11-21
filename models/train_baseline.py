import sys

import joblib
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from data.reader import ALL_COLUMNS, FEATURE_COLUMNS, read_features
from data.split import split_by_participant


def make_fake_data(n_humans=20, n_bots=20, windows=10, seed=0):
    """Données FICTIVES (un DataFrame comme le CSV de Saad), pour tester la chaîne."""
    rng = np.random.default_rng(seed)
    rows = []

    for i in range(n_humans):
        pid = f"p{i:02d}"
        style = rng.normal(1.0, 0.2)  # habitude personnelle de ce participant
        for w in range(windows):
            clicks = int(rng.poisson(3 * style))
            rows.append({
                "participant_id": pid, "session_id": f"sess-{pid}",
                "window_id": f"w{w:04d}", "label": "human", "bot_config": None,
                "mouse_distance_px": max(50, rng.normal(1000 * style, 300)),
                "mouse_speed_mean_px_s": max(10, rng.normal(150 * style, 35)),
                "mouse_speed_std_px_s": max(5, rng.normal(60, 15)),
                "direction_change_count": int(rng.poisson(9)),
                "click_count": clicks,
                "click_interval_mean_ms": max(200, rng.normal(1300, 400)) if clicks >= 2 else np.nan,
                "scroll_event_count": int(rng.poisson(5)),
                "scroll_distance_px": max(0, rng.normal(600, 200)),
            })

    for i in range(n_bots):
        pid = f"b{i:02d}"
        no_mouse = i % 2 == 1
        for w in range(windows):
            if no_mouse:  # bot qui ne fait que défiler
                rows.append({
                    "participant_id": pid, "session_id": f"sess-{pid}",
                    "window_id": f"w{w:04d}", "label": "bot", "bot_config": "no-mouse",
                    "mouse_distance_px": 0.0, "mouse_speed_mean_px_s": np.nan,
                    "mouse_speed_std_px_s": np.nan, "direction_change_count": 0,
                    "click_count": 0, "click_interval_mean_ms": np.nan,
                    "scroll_event_count": int(rng.poisson(12)),
                    "scroll_distance_px": rng.normal(1200, 200),
                })
            else:  # bot qui bouge en ligne droite, très vite
                rows.append({
                    "participant_id": pid, "session_id": f"sess-{pid}",
                    "window_id": f"w{w:04d}", "label": "bot", "bot_config": "linear-fast",
                    "mouse_distance_px": rng.normal(2400, 100),
                    "mouse_speed_mean_px_s": rng.normal(400, 10),
                    "mouse_speed_std_px_s": max(0, rng.normal(4, 1)),
                    "direction_change_count": 0, "click_count": 10,
                    "click_interval_mean_ms": rng.normal(100, 5),
                    "scroll_event_count": 0, "scroll_distance_px": 0.0,
                })

    return pd.DataFrame(rows)[ALL_COLUMNS]


def evaluate(model, df, name):
    pred = model.predict(df[FEATURE_COLUMNS])
    tn, fp, fn, tp = confusion_matrix(df["label"], pred, labels=["human", "bot"]).ravel()
    print(f"--- {name} ({len(df)} fenêtres) ---")
    print("accuracy:", round(accuracy_score(df["label"], pred), 3))
    print(f"humains pris pour des bots (faux positifs): {fp}")
    print(f"bots pris pour des humains (faux négatifs): {fn}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        df = read_features(sys.argv[1])  # vraies données de Saad
        model_version = "baseline-v0"
    else:
        df = make_fake_data()            # données fictives
        model_version = "baseline-fake-v0"

    train, val, test = split_by_participant(df)

    # Sécurité : aucun participant ne doit être dans deux ensembles
    ids = [set(d["participant_id"]) for d in (train, val, test)]
    assert not (ids[0] & ids[1] or ids[0] & ids[2] or ids[1] & ids[2])

    model = Pipeline([
        ("imputer", SimpleImputer(strategy="median", add_indicator=True)),
        ("scaler", StandardScaler()),
        ("clf", LogisticRegression()),
    ])
    model.fit(train[FEATURE_COLUMNS], train["label"])

    evaluate(model, val, "validation")
    # Le jeu de test ne se regarde qu'une seule fois, à la toute fin du projet.

    joblib.dump(
        {
            "pipeline": model,
            "feature_order": FEATURE_COLUMNS,
            "model_version": model_version,
        },
        "models/baseline_fake.joblib",
    )
    print("modèle sauvegardé")