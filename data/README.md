# Données et préparation

Responsable principal : Saad. Coordination avec Chahd.

Ce dossier contient les scripts de préparation, les schémas de données et la documentation des sources.

Ne pas versionner les données brutes de participants. Documenter les licences et les sources. Garder une séparation par participant et par session lors de l'évaluation.

Voir `docs/DATASETS_AND_EVALUATION.md`.

 ## CMU Keystroke Dynamics dataset
- Source: https://www.cs.cmu.edu/~keystroke/DSL-StrongPasswordData.csv
- Save as `data/raw/DSL-StrongPasswordData.csv` (not committed).
- Expected MD5: 470235f96568f28f9ea0da62234ec857
- Values are in seconds; `to_v0_keyboard_features` converts to ms.
- interkey_mean_ms is computed from DD.* columns (key down to key down).