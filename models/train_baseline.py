import joblib
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from data.reader import FEATURE_COLUMNS


def make_fake_data(n=200, seed=0):
    """Données FICTIVES, seulement pour tester la chaîne."""
    rng = np.random.default_rng(seed)
    humans = pd.DataFrame({
        "mouse_distance_px": rng.normal(1000, 350, n).clip(50),
        "mouse_speed_mean_px_s": rng.normal(150, 40, n).clip(10),
        "mouse_speed_std_px_s": rng.normal(60, 15, n).clip(5),
        "direction_change_count": rng.poisson(9, n),
        "click_count": rng.poisson(3, n),
        "click_interval_mean_ms": rng.normal(1300, 400, n).clip(200),
        "scroll_event_count": rng.poisson(5, n),
        "scroll_distance_px": rng.normal(600, 200, n).clip(0),
    })
    h = n // 2
    linear = pd.DataFrame({  # bot qui bouge en ligne droite, très vite
        "mouse_distance_px": rng.normal(2400, 100, h),
        "mouse_speed_mean_px_s": rng.normal(400, 10, h),
        "mouse_speed_std_px_s": rng.normal(4, 1, h).clip(0),
        "direction_change_count": np.zeros(h, dtype=int),
        "click_count": np.full(h, 10),
        "click_interval_mean_ms": rng.normal(100, 5, h),
        "scroll_event_count": np.zeros(h, dtype=int),
        "scroll_distance_px": np.zeros(h),
    })
    no_mouse = pd.DataFrame({  # bot qui ne fait que défiler
        "mouse_distance_px": np.zeros(n - h),
        "mouse_speed_mean_px_s": np.nan,
        "mouse_speed_std_px_s": np.nan,
        "direction_change_count": np.zeros(n - h, dtype=int),
        "click_count": np.zeros(n - h, dtype=int),
        "click_interval_mean_ms": np.nan,
        "scroll_event_count": rng.poisson(12, n - h),
        "scroll_distance_px": rng.normal(1200, 200, n - h),
    })
    X = pd.concat([humans, linear, no_mouse], ignore_index=True)[FEATURE_COLUMNS]
    # un intervalle entre clics n'existe pas s'il y a moins de 2 clics
    X.loc[X["click_count"] < 2, "click_interval_mean_ms"] = np.nan
    y = np.array(["human"] * n + ["bot"] * n)
    return X, y


if __name__ == "__main__":
    X, y = make_fake_data()
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, stratify=y, random_state=0
    )

    model = Pipeline([
        ("imputer", SimpleImputer(strategy="median", add_indicator=True)),
        ("scaler", StandardScaler()),
        ("clf", LogisticRegression()),
    ])
    model.fit(X_train, y_train)

    pred = model.predict(X_test)
    print("accuracy:", accuracy_score(y_test, pred))
    print(confusion_matrix(y_test, pred, labels=["human", "bot"]))

    joblib.dump(
        {
            "pipeline": model,
            "feature_order": FEATURE_COLUMNS,
            "model_version": "baseline-fake-v0",
        },
        "models/baseline_fake.joblib",
    )
    print("modèle sauvegardé")