# Sécurité et confidentialité

## 1. Principes

Le projet est un prototype universitaire. Il ne doit pas être présenté comme un système anti-bot de production.

Le système analyse des caractéristiques de navigation. Il ne doit pas collecter le contenu des communications de l'utilisateur.

## 2. Données interdites

Ne jamais collecter ou stocker :
- mots de passe ;
- texte saisi dans les champs ;
- contenu des formulaires ;
- données de paiement ;
- cookies de session ;
- jetons d'authentification ;
- données personnelles non nécessaires.

Pour le clavier, ne conserver que des intervalles temporels agrégés si cette fonctionnalité est approuvée. Ne pas enregistrer les valeurs des touches.

## 3. Données autorisées sous contrôle

- coordonnées et horodatages de souris, de préférence agrégés ;
- nombre et intervalle de clics ;
- mesures de défilement ;
- mesures temporelles de clavier sans caractères ;
- caractéristiques agrégées de requêtes HTTP ;
- identifiant de session pseudonyme ;
- classe et version du modèle.

## 4. Menaces

| Menace | Mesure |
|---|---|
| Événements falsifiés côté client | Validation serveur et comparaison avec les logs |
| Rejeu de données | Identifiants de fenêtre, horodatages et détection de doublons |
| Injection de données | Schémas Pydantic et limites de taille |
| Accès non autorisé à l'API | Authentification pour les routes internes |
| Fuite de secrets | Variables d'environnement et fichiers ignorés par Git |
| Fuite de données de participants | Minimisation, accès limité et rétention définie |
| Faux positifs | Vérification supplémentaire au lieu d'un blocage automatique |

## 5. Règles de collecte

- Informer les participants.
- Obtenir leur consentement avant la collecte.
- Utiliser des identifiants pseudonymes.
- Collecter uniquement les champs nécessaires.
- Définir une durée de conservation.
- Supprimer les données à la fin de l'expérience selon le protocole.
- Ne pas publier les données brutes.

## 6. Cloud

- Utiliser HTTPS.
- Ne jamais placer les secrets dans le frontend.
- Garder les secrets dans les variables d'environnement du fournisseur.
- Limiter les droits de la base de données.
- Ne pas envoyer de données de participants réels vers un service Cloud avant validation.
- Vérifier les coûts et les règles de conservation.

## 7. Cadre légal

Avant toute collecte réelle ou tout déploiement public, examiner la loi marocaine 09-08 et les recommandations de la CNDP. Cette documentation est une consigne de prudence et ne constitue pas un avis juridique.
