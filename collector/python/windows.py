"""
Module de gestion des fenêtres temporelles de capture clavier + souris.

Responsabilités :
- Organiser les mesures clavier et souris par fenêtres temporelles.
- Suivre les appuis, Flight Times et clics souris en attente.
- Vérifier les conditions de finalisation.
- Construire les payloads JSON multimodaux (clavier + souris).

L'état d'une session est centralisé dans WindowManager.
"""

import json
import math
from typing import Any, Dict, List, Optional

from .features import build_window_features
from .quality import evaluate_window_quality
from .mouse import (
    pair_mouse_clicks,
    add_click_features_to_windows,
    build_mouse_window_features,
    calculate_mouse_window_quality,
)


# ==============================================================================
# QUALITÉ GLOBALE (niveau module)
# ==============================================================================

def evaluate_global_quality(
    keyboard_status: str,
    mouse_status: str,
) -> str:
    """
    Évalue la qualité globale combinant clavier et souris.

    Règles :
    - "collected"         → les deux modalités sont "collected".
    - "no_data"           → les deux modalités sont "no_data".
    - "insufficient_data" → au moins une modalité manque de données.
    """
    if keyboard_status == "collected" and mouse_status == "collected":
        return "collected"
    if keyboard_status == "no_data" and mouse_status == "no_data":
        return "no_data"
    return "insufficient_data"


# ==============================================================================
# CLASSE WindowManager
# ==============================================================================

class WindowManager:
    """Gère les fenêtres temporelles d'une session de capture multimodale."""

    def __init__(
        self,
        session_start: float,
        user_id: str,
        session_id: str,
        window_duration: float = 30.0,
    ):
        if not isinstance(session_start, (int, float)) or isinstance(session_start, bool):
            raise ValueError("session_start doit être numérique.")
        if not math.isfinite(session_start):
            raise ValueError("session_start doit être fini.")

        if not isinstance(window_duration, (int, float)) or isinstance(window_duration, bool):
            raise ValueError("window_duration doit être numérique.")
        if not math.isfinite(window_duration) or window_duration <= 0:
            raise ValueError("window_duration doit être strictement positif.")

        if not user_id or not session_id:
            raise ValueError("user_id et session_id sont obligatoires.")

        self.session_start = float(session_start)
        self.window_duration = float(window_duration)
        self.user_id = user_id
        self.session_id = session_id

        # Données organisées par fenêtre
        self.window_buffers: Dict[int, Dict[str, Any]] = {}

        # Appuis clavier actuellement maintenus
        self.active_presses: Dict[Any, Dict[str, Any]] = {}

        # Historique chronologique des appuis clavier
        self.press_sequence: List[Dict[str, Any]] = []

        # Suivi des fenêtres
        self.finalized_windows: set = set()
        self.next_window_to_finalize: int = 0

        # Payloads produits pendant la session
        self.captured_payloads: List[Dict[str, Any]] = []

    # ==========================================================================
    # GESTION DES FENÊTRES
    # ==========================================================================

    def get_real_window_id(self, timestamp: float) -> int:
        """Détermine l'identifiant de fenêtre associé à un timestamp."""
        elapsed = timestamp - self.session_start
        if elapsed < 0:
            raise ValueError("Timestamp antérieur au début de session.")
        return math.floor(elapsed / self.window_duration)

    def get_window_buffer(self, window_id: int) -> Dict[str, Any]:
        """Crée ou récupère le buffer d'une fenêtre."""
        if window_id not in self.window_buffers:
            self.window_buffers[window_id] = {
                # Données clavier
                "hold_times": [],
                "flight_times": [],
                "expired_hold_count": 0,
                "incomplete_hold_count": 0,
                # Événements souris
                "mouse_events": [],
                # Résultats d'appariement des clics (remplis plus tard)
                "mouse_clicks": [],
                "mouse_incomplete_presses": [],
                "mouse_unmatched_releases": [],
            }
        return self.window_buffers[window_id]

    # ==========================================================================
    # AJOUT D'ÉVÉNEMENTS
    # ==========================================================================

    def add_mouse_event(self, event: Dict[str, Any]) -> None:
        """Ajoute un événement souris dans le buffer de sa fenêtre."""
        if not isinstance(event, dict):
            raise ValueError("L'événement souris doit être un dictionnaire.")
        if "timestamp" not in event:
            raise ValueError("Timestamp absent de l'événement souris.")

        timestamp = event["timestamp"]
        if (
            not isinstance(timestamp, (int, float))
            or isinstance(timestamp, bool)
            or not math.isfinite(timestamp)
        ):
            raise ValueError("Timestamp souris invalide.")

        window_id = self.get_real_window_id(timestamp)
        buffer = self.get_window_buffer(window_id)
        buffer["mouse_events"].append(event)

    # ==========================================================================
    # CONSTRUCTION DES DONNÉES SOURIS
    # ==========================================================================

    def build_mouse_windows(self) -> List[Dict[str, Any]]:
        """Construit les fenêtres au format attendu par les fonctions souris."""
        windows = []
        for window_id in sorted(self.window_buffers):
            start = self.session_start + window_id * self.window_duration
            end = start + self.window_duration
            buffer = self.window_buffers[window_id]
            windows.append({
                "window_id": f"w{window_id:04d}",
                "start": start,
                "end": end,
                "events": sorted(
                    buffer["mouse_events"],
                    key=lambda event: event["timestamp"],
                ),
            })
        return windows

    def build_mouse_click_data(self) -> Dict[str, Any]:
        """
        Apparier globalement les clics de la session,
        puis les répartit dans les fenêtres temporelles.
        """
        windows = self.build_mouse_windows()

        # Rassembler tous les événements souris
        all_mouse_events = []
        for window in windows:
            all_mouse_events.extend(window["events"])
        all_mouse_events.sort(key=lambda event: event["timestamp"])

        # Appariement global
        completed_clicks, incomplete_presses, unmatched_releases = (
            pair_mouse_clicks(all_mouse_events)
        )

        # Répartition par fenêtre
        clicks_by_window, intervals_by_window = (
            add_click_features_to_windows(
                windows=windows,
                completed_clicks=completed_clicks,
            )
        )

        return {
            "completed_clicks": completed_clicks,
            "incomplete_presses": incomplete_presses,
            "unmatched_releases": unmatched_releases,
            "clicks_by_window": clicks_by_window,
            "intervals_by_window": intervals_by_window,
        }

    def build_mouse_window_data(self) -> Dict[str, Dict[str, Any]]:
        """Construit les features et la qualité souris pour chaque fenêtre."""
        windows = self.build_mouse_windows()
        click_data = self.build_mouse_click_data()

        mouse_features = build_mouse_window_features(
            windows=windows,
            clicks_by_window=click_data["clicks_by_window"],
            intervals_by_window=click_data["intervals_by_window"],
        )

        mouse_window_data = {}
        for window in windows:
            window_id = window["window_id"]
            features = mouse_features[window_id]
            quality = calculate_mouse_window_quality(
                window=window,
                features=features,
                incomplete_session_presses=click_data["incomplete_presses"],
                unmatched_session_releases=click_data["unmatched_releases"],
            )
            mouse_window_data[window_id] = {
                "features": features,
                "quality": quality,
            }

        return mouse_window_data

    # ==========================================================================
    # SUIVI DES ÉLÉMENTS EN ATTENTE
    # ==========================================================================

    def count_pending_presses(self, window_id: int) -> int:
        """Compte les appuis clavier non encore relâchés dans une fenêtre."""
        return sum(
            1
            for record in self.active_presses.values()
            if record.get("window_id") == window_id
        )

    def count_pending_flights(self, window_id: int) -> int:
        """Compte les Flight Times clavier qui ne peuvent pas encore être calculés."""
        pending = 0
        for index in range(1, len(self.press_sequence)):
            previous_record = self.press_sequence[index - 1]
            next_record = self.press_sequence[index]

            if next_record.get("window_id") != window_id:
                continue

            if (
                previous_record.get("release_timestamp") is None
                and not previous_record.get("expired", False)
                and not previous_record.get("incomplete", False)
                and not previous_record.get("flight_calculated", False)
            ):
                pending += 1
        return pending

    def count_pending_mouse_clicks(self, window_id: int) -> int:
        """
        Compte les clics souris commencés dans une fenêtre
        dont le relâchement n'a pas encore été reçu.
        """
        pending_presses: Dict[str, List[Dict[str, Any]]] = {}
        ordered_events = []

        # Récupération de tous les événements souris
        for buffer in self.window_buffers.values():
            ordered_events.extend(buffer.get("mouse_events", []))

        # Tri chronologique global
        ordered_events.sort(key=lambda event: event["timestamp"])

        # Appariement FIFO par bouton
        for event in ordered_events:
            event_type = event.get("type")
            button = event.get("button")

            if event_type == "CLICK_PRESS":
                pending_presses.setdefault(button, [])
                pending_presses[button].append(event)
            elif event_type == "CLICK_RELEASE":
                if pending_presses.get(button):
                    pending_presses[button].pop(0)

        # Compter uniquement les appuis de la fenêtre demandée
        count = 0
        for button_events in pending_presses.values():
            for press_event in button_events:
                press_window_id = self.get_real_window_id(press_event["timestamp"])
                if press_window_id == window_id:
                    count += 1
        return count

    def can_finalize_window(self, window_id: int) -> bool:
        """
        Vérifie qu'aucun appui clavier, Flight Time
        ou clic souris n'est encore en attente.
        """
        return (
            self.count_pending_presses(window_id) == 0
            and self.count_pending_flights(window_id) == 0
            and self.count_pending_mouse_clicks(window_id) == 0
        )

    # ==========================================================================
    # GÉNÉRATION DU PAYLOAD JSON
    # ==========================================================================

    def generate_window_json(
        self,
        window_id: int,
        duration_seconds: Optional[float] = None,
        completion: str = "complete",
    ) -> str:
        """Construit le payload JSON clavier + souris d'une fenêtre."""
        data = self.get_window_buffer(window_id)

        # -------------------------------------------------------------
        # 1. FEATURES CLAVIER
        # -------------------------------------------------------------
        hold_values = data["hold_times"]
        flight_values = data["flight_times"]
        key_count = len(hold_values)

        keyboard_features = build_window_features(
            hold_times=hold_values,
            interkey_times=flight_values,
            key_count=key_count,
        )

        # Détection des Flight Times incomplets
        incomplete_flights = 0
        for index in range(1, len(self.press_sequence)):
            previous_record = self.press_sequence[index - 1]
            next_record = self.press_sequence[index]
            if (
                next_record.get("window_id") == window_id
                and (
                    previous_record.get("expired", False)
                    or previous_record.get("incomplete", False)
                )
                and not previous_record.get("flight_calculated", False)
            ):
                incomplete_flights += 1

        keyboard_quality_data = {
            "hold_times": hold_values,
            "flight_times": flight_values,
            "expired_hold_count": data.get("expired_hold_count", 0),
            "incomplete_hold_count": data.get("incomplete_hold_count", 0),
            "incomplete_flight_count": incomplete_flights,
            "key_count": key_count,
        }
        keyboard_quality = evaluate_window_quality(keyboard_quality_data)

        # -------------------------------------------------------------
        # 2. FEATURES ET QUALITÉ SOURIS
        # -------------------------------------------------------------
        mouse_window_data = self.build_mouse_window_data()
        window_key = f"w{window_id:04d}"
        mouse_data = mouse_window_data.get(window_key)

        if mouse_data is None:
            raise RuntimeError(f"Données souris introuvables pour {window_key}.")

        mouse_features = mouse_data["features"]
        mouse_quality = mouse_data["quality"]

        # -------------------------------------------------------------
        # 3. QUALITÉ GLOBALE CLAVIER + SOURIS
        # -------------------------------------------------------------
        global_quality = evaluate_global_quality(
            keyboard_status=keyboard_quality["status"],
            mouse_status=mouse_quality["global"],
        )

        # -------------------------------------------------------------
        # 4. DURÉE DE LA FENÊTRE
        # -------------------------------------------------------------
        if duration_seconds is None:
            duration_seconds = self.window_duration

        # -------------------------------------------------------------
        # 5. PAYLOAD FINAL
        # -------------------------------------------------------------
        payload = {
            "schema_version": "0.1",
            "user_id": self.user_id,
            "session_id": self.session_id,
            "window_id": window_key,
            "duration_seconds": round(duration_seconds, 4),
            "completion": completion,
            "features": {
                "keyboard": keyboard_features,
                "mouse": mouse_features,
            },
            "quality": {
                "keyboard": keyboard_quality,
                "mouse": mouse_quality,
                "global": global_quality,
            },
        }

        return json.dumps(
            payload,
            indent=2,
            ensure_ascii=False,
            allow_nan=False,
        )

    # ==========================================================================
    # FINALISATION DES FENÊTRES
    # ==========================================================================

    def finalize_window(self, window_id: int) -> Optional[str]:
        """Finalise une fenêtre complète si elle est prête."""
        if window_id in self.finalized_windows:
            return None
        if not self.can_finalize_window(window_id):
            return None

        json_data = self.generate_window_json(window_id)
        self.finalized_windows.add(window_id)
        return json_data

    def finalize_completed_windows(
        self, current_timestamp: float
    ) -> List[Dict[str, Any]]:
        """Finalise les fenêtres complètes dans l'ordre chronologique."""
        # ✅ CORRECTION : validation de current_timestamp
        if (
            not isinstance(current_timestamp, (int, float))
            or isinstance(current_timestamp, bool)
            or not math.isfinite(current_timestamp)
        ):
            raise ValueError("current_timestamp doit être un nombre fini.")

        elapsed = current_timestamp - self.session_start
        if elapsed < 0:
            raise ValueError("Timestamp antérieur au début de session.")
        if elapsed < self.window_duration:
            return []

        last_closed_window = math.floor(elapsed / self.window_duration) - 1
        results = []

        while self.next_window_to_finalize <= last_closed_window:
            window_id = self.next_window_to_finalize
            self.get_window_buffer(window_id)

            json_data = self.finalize_window(window_id)
            if json_data is None:
                break  # Fenêtre bloquée → on arrête pour préserver l'ordre

            result = {"window_id": window_id, "json": json_data}
            results.append(result)
            self.captured_payloads.append(result)
            self.next_window_to_finalize += 1

        return results

    def get_partial_window_metadata(self, stop_timestamp: float) -> Dict[str, Any]:
        """Calcule les informations de la dernière fenêtre partielle."""
        # ✅ CORRECTION : validation de stop_timestamp
        if (
            not isinstance(stop_timestamp, (int, float))
            or isinstance(stop_timestamp, bool)
            or not math.isfinite(stop_timestamp)
        ):
            raise ValueError("stop_timestamp doit être un nombre fini.")

        elapsed = stop_timestamp - self.session_start
        if elapsed <= 0:
            raise ValueError("Durée de session insuffisante.")

        window_id = math.floor(elapsed / self.window_duration)
        window_start = self.session_start + window_id * self.window_duration
        duration = stop_timestamp - window_start

        if duration <= 0:
            raise ValueError("Aucune fenêtre partielle à finaliser.")
        if duration >= self.window_duration:
            raise ValueError("Cette fenêtre n'est pas partielle.")

        return {
            "window_id": window_id,
            "duration_seconds": duration,
            "completion": "partial",
        }

    def finalize_partial_window(
        self, stop_timestamp: float
    ) -> Optional[Dict[str, Any]]:
        """Finalise la dernière fenêtre partielle, même si elle est vide."""
        try:
            metadata = self.get_partial_window_metadata(stop_timestamp)
        except ValueError:
            return None

        window_id = metadata["window_id"]

        # ✅ CORRECTION CRITIQUE : préservation stricte de l'ordre chronologique
        if self.next_window_to_finalize != window_id:
            return None

        if window_id in self.finalized_windows:
            return None

        self.get_window_buffer(window_id)

        if not self.can_finalize_window(window_id):
            return None

        payload = self.generate_window_json(
            window_id=window_id,
            duration_seconds=metadata["duration_seconds"],
            completion="partial",
        )

        result = {"window_id": window_id, "json": payload}
        self.captured_payloads.append(result)
        self.finalized_windows.add(window_id)
        self.next_window_to_finalize += 1  # ✅ Incrémentation explicite

        return result
