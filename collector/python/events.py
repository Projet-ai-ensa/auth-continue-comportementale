# src/agent/events.py
"""
Module de capture et de traitement des événements clavier.

Responsabilités :
- Recevoir les événements clavier via pynput.
- Placer les événements dans une file d'attente.
- Traiter les appuis et les relâchements.
- Calculer les Hold Times et les Flight Times.
- Ignorer les répétitions et les relâchements orphelins.
- Expirer les appuis maintenus trop longtemps.

Les données de session sont centralisées dans WindowManager.
"""

from queue import Queue, Empty
from typing import Any, Optional

from pynput import keyboard

from .features import calculate_hold_time, calculate_flight_time


class EventProcessor:
    """Gère la capture et le traitement des événements clavier."""

    def __init__(
        self,
        window_manager,
        max_hold_seconds: float = 5.0,
        event_queue: Optional[Queue] = None,
    ):
        if isinstance(max_hold_seconds, bool) or not isinstance(
            max_hold_seconds, (int, float)
        ):
            raise ValueError("max_hold_seconds doit être numérique.")

        if max_hold_seconds <= 0:
            raise ValueError("max_hold_seconds doit être positif.")

        self.window_manager = window_manager
        self.max_hold_seconds = float(max_hold_seconds)

        self.event_queue = event_queue if event_queue is not None else Queue()

        self.stop_requested = False
        self.ignored_releases = 0

    # ------------------------------------------------------------------
    # CALLBACKS PYNPUT
    # ------------------------------------------------------------------

    def on_press(self, key):
        """Callback appelé lorsqu'une touche est pressée."""

        timestamp = __import__("time").perf_counter()

        if key == keyboard.Key.esc:
            self.event_queue.put(("STOP", None, timestamp))
            return False

        self.event_queue.put(("PRESS", key, timestamp))

    def on_release(self, key):
        """Callback appelé lorsqu'une touche est relâchée."""

        if key == keyboard.Key.esc:
            return False

        timestamp = __import__("time").perf_counter()

        self.event_queue.put(("RELEASE", key, timestamp))

    # ------------------------------------------------------------------
    # TRAITEMENT DES APPELS
    # ------------------------------------------------------------------

    def process_press_event(self, key: Any, timestamp: float) -> str:
        """Enregistre un nouvel appui et tente le calcul du Flight Time."""

        manager = self.window_manager

        if key in manager.active_presses:
            return "REPETITION"

        window_id = manager.get_real_window_id(timestamp)

        record = {
            "press_timestamp": timestamp,
            "release_timestamp": None,
            "window_id": window_id,
            "flight_calculated": False,
        }

        manager.press_sequence.append(record)
        manager.active_presses[key] = record

        # Tenter de calculer le Flight Time avec l'appui précédent.
        if len(manager.press_sequence) >= 2:
            previous_record = manager.press_sequence[-2]
            self.add_flight_time(previous_record, record)

        return "NOUVEL APPUI"

    def process_release_event(self, key: Any, timestamp: float):
        """Enregistre un relâchement et calcule le Hold Time."""

        manager = self.window_manager

        if key not in manager.active_presses:
            self.ignored_releases += 1
            return None

        record = manager.active_presses[key]

        hold = calculate_hold_time(
            record["press_timestamp"],
            timestamp,
        )

        # Retirer l'appui actif uniquement après validation du calcul.
        manager.active_presses.pop(key)

        record["release_timestamp"] = timestamp

        # Le Hold Time appartient à la fenêtre du début de l'appui.
        window_id = record["window_id"]

        manager.get_window_buffer(window_id)["hold_times"].append(hold)

        # Rechercher le prochain appui dans la séquence.
        index = next(
            i for i, item in enumerate(manager.press_sequence)
            if item is record
        )

        if index + 1 < len(manager.press_sequence):
            next_record = manager.press_sequence[index + 1]
            self.add_flight_time(record, next_record)

        return hold

    # ------------------------------------------------------------------
    # CALCUL DU FLIGHT TIME
    # ------------------------------------------------------------------

    def add_flight_time(self, previous_record, next_record):
        """
        Calcule le Flight Time entre deux appuis consécutifs.

        Le Flight Time est associé à la fenêtre du prochain appui.
        Les valeurs négatives sont conservées.
        """

        if previous_record["flight_calculated"]:
            return

        release_timestamp = previous_record["release_timestamp"]

        if release_timestamp is None:
            return

        flight = calculate_flight_time(
            release_timestamp,
            next_record["press_timestamp"],
        )

        window_id = next_record["window_id"]

        self.window_manager.get_window_buffer(
            window_id
        )["flight_times"].append(flight)

        previous_record["flight_calculated"] = True

    # ------------------------------------------------------------------
    # FILE D'ATTENTE
    # ------------------------------------------------------------------

    def process_queued_event(self, event):
        """Traite un événement extrait de la file d'attente."""

        if not isinstance(event, tuple) or len(event) != 3:
            raise ValueError("Format d'événement invalide.")

        event_type, key, timestamp = event

        if event_type == "PRESS":
            return self.process_press_event(key, timestamp)

        elif event_type == "RELEASE":
            return self.process_release_event(key, timestamp)

        elif event_type == "STOP":
            return "STOP"

        else:
            raise ValueError(
                f"Type d'événement inconnu : {event_type}"
            )

    def process_available_events(self) -> int:
        """Traite tous les événements actuellement disponibles."""

        processed = 0

        while True:
            try:
                event = self.event_queue.get_nowait()
            except Empty:
                break

            result = self.process_queued_event(event)
            processed += 1

            if result == "STOP":
                self.stop_requested = True

        return processed

    # ------------------------------------------------------------------
    # EXPIRATION DES APPUIS
    # ------------------------------------------------------------------

    def expire_long_presses(self, current_timestamp: float) -> int:
        """
        Expire les appuis maintenus au-delà de MAX_HOLD_SECONDS.

        Les appuis expirés sont retirés de active_presses, mais leur
        historique reste dans press_sequence.
        """

        manager = self.window_manager
        expired_keys = []

        for key, record in manager.active_presses.items():
            hold_duration = (
                current_timestamp - record["press_timestamp"]
            )

            if hold_duration > self.max_hold_seconds:
                expired_keys.append(key)

        for key in expired_keys:
            record = manager.active_presses.pop(key)
            record["expired"] = True

            window_id = record["window_id"]

            manager.get_window_buffer(
                window_id
            )["expired_hold_count"] += 1

        return len(expired_keys)