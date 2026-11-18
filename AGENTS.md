# AGENTS.md — Instructions Codex

Ce dépôt concerne **l'authentification continue comportementale sur poste de travail** (clavier et souris), **pas** la détection de bots sur un site web.

## Avant tout travail

1. Lire `docs/CODEX_HANDOFF_J1.md` et le README actuel.
2. Inspecter les fichiers et les branches existantes. Préserver le contenu utile.
3. Ne pas utiliser les documents de la branche `docs/behavioral-bot-detection-restructure` comme architecture de référence.
4. Expliquer les hypothèses à valider avant de changer les contrats.
5. Travailler sur une branche dédiée ; ne pas pousser ni fusionner directement sur `main`.

## Règles de développement

- Python, FastAPI, scikit-learn et Streamlit sont proposés dans le cadrage.
- Utiliser des schémas partagés et des unités explicites.
- Ne jamais enregistrer ni transmettre les caractères frappés, les mots de passe ou le contenu des formulaires.
- Les tests utilisent par défaut des données synthétiques.
- Écrire des tests adaptés à chaque composant modifié.
- Ne pas présenter les scores fictifs comme les résultats d'un modèle entraîné.
- Ne pas considérer `INSUFFICIENT_DATA` comme une suspicion automatique.
- Aucun verrouillage réel ni déploiement public sans validation expresse.
- Ne pas ajouter de secrets ou de fichiers de données sensibles dans Git.

## Collaboration

Équipe : Imrane, Hiba, Saad, Chahd et Yahya. Travail en parallèle, pair programming, petites PR revues, intégration régulière. Les membres doivent apprendre toutes les couches du projet, mais éviter les modifications concurrentes d'un même fichier de contrat.

## Format d'une réponse Codex

Expliquer en français clair :
1. Ce qui a été inspecté.
2. Ce qui a été changé et pourquoi.
3. Comment tester.
4. Ce qui reste à valider ou à faire.
