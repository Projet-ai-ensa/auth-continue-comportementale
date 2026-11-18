# Instructions pour les agents de développement

## Contexte du projet

Ce dépôt contient un projet universitaire de détection comportementale de bots web. Le système étudie des signaux du navigateur et des caractéristiques de requêtes HTTP pour distinguer les sessions humaines des sessions automatisées.

## Avant chaque tâche

1. Lire ce fichier.
2. Lire `README.md`.
3. Lire les documents concernés dans `docs/`.
4. Vérifier le code et les tests existants avant de modifier un fichier.
5. Identifier les contrats partagés qui peuvent être affectés.

## Règles obligatoires

- Utiliser des noms cohérents pour les champs et les états.
- Ne pas modifier un contrat partagé sans mettre à jour sa documentation et ses tests.
- Ne jamais enregistrer les caractères saisis, les mots de passe ou le contenu des formulaires.
- Ne pas collecter des données personnelles non nécessaires.
- Ne pas ajouter de secret, clé API ou jeton au dépôt.
- Ne pas faire confiance aux événements envoyés par le navigateur.
- Valider toutes les entrées côté serveur.
- Ne pas présenter un score de modèle comme une probabilité sans calibration.
- Ne pas bloquer automatiquement de vrais visiteurs dans le MVP.
- Ne pas inventer de résultats expérimentaux.
- Ne pas ajouter de dépendance sans expliquer son besoin.
- Ne pas supprimer de fichiers existants sans vérifier leur contenu et leur usage.
- Ne pas pousser directement sur `main`.

## Méthode de travail

1. Traiter une tâche limitée à la fois.
2. Créer une branche dédiée.
3. Écrire ou mettre à jour les tests.
4. Exécuter les tests disponibles.
5. Décrire les fichiers modifiés.
6. Décrire les tests exécutés et leurs résultats.
7. Signaler les limites et les décisions qui nécessitent une validation humaine.
8. Préparer une pull request.

## Style de documentation

Écrire en français technique clair, avec des phrases courtes. Définir chaque terme spécialisé lors de sa première utilisation. Distinguer les exigences obligatoires, les choix proposés et les options futures. Utiliser des exemples vérifiables.

## Définition de terminé

Une tâche est terminée seulement si :
- le code respecte le contrat partagé ;
- les tests pertinents passent ;
- la documentation est à jour ;
- aucun secret ou contenu sensible n'est ajouté ;
- la pull request explique le changement et les résultats des tests.
