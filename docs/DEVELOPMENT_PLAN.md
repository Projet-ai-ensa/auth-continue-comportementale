# Plan de développement

## Principe

Le développement se fait en parallèle, mais les interfaces sont définies avant les implémentations. Le MVP local est prioritaire. Le Cloud est optionnel.

## Jalons proposés

| Jalon | Résultat attendu |
|---|---|
| J1 | Sujet, architecture, contrats et règles Git approuvés |
| J2-J3 | Site et collecteur, exploration dataset, baseline ML, API simulée, dashboard simulé |
| J4 | Premier flux frontend → API → dashboard |
| J5-J6 | Modèle réel, prétraitement et politique de risque intégrés |
| J7 | MVP local de bout en bout |
| J8 | Sessions humaines et bots contrôlés |
| J9 | Évaluation, correction et tests de robustesse |
| J10 | Rapport, slides et démonstration |

## Priorité d'intégration

1. Définir le contrat d'événements.
2. Définir le contrat API.
3. Créer des fixtures de test.
4. Connecter le collecteur à l'API.
5. Connecter le pipeline ML à l'API.
6. Connecter le dashboard à l'API.
7. Tester le flux complet.

## Définition de terminé

Chaque livrable doit inclure :
- code ;
- tests ;
- documentation ;
- instructions d'exécution vérifiées ;
- preuve de fonctionnement ;
- pull request revue.

## Risques de planning

- Retard de collecte des sessions humaines.
- Incompatibilité des features entre datasets et collecteur.
- Dépendances non fixées.
- Déploiement Cloud trop tôt.
- Temps insuffisant pour l'évaluation.

Si le planning est serré, supprimer d'abord les fonctionnalités optionnelles. Ne pas supprimer les tests et l'évaluation.
