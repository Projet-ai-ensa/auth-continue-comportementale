# Modèles de machine learning

Responsable principal : Chahd. Coordination du format des données avec Saad.

Ce dossier contient :
- l'entraînement ;
- le prétraitement ;
- la comparaison des modèles ;
- l'évaluation ;
- l'export des pipelines.

Modèles de départ prévus : Logistic Regression, Random Forest et HistGradientBoosting.
Pour l'instant, seule la Logistic Regression est implémentée (modèle de base).

Le prétraitement est inclus dans le pipeline exporté. Aucune performance n'est annoncée
avant l'évaluation sur de vraies données.

## Fichiers

| Fichier | Rôle |
|---|---|
| `interface.py` | Schémas d'entrée et de sortie de `predict()` et fonction `predict()` |
| `train_baseline.py` | Entraînement du modèle de base et évaluation sur la validation |
| `baseline_fake.joblib` | Modèle entraîné sur données fictives (généré, non versionné) |

## Entraîner le modèle de base

Depuis la racine du projet, avec l'environnement virtuel activé :

```
python -m models.train_baseline
```

Le script :
1. génère des données **fictives** (même colonnes que `data/reader.py`) ;
2. sépare train / validation / test **par participant** avec `data/split.py` ;
3. entraîne un pipeline : imputation → normalisation → régression logistique ;
4. affiche l'accuracy, les faux positifs et les faux négatifs sur la validation ;
5. sauvegarde le pipeline dans `models/baseline_fake.joblib`.

Le jeu de test n'est pas utilisé pendant le développement.
Les résultats sur données fictives ne mesurent pas la qualité du modèle : ils servent
seulement à vérifier que la chaîne fonctionne.

## Contenu du fichier sauvegardé

Un dictionnaire `joblib` avec :
- `pipeline` : imputer + scaler + classifieur ;
- `feature_order` : la liste `FEATURE_COLUMNS` de `data/reader.py` (ordre des 8 mesures) ;
- `model_version` : par exemple `baseline-fake-v0`.

Les fichiers `*.joblib` sont ignorés par Git. Pour obtenir le modèle, relancer l'entraînement.

## Utilisation : `predict()`

Entrée (`PredictInput`) : les champs de l'observation envoyée par le collecteur, dont
`browser_features` avec les 8 mesures de `FEATURE_COLUMNS`.

Sortie (`PredictOutput`) : uniquement
- `prediction` : `"HUMAN"` ou `"BOT"` ;
- `model_version`.

`session_id`, `window_id`, `data_quality` et `risk_level` sont gérés par l'API.

Si le fichier du modèle est absent, `predict()` renvoie une réponse simulée
(`model_version = "mock-v0"`).

## Valeurs manquantes

- Un zéro reste un zéro.
- Seules `mouse_speed_mean_px_s`, `mouse_speed_std_px_s` et `click_interval_mean_ms`
  peuvent être `null` (à confirmer avec Hiba). Les cinq autres mesures sont obligatoires.
- Une valeur `null` est remplacée par la médiane du jeu d'entraînement, et une colonne
  indicatrice signale qu'elle manquait.
- Une fenêtre sans aucune activité n'est pas envoyée au modèle : c'est
  `data_quality: INSUFFICIENT` côté API.

## À décider

- Convention des étiquettes (`HUMAN`/`BOT` ou `human`/`bot`) avec Imrane.
- Besoin d'un score (probabilité) en plus de la prédiction, pour le niveau de risque.
- Comment l'API obtient le fichier du modèle.
- Comparaison avec Random Forest et HistGradientBoosting sur les vraies données.