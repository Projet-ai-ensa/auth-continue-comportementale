# Contrat API — proposition initiale

Ce document propose une première interface entre le collecteur et FastAPI. Le schéma reste à valider par Imrane et Hiba avant le développement.

## 1. Principes

- JSON avec version de schéma.
- Identifiant de session pseudonyme.
- Fenêtres d'observation identifiées.
- Caractéristiques numériques agrégées.
- Aucun texte saisi ni valeur de touche.
- Validation côté serveur.
- Taille et fréquence des requêtes limitées.

## 2. Exemple de requête

```json
{
  "schema_version": "1.0",
  "session_id": "session-pseudonyme",
  "window_id": "window-0001",
  "window_started_at": "2026-11-17T10:00:00Z",
  "window_duration_ms": 30000,
  "collector_version": "0.1.0",
  "browser_features": {
    "mouse_distance_px": 1200.0,
    "mouse_speed_mean_px_s": 180.0,
    "mouse_speed_std_px_s": 55.0,
    "direction_change_count": 8,
    "click_count": 4,
    "click_interval_mean_ms": 850.0,
    "scroll_event_count": 6,
    "scroll_distance_px": 720.0
  }
}
```

Les valeurs sont illustratives. Le schéma final doit définir les champs facultatifs, les unités, les valeurs nulles et la gestion des fenêtres inactives.

## 3. Réponse proposée

```json
{
  "session_id": "session-pseudonyme",
  "window_id": "window-0001",
  "prediction": "HUMAN",
  "risk_level": "LOW",
  "model_version": "baseline-0.1",
  "data_quality": "SUFFICIENT"
}
```

Les valeurs possibles de prédiction sont à confirmer. Une classe et un score brut ne sont pas une probabilité calibrée.

## 4. Erreurs

- 400 : schéma invalide.
- 401 : client non autorisé.
- 413 : requête trop volumineuse.
- 422 : valeurs incohérentes.
- 429 : fréquence excessive.
- 500 : erreur interne.

## 5. Points à valider

- Noms finaux des caractéristiques.
- Fenêtre d'observation.
- Authentification du collecteur.
- Idempotence et détection de doublons.
- Champs de logs serveur.
- Gestion des données manquantes.
