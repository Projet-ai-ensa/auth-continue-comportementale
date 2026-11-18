# Fonctionnalités prévues — Bot Detection

Ce fichier décrit les fonctionnalités cibles du MVP. Une fonctionnalité n'est pas considérée comme terminée tant qu'elle n'a pas de test ou de preuve de démonstration.

## Collecte navigateur

- [ ] Collecter des mouvements de souris avec horodatage.
- [ ] Calculer la distance, la vitesse et les changements de direction.
- [ ] Collecter les clics et les intervalles entre clics.
- [ ] Collecter les événements de défilement.
- [ ] Étudier les intervalles de frappe sans enregistrer les caractères.
- [ ] Agréger les événements par fenêtre de session.
- [ ] Gérer les fenêtres avec peu ou pas d'activité.

## Données serveur

- [ ] Associer les requêtes à une session pseudonyme.
- [ ] Calculer le nombre et le type de requêtes.
- [ ] Calculer les intervalles entre requêtes.
- [ ] Calculer les séquences de pages et la durée de session.
- [ ] Valider les données reçues et rejeter les formats incorrects.

## Machine learning

- [ ] Préparer les jeux de données.
- [ ] Comparer Logistic Regression.
- [ ] Comparer Random Forest.
- [ ] Comparer HistGradientBoosting.
- [ ] Évaluer les résultats par participant et par configuration de bot.
- [ ] Mesurer F1, précision, rappel, FPR, FNR et latence.
- [ ] Exporter le pipeline final avec sa version.

## API et tableau de bord

- [ ] Exposer une route de prédiction documentée.
- [ ] Enregistrer les résultats nécessaires à l'expérience.
- [ ] Afficher les sessions et les prédictions.
- [ ] Afficher les métriques du modèle.
- [ ] Présenter les états « autoriser », « vérifier » et « restreindre » à titre de démonstration.

## Sécurité et confidentialité

- [ ] Ne jamais stocker le texte saisi.
- [ ] Ne jamais stocker les mots de passe.
- [ ] Utiliser des identifiants pseudonymes.
- [ ] Définir une durée de conservation.
- [ ] Protéger les secrets par variables d'environnement.
- [ ] Documenter les limites du collecteur côté navigateur.

## Déploiement

- [ ] Faire fonctionner le MVP en local.
- [ ] Ajouter Docker après validation locale.
- [ ] Déployer une démonstration Cloud seulement après revue de sécurité et de coût.
