# Cadrage du projet

## Sujet

Détection comportementale des bots sur un site web par apprentissage automatique.

## Problème

Les applications web reçoivent des sessions humaines et des sessions automatisées. Les bots peuvent être légitimes ou abusifs. Le projet étudie si les signaux comportementaux et les caractéristiques de requêtes peuvent aider à distinguer ces sessions.

## Objectif mesurable

Construire un prototype qui classe des sessions de test comme humaines ou automatisées et mesurer sa performance sur des participants et des configurations de bots qui ne sont pas présents dans l'entraînement.

## Périmètre MVP

- Site de test contrôlé.
- Collecte JavaScript de souris, clics et défilement.
- Timing clavier uniquement si le besoin est confirmé et sans collecte du texte.
- Caractéristiques de requêtes calculées côté serveur.
- Modèles de classification tabulaire.
- API de prédiction.
- Dashboard de résultats.
- Évaluation hors ligne et démonstration locale.

## Hors périmètre

- Détection certaine de l'intention malveillante.
- Blocage de visiteurs réels.
- Protection anti-bot commerciale.
- Fingerprinting invasif.
- Déploiement de production.

## Catégories expérimentales

1. Humain : navigation manuelle consentie.
2. Bot simple : client HTTP automatisé.
3. Bot intermédiaire : navigateur automatisé.
4. Bot avancé : navigateur automatisé avec variations de timing et de mouvement.

La catégorie « bot avancé » doit être définie par le protocole de l'équipe. Elle ne signifie pas que tous les bots modernes sont couverts.

## Hypothèses à tester

- H1 : les caractéristiques combinées du navigateur et du serveur améliorent la détection par rapport à chaque source seule.
- H2 : les bots avancés sont plus difficiles à détecter que les bots simples.
- H3 : la performance diminue sur une configuration de bot non vue pendant l'entraînement.
- H4 : le timing clavier apporte une amélioration mesurable par rapport aux autres signaux.

## Critère de réussite

Le projet doit fournir une expérience reproductible, des résultats mesurés, une analyse des erreurs et une démonstration de bout en bout. Aucun seuil de performance ne doit être annoncé avant les expériences.
