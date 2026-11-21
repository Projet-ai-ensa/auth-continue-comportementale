import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from data.reader import FEATURE_COLUMNS
from data.split import split_by_participant
from models.train_baseline import make_fake_data


def build_models():
    def imputer():
        return SimpleImputer(strategy="median", add_indicator=True)

    return {
        "logistic_regression": Pipeline([
            ("imputer", imputer()),
            ("scaler", StandardScaler()),
            ("clf", LogisticRegression()),
        ]),
        "random_forest": Pipeline([
            ("imputer", imputer()),
            ("clf", RandomForestClassifier(n_estimators=200, random_state=0)),
        ]),
        # gère les valeurs manquantes tout seul, pas besoin d'imputer
        "hist_gradient_boosting": Pipeline([
            ("clf", HistGradientBoostingClassifier(random_state=0)),
        ]),
    }


if __name__ == "__main__":
    df = make_fake_data()
    train, val, _test = split_by_participant(df)  # le test n'est pas utilisé ici

    rows = []
    for name, model in build_models().items():
        model.fit(train[FEATURE_COLUMNS], train["label"])
        pred = model.predict(val[FEATURE_COLUMNS])
        tn, fp, fn, tp = confusion_matrix(
            val["label"], pred, labels=["human", "bot"]
        ).ravel()
        rows.append({
            "modèle": name,
            "accuracy": round(accuracy_score(val["label"], pred), 3),
            "faux positifs (humain pris pour bot)": fp,
            "faux négatifs (bot pris pour humain)": fn,
        })

    print(pd.DataFrame(rows).to_string(index=False))