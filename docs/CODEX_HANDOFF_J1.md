# PASSATION VERS CODEX — J1

> Statut : projet académique, conception initiale. Document de contexte à lire avant tout changement.

## 1. Sujet EXACT

**Authentification continue comportementale par intelligence artificielle** sur un poste de travail.

L'agent local collecte des **mesures de temps clavier et de mouvement souris**, sans stocker les caractères ni les mots de passe. Le backend compare des fenêtres de caractéristiques à un profil de référence appris lors de l'enrôlement. Un moteur de décision propose une action. Le dashboard expose les scores, alertes et résultats.

**Ne pas transformer ce sujet en « détection de bots web ».** La branche `docs/behavioral-bot-detection-restructure` concerne une ancienne direction non retenue ici. Ne pas la fusionner automatiquement.

## 2. Équipe et mode de travail

- **Imrane** : référent API FastAPI, architecture et coordination technique. Travaille physiquement avec Hiba.
- **Hiba** : référente agent local, capture et features clavier/souris. Travaille physiquement avec Imrane.
- **Saad** : référent données et prétraitement. Travaille physiquement avec Chahd.
- **Chahd** : référente entraînement et évaluation ML. Travaille physiquement avec Saad.
- **Yahya** : référent dashboard, intégration et tests ; disponible pour aider tous les membres.

**Objectif pédagogique** : chaque personne code, participe aux revues et apprend l'ensemble des composants. Pair programming avec échange driver/navigator toutes les 25 minutes ; revues croisées et rotations courtes. **Objectif production** : MVP intégré et démontrable en 10 jours.

**Environnement :** VS Code, Git et GitHub. Pas de push direct sur `main`. Petites branches par fonctionnalité ; tests et revue avant fusion.

## 3. Architecture cible (proposition à valider)

```text
Poste utilisateur
  Agent Python / pynput
     -> agrégation d'événements en fenêtres (30 s pour première démo)
     -> extraction de caractéristiques sans texte saisi
     -> requête HTTP/JSON authentifiée
Serveur FastAPI
     -> validation des données
     -> prétraitement identique à l'entraînement
     -> modèle de comportement de l'utilisateur
     -> moteur de décision / qualité des observations
     -> SQLite (historique, modèles, décisions)
     -> réponse JSON à l'agent
Dashboard Streamlit
     -> lit les résultats du backend (pas de décision locale)
```

**Deux phases :**
1. Enrôlement : recueillir plusieurs sessions légitimes et apprendre un profil.
2. Surveillance : comparer les nouvelles fenêtres au profil.

**Cloud :** optionnel après MVP local ; ne pas activer de déploiement ou de frais sans autorisation.

## 4. Recherche et limites

- CMU Keystroke Dynamics : données de rythme de frappe sur **mot de passe fixe** ; ne démontre pas à lui seul une authentification continue sur texte libre.
- Balabit Mouse Dynamics : souris, autres participants et autre protocole ; ne pas fusionner naïvement les lignes de CMU et Balabit.
- Pour la démonstration multimodale : collecte volontaire de sessions propres à l'équipe avec consentement.
- Modèles envisagés : Isolation Forest et One-Class SVM en priorité ; autoencoder seulement si le calendrier et les données le permettent.
- Mesures : FAR, FRR, EER, délai de détection, fenêtres insuffisantes, robustesse. Éviter les fuites de données entre sessions/personnes.
- Ne pas qualifier un score 0–100 de probabilité sans calibration ; seuils et règles de verrouillage restent à valider.
- Les fenêtres sans activité doivent donner un état « INSUFFICIENT_DATA », pas une accusation d'imposture.
- Pas de verrouillage automatique réel sans chemin de récupération testé. Utiliser une action simulée pour le premier MVP.

## 5. Contrat d'entrée provisoire (EXEMPLE, NON GELÉ)

```json
{
  "schema_version": "0.1",
  "user_id": "demo_user_01",
  "session_id": "demo_session_01",
  "window_id": "w0001",
  "duration_seconds": 30,
  "features": {
    "key_count": 85,
    "hold_mean_ms": 115.4,
    "interkey_mean_ms": 210.2,
    "mouse_distance_px": 1500.0,
    "mouse_speed_mean_px_s": 160.0,
    "click_count": 6
  }
}
```

Contrat de sortie **simulé** :
```json
{
  "session_id": "demo_session_01",
  "window_id": "w0001",
  "model_version": "mock-v0",
  "data_quality": "SUFFICIENT",
  "score": null,
  "decision": "NORMAL"
}
```

**À résoudre collectivement avant de stabiliser les contrats** : durée de fenêtre, règles de gestion des données absentes, unité et définition exactes des intervalles de frappe, authenticité du client, ordre des features, routes et erreurs HTTP, sens du score et gestion des profils.

## 6. J1 — Tous présents ensemble au café

**Objectif :** cinq personnes actives et un premier trajet fictif agent → API → dashboard, plus des contrats compris par tous.

1. 20 min : chacun explique la problématique, l'enrôlement et la surveillance.
2. 40 min : dessiner le flux et les composants.
3. 35 min : décider des features et rédiger le contrat provisoire.
4. 25 min : vérifier VS Code, GitHub, branches et préparer 5 petites issues.
5. 70 min : chacun code une petite tâche en parallèle.
6. 30 min : démonstration fictive et revue croisée.
7. 20 min : noter les blocages et le plan J2.

Premières tâches indépendantes :
- Hiba : calcul de durées d'appui sur événements **synthétiques** + test.
- Imrane : schéma Pydantic et endpoint API simulé + test.
- Saad : petit CSV synthétique de features + validation de colonnes.
- Chahd : interface de prédiction simulée + test et définition du futur artefact.
- Yahya : dashboard Streamlit alimenté par réponse simulée + contrôle des champs.

## 7. Calendrier

- J1 : compréhension, architecture, contrats, mocks et premières PR.
- J2–J3 : agent, datasets, baseline ML, API et dashboard en parallèle.
- J4 : premier flux réel agent → API → dashboard.
- J5–J6 : vrai modèle, décision, historique et tests.
- J7 : MVP local intégré.
- J8 : collecte consentie et tests d'imposture.
- J9 : FAR/FRR/EER, robustesse et corrections.
- J10 : documentation, présentation et démonstration.

Si le temps manque, prioriser un **flux complet simple** et des résultats scientifiques honnêtes. Reporter fonctions réseau, cloud, autoencoder coûteux et verrouillage réel.

## 8. Protocole de travail pour Codex

- Commencer par **inspecter le dépôt** et l'état des branches/PR. Ne pas supposer que les fichiers décrits ici existent déjà.
- Lire ce document et `AGENTS.md`.
- Première action demandée : proposer une liste d'issues J1 et les contrats techniques, **sans générer l'ensemble du projet d'un seul coup**.
- Pour chaque tâche : objectif, fichiers, entrées/sorties, tests, dépendances, risques, Definition of Done.
- Ne pas écraser le travail déjà présent ; ne pas modifier `main` directement.
- Toutes les décisions non validées sont des **propositions**, pas des obligations définitives.
- Rédiger les explications en **français clair**, phrases simples, terminologie cohérente (style inspiré d'ASD-STE100).
- Travailler par fonctionnalités verticales ; cinq membres contribuent à du code et à des revues.

## 9. Documentation détaillée

Le guide de travail J1 de 11 pages, créé dans la discussion ChatGPT, contient le déroulement pratique, les exemples de contrats, les rotations et les checklists. Il n'est pas automatiquement présent dans ce dépôt : pour l'ajouter, importer le PDF depuis ChatGPT puis le placer dans `docs/` via une PR.

**Décision ouverte :** confirmer avec l'équipe que le sujet final est bien celui-ci, notamment en cas de confusion avec le sujet de détection de bots web discuté auparavant.
