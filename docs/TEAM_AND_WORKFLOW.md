# Équipe et méthode de travail

## 1. Répartition des responsabilités

| Membre | Rôle principal | Livrables |
|---|---|---|
| Imrane | Responsable technique, architecture et API | Contrats, API FastAPI, revue technique, intégration |
| Hiba | Frontend et collecteur JavaScript | Site de test, collecte, agrégation navigateur |
| Saad | Data engineering | Datasets, nettoyage, extraction et préparation |
| Chahd | Machine learning et évaluation | Entraînement, comparaison, métriques, rapport ML |
| Yahya | Dashboard, tests transversaux et Cloud | Streamlit, CI, intégration, déploiement de démonstration |

Cette répartition est une proposition fondée sur le périmètre du projet. Elle ne suppose pas un niveau de compétence particulier. L'équipe peut échanger des tâches après une courte revue des compétences et disponibilités.

## 2. Coordination de proximité

- Imrane et Hiba travaillent en coordination rapprochée sur le contrat entre le frontend, le collecteur et l'API.
- Saad et Chahd travaillent en coordination rapprochée sur le format des données, les features et le pipeline d'entraînement.
- Yahya est disponible pour aider les quatre membres, surtout sur l'intégration, les tests et l'infrastructure.

La proximité facilite les échanges. Elle ne remplace pas les responsabilités individuelles.

## 3. Contrats entre les blocs

### Hiba ↔ Imrane

- Définir les noms et unités des features.
- Définir l'identifiant de session.
- Définir le format JSON.
- Tester ensemble l'envoi du navigateur vers l'API.

### Saad ↔ Chahd

- Définir les sources et les labels.
- Définir les règles de nettoyage.
- Définir la séparation train/validation/test.
- Fournir exactement les mêmes features en entraînement et en inférence.

### Yahya ↔ tous

- Obtenir des données de test stables.
- Vérifier que les interfaces fonctionnent ensemble.
- Maintenir les tests d'intégration.
- Préparer l'environnement de démonstration.

## 4. Règles GitHub

- `main` contient uniquement le code intégré et revu.
- Une branche par tâche : `feature/nom-tache` ou `docs/nom-tache`.
- Pas de push direct sur `main`.
- Une pull request doit expliquer le besoin, les fichiers modifiés et les tests.
- Les contrats partagés doivent être revus par les deux responsables concernés.
- Ne pas ajouter de données brutes de participants au dépôt.

## 5. Rituels

Chaque jour : point de 10 minutes.
1. Ce qui est terminé.
2. Ce qui est prévu.
3. Le blocage actuel.
4. L'aide nécessaire.

Deux synchronisations techniques :
- Imrane + Hiba : interface navigateur/API.
- Saad + Chahd : interface données/modèle.

Yahya vérifie les dépendances transversales.

## 6. Définition de terminé

Une tâche est terminée quand :
- le code respecte le contrat ;
- les tests passent ;
- la documentation est à jour ;
- la pull request est revue ;
- le résultat peut être démontré.
