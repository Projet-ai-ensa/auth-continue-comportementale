# Collecteur comportemental Python

Responsable principal : Hiba.
Coordination du contrat API : Imrane.

## Présentation

Ce dossier contient le collecteur comportemental Python.
Il capture et traite les événements autorisés du clavier et
de la souris afin de calculer des caractéristiques agrégées
sur des fenêtres temporelles.

## Organisation

- `python/events.py` : capture et traitement des événements clavier.
- `python/features.py` : calcul des caractéristiques temporelles clavier.
- `python/quality.py` : évaluation de la qualité des données.
- `python/mouse.py` : capture et traitement des événements souris.
- `python/windows.py` : gestion des fenêtres temporelles et JSON.
- `python/session.py` : orchestration des sessions de capture.
- `python/api_client.py` : client HTTP pour la transmission des données.

## Installation

Depuis la racine du projet :

    python -m pip install -r requirements.txt

## Sécurité et confidentialité

- Ne jamais enregistrer les caractères saisis.
- Ne jamais enregistrer les mots de passe ou le contenu des champs.
- Transmettre uniquement des caractéristiques agrégées.
- Respecter le contrat défini dans `docs/API_CONTRACT.md`.

## Tests

La syntaxe des modules peut être vérifiée avec :

    python -m compileall collector/python

Les tests fonctionnels et d'intégration doivent être exécutés
avant toute intégration dans la branche principale.

## Contrat API

Le format de transmission doit être validé avec le responsable
du backend avant l'intégration réelle.
