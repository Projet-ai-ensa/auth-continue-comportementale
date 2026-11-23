# Proposition de contrat — observations clavier agrégées (à valider)

> **Statut : proposition de discussion, pas contrat approuvé.**  
> Responsables à consulter : Hiba (collecte), Imrane (API), Saad (données), Chahd (modèle), Yahya (intégration).  
> Cette proposition **ne modifie pas** `/v1/observations` ni le schéma navigateur `1.0`.

## 1. Objectif

Transmettre uniquement des statistiques temporelles **agrégées** de frappe depuis un collecteur contrôlé vers une API de démonstration locale. Aucune touche, aucun caractère, aucun texte saisi, mot de passe, nom de champ ou contenu de formulaire n'est collecté ni envoyé.

La collecte nécessite l'accord des participants et doit être désactivée dans les champs sensibles (notamment `input[type=password]`). Il faut éviter aussi les champs libres susceptibles de contenir des données sensibles; privilégier une zone de test dédiée, avec consentement explicite.

## 2. Écarts constatés entre l'exemple de Hiba et notre API

| Exemple du collecteur clavier communiqué | Contrat navigateur actuel |
|---|---|
| `window_id: 1` (entier) | `window_id` : chaîne non vide |
| `duration_seconds: 30.0` | `window_duration_ms: 30000` |
| `features.hold_mean`, `features.flight_mean` | `browser_features` avec 8 métriques souris/clic/défilement |
| `quality.status: "no_data"` et `features: {}` pour une fenêtre vide | Champs navigateur requis, valeurs `null` seulement pour quelques mesures |
| Intervalles potentiellement signés (`flight_min < 0`) | Mesures navigateur non négatives |

**Important :** Le `flight_min` négatif n'est pas systématiquement une erreur : il peut représenter le chevauchement de frappes, selon la définition de la latence utilisée. Cette convention doit être vérifiée avec Hiba.

## 3. Proposition de transport

Créer ultérieurement, **après accord**, une route indépendante `POST /v1/keyboard-observations`. Ne pas introduire ces champs dans le contrat navigateur actuel sans revue de version.

Une observation devrait transmettre :
- `schema_version` (version propre au contrat clavier, à fixer) ;
- `session_id` et `window_id` pseudonymes, typés comme chaînes ;
- `window_started_at` avec fuseau horaire explicite ;
- `window_duration_ms` entier strictement positif ;
- `collector_version` ;
- `keyboard_features` : statistiques agrégées uniquement ;
- `quality` : comptages et statut de collecte.

Les intervalles temporels doivent être exprimés **en millisecondes dans l'API**, avec conversion explicite depuis les secondes éventuelles du collecteur. Le nom `hold` correspond à la durée d'appui; `flight` désigne un intervalle entre deux événements de frappe **dont la définition précise doit être fournie par Hiba**.

### Exemple purement illustratif — à ne pas traiter comme le format final

```json
{
  "schema_version": "keyboard-proposal-1",
  "session_id": "session-demo-001",
  "window_id": "1",
  "window_started_at": "2026-11-23T12:00:00Z",
  "window_duration_ms": 30000,
  "collector_version": "0.1.0",
  "keyboard_features": {
    "hold_count": 11,
    "hold_mean_ms": 171.57,
    "flight_count": 10,
    "flight_mean_ms": 520.45,
    "flight_min_ms": -26.42
  },
  "quality": {
    "hold_count": 11,
    "flight_count": 10,
    "expired_hold_count": 0,
    "incomplete_flight_count": 0,
    "status": "collected"
  }
}
```

Ces valeurs sont fictives / illustratives et ne constituent **aucune performance expérimentale**.

## 4. Points de validation à résoudre avant le code

1. **Origine du collecteur :** notebook Python de démonstration ou JavaScript intégré à une page web ? Le projet cible un collecteur navigateur JavaScript, mais les exemples transmis ne prouvent pas son implémentation.
2. **Définition exacte des intervalles :** hold et flight (événements de référence, chevauchement, signe, origine du temps).
3. **Liste complète des métriques :** `count`, `mean`, `median`, `min`, `max`, `std` pour hold/flight ? Que faire si le nombre d'échantillons est insuffisant ?
4. **Fenêtre sans activité :** `keyboard_features: {}` ou valeurs explicites `null` ? La proposition privilégie un schéma explicite avec `null` si approuvé, pour faciliter validation et ML.
5. **Qualité :** valeurs permises pour `quality.status`, cohérence entre `quality.*_count` et `keyboard_features.*_count`, et statut en cas de données partielles.
6. **IDs :** supprimer le `user_id` non nécessaire ou le remplacer par un identifiant pseudonyme sans identifiant personnel stable.
7. **Prédiction :** préciser si la version initiale valide et accuse réception, sans prédire, tant que Chahd n'a pas un modèle entraîné avec les caractéristiques clavier.
8. **Sécurité :** taille limite, limitation de fréquence, rétention, vérification des sessions et politique CORS pour un futur frontend distant.

## 5. Critères d'acceptation d'une future implémentation

- Une requête conforme est acceptée et une réponse documentée est renvoyée.
- Une durée négative, un compteur négatif, une valeur numérique non finie ou un champ inattendu sont rejetés par HTTP 422.
- Une valeur `flight_min_ms` négative peut être acceptée **si la convention signée est approuvée**.
- Une fenêtre vide possède une représentation non ambiguë et ne déclenche pas de prédiction trompeuse.
- Le schéma navigateur `/v1/observations` reste inchangé; tous ses tests de régression restent au vert.
- Aucune donnée de touche ni texte saisi n'entre dans le dépôt ou les journaux.

## 6. Étapes suivantes

1. Hiba publie son code/son notebook et **un exemple de JSON anonymisé** dans une branche GitHub dédiée (jamais de frappe réelle ou sensible).
2. L'équipe valide les questions de la section 4.
3. Imrane implémente le schéma Pydantic, la route indépendante et les tests.
4. Saad/Chahd définissent comment utiliser les données clavier, sans supposer que le modèle actuel à 8 features sait les analyser.
5. Yahya effectue la démonstration locale de bout en bout.

Voir également `docs/API_CONTRACT.md`, `AGENTS.md` et `FEATURES.md`.
