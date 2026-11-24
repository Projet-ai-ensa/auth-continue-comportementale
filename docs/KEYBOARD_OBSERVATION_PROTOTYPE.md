# Prototype d'observation clavier agrégée

**Statut provisoire, pour démonstration locale.** Ce format reprend l'exemple
illustratif de la [proposition de contrat (PR #17)](https://github.com/Projet-ai-ensa/auth-continue-comportementale/pull/17).
Le code du collecteur et un export JSON anonymisé de Hiba restent à vérifier
avant de valider l'interopérabilité.

## Requête

Envoyer un JSON à `POST /v1/keyboard-observations`. Le fichier
[de test synthétique](../tests/fixtures/keyboard_observation_provisional.json)
contient un exemple complet.

- Utiliser `schema_version: "keyboard-proposal-1"`, des identifiants de
  session et de fenêtre pseudonymes sous forme de chaînes non vides, un
  horodatage avec fuseau horaire, une durée entière strictement positive en
  millisecondes et une version du collecteur non vide.
- Envoyer les comptages entiers non négatifs dans `keyboard_features` et
  reporter les mêmes comptages dans `quality`. Indiquer également les nombres
  d'appuis expirés et d'intervalles incomplets.
- Fournir `hold_mean_ms` (durée moyenne des appuis) et `flight_mean_ms` et
  `flight_min_ms` (moyenne et minimum des intervalles entre événements de
  frappe). Les statistiques sont finies. Le temps d'appui est non négatif.
  Les intervalles de frappe peuvent être signés pour représenter un
  chevauchement éventuel, sous réserve de confirmation par Hiba.
- Mettre les statistiques à `null` lorsque leur comptage vaut zéro.
  Utiliser `quality.status: "no_data"` si les deux comptages valent zéro et
  `"collected"` si au moins une statistique est disponible.
- Convertir les secondes en millisecondes côté émetteur si nécessaire. La
  forme historique décrite dans la proposition (identifiant entier,
  `duration_seconds`, `features: {}`) doit être adaptée avant l'envoi.

Les champs supplémentaires sont rejetés à tous les niveaux. Envoyer
uniquement des agrégats et les métadonnées prévues. Générer les identifiants
indépendamment des données de frappe.

## Réponse

HTTP 200 confirme la validation seule. Le prototype traite les agrégats en
mémoire le temps de la requête, sans stockage ni appel au modèle.

```json
{"status": "validated", "collection_status": "collected"}
```

HTTP 422 indique une requête invalide avec un message fixe qui ne reprend
aucune donnée soumise.

```json
{"detail": "Invalid keyboard observation."}
```

## Démonstration locale

Depuis la racine du dépôt, avec l'API lancée via `python -m uvicorn api.main:app` :

```sh
curl -H "Content-Type: application/json" --data-binary "@tests/fixtures/keyboard_observation_provisional.json" http://127.0.0.1:8000/v1/keyboard-observations
```

## Validation par l'équipe

Comparer le format, les unités, la définition et le signe des intervalles,
ainsi que les fenêtres partielles et vides, avec un export anonymisé du
collecteur. Utiliser les données synthétiques pour cette démonstration.
Avant toute collecte réelle, appliquer les règles de consentement de
[confidentialité](SECURITY_AND_PRIVACY.md) et valider les contrôles d'accès,
les limites de taille et de fréquence, et la rétention.
