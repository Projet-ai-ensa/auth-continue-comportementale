# src/agent/quality.py

"""
Module d'évaluation de la qualité des fenêtres comportementales.

Responsabilité :
Évaluer la quantité et la complétude des données collectées
pour chaque fenêtre temporelle.
"""

# Seuils minimaux de données (valeurs provisoires du projet)
MIN_HOLD_SAMPLES = 10
MIN_FLIGHT_SAMPLES = 10

# À vérifier avec la valeur déjà utilisée dans le notebook.
FLIGHT_ANALYSIS_THRESHOLD = 1.0


def evaluate_window_quality(data):
    """
    Évalue la qualité des données d'une fenêtre.

    Args:
        data (dict): Dictionnaire contenant :
            - hold_times
            - flight_times
            - expired_hold_count (facultatif)
            - incomplete_flight_count (facultatif)
            - incomplete_hold_count (facultatif)

    Returns:
        dict: Compteurs et statut de qualité.
    """

    hold_count = len(data["hold_times"])
    flight_count = len(data["flight_times"])

    expired_count = data.get("expired_hold_count", 0)
    incomplete_flights = data.get("incomplete_flight_count", 0)
    incomplete_holds = data.get("incomplete_hold_count", 0)

    long_pause_count = sum(
        value > FLIGHT_ANALYSIS_THRESHOLD
        for value in data["flight_times"]
    )

    negative_count = sum(
        value < 0
        for value in data["flight_times"]
    )

    # Détermination du statut
    if (
        expired_count > 0
        or incomplete_flights > 0
        or incomplete_holds > 0
    ):
        status = "incomplete"

    elif hold_count == 0 and flight_count == 0:
        status = "no_data"

    elif (
        hold_count < MIN_HOLD_SAMPLES
        or flight_count < MIN_FLIGHT_SAMPLES
    ):
        status = "insufficient_data"

    else:
        status = "collected"

    return {
        "hold_count": hold_count,
        "flight_count": flight_count,
        "expired_hold_count": expired_count,
        "incomplete_flight_count": incomplete_flights,
        "incomplete_hold_count": incomplete_holds,
        "long_pause_count": long_pause_count,
        "negative_count": negative_count,
        "status": status
    }