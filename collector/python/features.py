# agent/features.py
"""
Module d'extraction des features comportementales clavier.

Responsabilité : transformer des listes de timestamps en vecteurs de features
numériques.
NOTE : Le contrôle de qualité des fenêtres (suffisance des données) est
géré exclusivement par le module quality.py.

Conventions :
- Tous les timestamps sont en secondes (float), issus d'une horloge monotone.
- Les features agrégées sont retournées en millisecondes (contrat JSON v0).
- Une feature avec données insuffisantes retourne None (jamais 0).
"""

import math
from numbers import Real
from typing import List, Optional, Dict, Any


# ============================================================================
# FONCTIONS PURES DE CALCUL
# ============================================================================

def calculate_hold_time(press_timestamp: float, release_timestamp: float) -> float:
    """
    Calcule la durée d'appui (hold time) d'une touche.
    """
    if (
        isinstance(press_timestamp, bool)
        or isinstance(release_timestamp, bool)
        or not isinstance(press_timestamp, Real)
        or not isinstance(release_timestamp, Real)
    ):
        raise TypeError("Les timestamps doivent être numériques.")

    press_timestamp = float(press_timestamp)
    release_timestamp = float(release_timestamp)

    if not math.isfinite(press_timestamp) or not math.isfinite(release_timestamp):
        raise ValueError("Les timestamps doivent être des valeurs finies.")

    if release_timestamp < press_timestamp:
        raise ValueError("Le relâchement ne peut pas précéder l'appui.")

    return release_timestamp - press_timestamp


def calculate_flight_time(previous_release: float, next_press: float) -> float:
    """
    Calcule le temps de vol (flight time / inter-key time) entre deux frappes.

    NOTE : Cette valeur peut être NÉGATIVE si les touches se chevauchent
    (ex: appui sur la touche suivante avant le relâchement de la précédente).
    C'est une information comportementale valide.
    """
    if (
        isinstance(previous_release, bool)
        or isinstance(next_press, bool)
        or not isinstance(previous_release, Real)
        or not isinstance(next_press, Real)
    ):
        raise TypeError("Les timestamps doivent être numériques.")

    previous_release = float(previous_release)
    next_press = float(next_press)

    if not math.isfinite(previous_release) or not math.isfinite(next_press):
        raise ValueError("Les timestamps doivent être finis.")

    # Pas de vérification de chronologie : les valeurs négatives sont autorisées
    return next_press - previous_release


# ============================================================================
# FONCTIONS STATISTIQUES
# ============================================================================

def calculate_statistics(values: List[float]) -> Dict[str, Optional[float]]:
    """
    Calcule les statistiques descriptives d'une liste de valeurs.
    Utilise l'écart-type de population (diviseur n).
    """
    if not values:
        return {
            "mean": None,
            "median": None,
            "std": None,
            "min": None,
            "max": None,
            "count": 0,
        }

    # Validation stricte de chaque élément
    for value in values:
        if isinstance(value, bool) or not isinstance(value, Real):
            raise TypeError("Toutes les valeurs doivent être numériques.")
        if not math.isfinite(float(value)):
            raise ValueError("Les valeurs doivent être finies.")

    # Conversion garantie après validation
    values = [float(value) for value in values]
    n = len(values)  # n est nécessairement > 0 ici

    mean = sum(values) / n
    sorted_values = sorted(values)

    if n % 2 == 1:
        median = sorted_values[n // 2]
    else:
        median = (sorted_values[n // 2 - 1] + sorted_values[n // 2]) / 2

    min_val = min(values)
    max_val = max(values)

    # Écart-type de population (diviseur n)
    variance = sum((x - mean) ** 2 for x in values) / n
    std = math.sqrt(variance)

    return {
        "mean": mean,
        "median": median,
        "std": std,
        "min": min_val,
        "max": max_val,
        "count": n,
    }


# ============================================================================
# CONSTRUCTION DU VECTEUR DE FEATURES (Conforme au contrat JSON v0)
# ============================================================================

def build_window_features(
    hold_times: List[float],
    interkey_times: List[float],  # Correspond aux "flight_times" du notebook
    key_count: int,
) -> Dict[str, Any]:
    """
    Construit le vecteur de features clavier pour une fenêtre temporelle.
    Strictement conforme au contrat JSON v0 (Section 5 du guide J1).
    """
    # Validation de key_count
    if isinstance(key_count, bool) or not isinstance(key_count, int):
        raise TypeError("key_count doit être un entier.")

    if key_count < 0:
        raise ValueError("key_count doit être positif ou nul.")

    hold_stats = calculate_statistics(hold_times)
    interkey_stats = calculate_statistics(interkey_times)

    # Conversion secondes → millisecondes
    def _to_ms(value: Optional[float]) -> Optional[float]:
        return round(value * 1000, 3) if value is not None else None

    # Contrat JSON v0 exact (sans durée ni débit de frappe non validés)
    return {
        "key_count": key_count,
        "hold_mean_ms": _to_ms(hold_stats["mean"]),
        "interkey_mean_ms": _to_ms(interkey_stats["mean"]),
    }
