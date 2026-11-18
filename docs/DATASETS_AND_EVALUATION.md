# Datasets et protocole d'évaluation

## 1. Sources de données à étudier

### M4D Web Bot Detection Dataset

Lien : https://m4d.iti.gr/web-bot-detection-dataset/

Le dataset de l'étude sur les web bots contient des sessions humaines et automatisées, des journaux web et des données de comportement de souris. Il constitue la source externe principale proposée.

Avant utilisation :
- lire la documentation du dataset ;
- vérifier la licence et les obligations d'attribution ;
- vérifier le format des fichiers ;
- comprendre les labels et le protocole de collecte ;
- ne pas supposer que les bots de 2021 représentent tous les bots actuels.

### Web Robot Detection Dataset — Zenodo

Lien : https://zenodo.org/records/3477932

Dataset complémentaire de journaux de requêtes HTTP. Il peut aider à étudier les caractéristiques serveur. Il ne doit pas être fusionné directement avec le dataset M4D sans analyse des différences de schéma et de labels.

### Données collectées par l'équipe

Collecter des sessions de participants volontaires sur le site de test. Utiliser des identifiants pseudonymes. Collecter les sessions de bots dans le même environnement.

## 2. Catégories expérimentales

- Humain : navigation manuelle.
- Bot simple : client HTTP automatisé.
- Bot intermédiaire : navigateur automatisé.
- Bot avancé : navigateur automatisé avec variations contrôlées de timing et de mouvement.

Documenter précisément la configuration de chaque bot. Ne pas utiliser un seul script comme représentant de tous les bots.

## 3. Groupes de caractéristiques

### Navigateur

- vitesse et distance de souris ;
- accélération ;
- changements de direction ;
- durée des pauses ;
- fréquence des clics ;
- intervalles entre clics ;
- fréquence et amplitude de défilement ;
- timing clavier sans contenu, si approuvé.

### Serveur

- nombre de requêtes ;
- méthodes HTTP ;
- codes de réponse ;
- intervalles entre requêtes ;
- nombre de pages demandées ;
- séquences de navigation ;
- durée de session.

## 4. Modèles à comparer

1. Logistic Regression : baseline interprétable.
2. Random Forest : modèle d'arbres en ensemble.
3. HistGradientBoosting : modèle de gradient boosting.

Le choix final dépend des résultats de validation. Ne pas choisir un modèle uniquement parce qu'il est plus complexe.

## 5. Protocole

- Définir les labels avant l'entraînement.
- Nettoyer les données sans utiliser le jeu de test.
- Séparer les données par participant et par session.
- Garder au moins une configuration de bot pour un test de généralisation si les données le permettent.
- Utiliser la validation pour sélectionner le modèle et les seuils.
- Utiliser le test final une seule fois pour rapporter les résultats.
- Documenter les différences entre les datasets.

Une séparation aléatoire de lignes peut placer des événements d'une même session dans plusieurs ensembles et produire une estimation trop optimiste.

## 6. Métriques

- Accuracy.
- Precision.
- Recall.
- F1-score.
- False Positive Rate (FPR).
- False Negative Rate (FNR).
- ROC-AUC.
- PR-AUC.
- Délai de détection.
- Latence API.

Pour le projet, un faux positif signifie qu'une session humaine est classée comme automatisée. Un faux négatif signifie qu'une session automatisée est classée comme humaine.

## 7. Expériences

| ID | Expérience | Question |
|---|---|---|
| E1 | Caractéristiques serveur seules | Que détectent les logs ? |
| E2 | Souris et clics seuls | Que détecte le comportement navigateur ? |
| E3 | Signaux combinés | La fusion améliore-t-elle les résultats ? |
| E4 | Bots simples vs avancés | Quel est l'effet de la sophistication ? |
| E5 | Participants non vus | Le modèle généralise-t-il ? |
| E6 | Configuration de bot non vue | Le modèle apprend-il des comportements généraux ? |
| E7 | Sans timing clavier / avec timing clavier | Le clavier apporte-t-il un gain ? |

E7 est optionnelle et nécessite une collecte respectueuse de la vie privée.

## 8. Limites à rapporter

- Taille et diversité limitées des participants.
- Âge des datasets publics.
- Différences de navigateur et d'appareil.
- Événements client modifiables ou absents.
- Bots légitimes et automatisation d'accessibilité.
- Écart entre un environnement de test et le trafic réel.

Ne jamais inventer de résultats ou de seuils de performance.
