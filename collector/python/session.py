"""
Module d'orchestration d'une session de capture multimodale.

Responsabilité :
- Coordonner les captures clavier et souris en parallèle.
- Partager une horloge unique (time.perf_counter()).
- Piloter l'EventProcessor clavier sans reproduire sa logique.
- Clôturer les appuis encore actifs à l'arrêt (appuis incomplets).
- Finaliser les fenêtres (complètes puis partielle) avec le timestamp
  de FIN DE SESSION (jamais "maintenant").
- Retourner les payloads JSON prêts à être envoyés à l'API.

Ce module ne contient PAS de logique de capture directe :
il délègue à events.py (clavier), mouse.py (souris) et windows.py (fenêtres).

Flux :
    1. Valider les paramètres
    2. Horloge commune, WindowManager, EventProcessor
    3. Démarrer listener clavier + thread souris (démarrage sécurisé)
    4. Boucle : traiter le clavier, expirer les appuis trop longs, vérifier Échap
    5. Arrêt coordonné (stop_event) : durée, Échap ou erreur
    6. Derniers événements clavier, appuis incomplets, transfert souris
    7. Finaliser les fenêtres avec session_end
    8. Retourner le résultat
"""

import json
import math
import threading
import time
from typing import Any, Dict, List, Optional

from pynput import keyboard

from .events import EventProcessor
from .mouse import capture_mouse_session
from .windows import WindowManager


# ==============================================================================
# CONSTANTES
# ==============================================================================

CAPTURE_DURATION: float = 30.0
WINDOW_DURATION: float = 30.0
MAX_HOLD_SECONDS: float = 5.0

# Intervalle de traitement de la file clavier (secondes)
PROCESSING_INTERVAL: float = 0.01

KEYBOARD_LISTENER_TIMEOUT: float = 2.0
MOUSE_THREAD_TIMEOUT: float = 2.0

# Tolérance pour détecter des timestamps souris incohérents (secondes)
MOUSE_TIMESTAMP_TOLERANCE: float = 1.0

DEFAULT_USER_ID: str = "demo_user_01"
DEFAULT_SESSION_ID: str = "demo_session_01"


# ==============================================================================
# OUTILS
# ==============================================================================

def _validate_positive_number(value: Any, name: str) -> float:
    """Vérifie qu'une valeur est numérique, finie et strictement positive."""
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
        or value <= 0
    ):
        raise ValueError(
            f"{name} doit être un nombre fini strictement positif."
        )
    return float(value)


def close_active_presses(manager: WindowManager) -> int:
    """
    Clôture les appuis encore maintenus à la fin de la session.

    - Aucun Hold Time ni Flight Time n'est fabriqué (le vrai relâchement
      n'a jamais été observé).
    - L'appui est retiré de active_presses (ce qui débloque la finalisation
      de sa fenêtre) mais reste dans press_sequence.
    - Il est marqué record["incomplete"] = True et compté dans
      buffer["incomplete_hold_count"], distinct de expired_hold_count.

    Returns:
        Nombre d'appuis clôturés.
    """
    closed = 0
    for key in list(manager.active_presses.keys()):
        record = manager.active_presses.pop(key)
        record["incomplete"] = True

        buffer = manager.get_window_buffer(record["window_id"])
        buffer["incomplete_hold_count"] = (
            buffer.get("incomplete_hold_count", 0) + 1
        )
        closed += 1
    return closed


def finalize_session(
    manager: WindowManager,
    stop_timestamp: float,
) -> List[Dict[str, Any]]:
    """
    Finalise les fenêtres complètes (ordre chronologique) puis la partielle.

    Args:
        manager: WindowManager de la session.
        stop_timestamp: timestamp de FIN DE SESSION (perf_counter), et non
            l'instant où cette fonction est appelée.

    Returns:
        Liste de payloads {"window_id": int, "json": str}.
    """
    if (
        not isinstance(stop_timestamp, (int, float))
        or isinstance(stop_timestamp, bool)
        or not math.isfinite(stop_timestamp)
    ):
        raise ValueError("stop_timestamp doit être un nombre fini.")

    payloads: List[Dict[str, Any]] = []
    payloads.extend(manager.finalize_completed_windows(stop_timestamp))

    partial = manager.finalize_partial_window(stop_timestamp)
    if partial is not None:
        payloads.append(partial)

    return payloads


# ==============================================================================
# ORCHESTRATION PRINCIPALE
# ==============================================================================

def run_session(
    user_id: str = DEFAULT_USER_ID,
    session_id: str = DEFAULT_SESSION_ID,
    duration: float = CAPTURE_DURATION,
    window_duration: float = WINDOW_DURATION,
    max_hold_seconds: float = MAX_HOLD_SECONDS,
    enable_keyboard: bool = True,
    enable_mouse: bool = True,
) -> Dict[str, Any]:
    """
    Orchestre une session complète de capture clavier + souris.

    Returns:
        Dictionnaire avec : user_id, session_id, session_start, session_end,
        session_duration, stop_reason ("duration" | "escape" | "error"),
        finalized (bool), payloads, keyboard_events_processed,
        mouse_events_received / valid / invalid, incomplete_presses,
        errors, warnings.
    """
    # --- 0. Validation ------------------------------------------------------
    duration = _validate_positive_number(duration, "duration")
    window_duration = _validate_positive_number(
        window_duration, "window_duration"
    )
    max_hold_seconds = _validate_positive_number(
        max_hold_seconds, "max_hold_seconds"
    )
    if not isinstance(user_id, str) or not user_id.strip():
        raise ValueError("user_id est obligatoire.")
    if not isinstance(session_id, str) or not session_id.strip():
        raise ValueError("session_id est obligatoire.")
    if not (enable_keyboard or enable_mouse):
        raise ValueError("Au moins une capture doit être activée.")

    errors: List[str] = []
    warnings: List[str] = []
    stop_reason: str = "duration"

    # --- 1. Horloge commune -------------------------------------------------
    session_start: float = time.perf_counter()
    stop_timestamp: float = session_start + duration
    # session_end sera fixé dans le finally, après l'arrêt réel des captures.
    session_end: float = stop_timestamp

    # --- 2. Manager + processeur clavier ------------------------------------
    manager = WindowManager(
        session_start=session_start,
        user_id=user_id,
        session_id=session_id,
        window_duration=window_duration,
    )
    processor = EventProcessor(
        window_manager=manager,
        max_hold_seconds=max_hold_seconds,
    )

    # Arrêt partagé : positionné à la fin (durée, Échap ou erreur)
    stop_event = threading.Event()

    keyboard_listener: Optional[keyboard.Listener] = None
    mouse_thread: Optional[threading.Thread] = None
    mouse_result: Optional[Dict[str, Any]] = None
    keyboard_events_processed = 0
    captures_started = False

    # Indicateurs de démarrage individuel (pour sécuriser le finally)
    keyboard_started = False
    mouse_started = False

    def _mouse_worker() -> None:
        """Capture souris dans un thread dédié."""
        nonlocal mouse_result
        try:
            # Durée restante calculée au démarrage réel du thread : la
            # capture souris se termine à stop_timestamp, pas après.
            remaining = max(stop_timestamp - time.perf_counter(), 0.01)
            mouse_result = capture_mouse_session(
                duration=remaining,
                validate=True,
                session_start=session_start,
                stop_event=stop_event,
            )
        except Exception as exc:  # noqa: BLE001
            errors.append(f"Erreur capture souris : {exc}")

    try:
        # --- 3. Démarrage sécurisé des captures -----------------------------
        if enable_keyboard:
            keyboard_listener = keyboard.Listener(
                on_press=processor.on_press,
                on_release=processor.on_release,
            )
            keyboard_listener.start()
            keyboard_started = True

        if enable_mouse:
            mouse_thread = threading.Thread(
                target=_mouse_worker,
                name="mouse-capture",
                daemon=True,
            )
            mouse_thread.start()
            mouse_started = True

        captures_started = True

        # --- 4. Boucle principale -------------------------------------------
        while True:
            now = time.perf_counter()
            if now >= stop_timestamp:
                break

            if enable_keyboard:
                keyboard_events_processed += (
                    processor.process_available_events()
                )
                processor.expire_long_presses(now)

                if processor.stop_requested:
                    stop_reason = "escape"
                    break

            time.sleep(PROCESSING_INTERVAL)

    except Exception as exc:  # noqa: BLE001
        phase = "boucle principale" if captures_started else "démarrage"
        errors.append(f"Erreur pendant le {phase} : {exc}")
        stop_reason = "error"
        # session_end sera fixé dans le finally.

    finally:
        # --- 5. Arrêt coordonné (même si le démarrage a échoué) -------------
        stop_event.set()

        if keyboard_started and keyboard_listener is not None:
            keyboard_listener.stop()
            keyboard_listener.join(timeout=KEYBOARD_LISTENER_TIMEOUT)
            if keyboard_listener.is_alive():
                errors.append("Listener clavier non terminé dans le délai.")

        if mouse_started and mouse_thread is not None:
            mouse_thread.join(timeout=MOUSE_THREAD_TIMEOUT)
            if mouse_thread.is_alive():
                errors.append("Thread souris non terminé dans le délai.")

        # Timestamp réel de fin de session, après l'arrêt des deux captures.
        session_end = time.perf_counter()

        # Derniers événements clavier encore dans la file
        if enable_keyboard:
            keyboard_events_processed += processor.process_available_events()

    def _build_result(
        finalized: bool,
        payloads: List[Dict[str, Any]],
        mouse_counts: tuple = (0, 0, 0),
        incomplete: int = 0,
    ) -> Dict[str, Any]:
        return {
            "user_id": user_id,
            "session_id": session_id,
            "session_start": session_start,
            "session_end": session_end,
            "session_duration": session_end - session_start,
            "stop_reason": stop_reason,
            "finalized": finalized,
            "payloads": payloads,
            "keyboard_events_processed": keyboard_events_processed,
            "mouse_events_received": mouse_counts[0],
            "mouse_events_valid": mouse_counts[1],
            "mouse_events_invalid": mouse_counts[2],
            "incomplete_presses": incomplete,
            "errors": errors,
            "warnings": warnings,
        }

    # --- Garde-fou : ne pas finaliser si le démarrage a échoué ou si une
    #     capture tourne encore (elle pourrait produire d'autres événements) --
    capture_still_running = (
        (mouse_thread is not None and mouse_thread.is_alive())
        or (keyboard_listener is not None and keyboard_listener.is_alive())
    )
    if not captures_started or capture_still_running:
        stop_reason = "error"
        return _build_result(finalized=False, payloads=[])

    # --- 6a. Appuis clavier encore actifs -> incomplets ---------------------
    # Les expirations normales ont déjà eu lieu dans la boucle principale.
    incomplete_presses = 0
    if enable_keyboard:
        incomplete_presses = close_active_presses(manager)

    # --- 6b. Transfert des événements souris --------------------------------
    # Timestamps déjà absolus (session_start transmis) : aucune conversion.
    mouse_received = mouse_valid = mouse_invalid = 0

    if mouse_result is not None:
        valid_events = mouse_result.get("valid_events", [])
        mouse_received = len(mouse_result.get("events", valid_events))
        mouse_valid = len(valid_events)
        mouse_invalid = len(mouse_result.get("invalid_events", []))

        if valid_events:
            timestamps = [e["timestamp"] for e in valid_events]
            if (
                min(timestamps) < session_start - MOUSE_TIMESTAMP_TOLERANCE
                or max(timestamps) > session_end + MOUSE_TIMESTAMP_TOLERANCE
            ):
                warnings.append(
                    "Timestamps souris hors de l'intervalle de session : "
                    "vérifier la synchronisation des horloges."
                )

        for event in valid_events:
            manager.add_mouse_event(event)
    elif enable_mouse:
        warnings.append("Aucun résultat de capture souris.")

    # --- 7. Finalisation avec la FIN DE SESSION -----------------------------
    payloads = finalize_session(manager, session_end)

    # --- 8. Résultat --------------------------------------------------------
    return _build_result(
        finalized=True,
        payloads=payloads,
        mouse_counts=(mouse_received, mouse_valid, mouse_invalid),
        incomplete=incomplete_presses,
    )


# ==============================================================================
# DÉMONSTRATION
# ==============================================================================

def demo_session(
    duration: float = 10.0,
    window_duration: float = 5.0,
    enable_keyboard: bool = True,
    enable_mouse: bool = True,
) -> None:
    """Lance une session courte et affiche un résumé des payloads."""
    print("=" * 60)
    print(f"Session de {duration}s | fenêtres de {window_duration}s")
    print("Tape au clavier, bouge la souris. Échap pour arrêter.")
    print("=" * 60)

    result = run_session(
        user_id="demo_user",
        session_id="demo_session",
        duration=duration,
        window_duration=window_duration,
        enable_keyboard=enable_keyboard,
        enable_mouse=enable_mouse,
    )

    print(f"Durée réelle          : {result['session_duration']:.3f}s")
    print(f"Motif d'arrêt         : {result['stop_reason']}")
    print(f"Finalisée             : {result['finalized']}")
    print(f"Événements clavier    : {result['keyboard_events_processed']}")
    print(
        f"Souris valides/invalid: {result['mouse_events_valid']}"
        f" / {result['mouse_events_invalid']}"
    )
    print(f"Appuis incomplets     : {result['incomplete_presses']}")
    print(f"Payloads              : {len(result['payloads'])}")

    for payload in result["payloads"]:
        data = json.loads(payload["json"])
        print(
            f"  {data['window_id']} | {data['completion']:8s} | "
            f"{data['quality']['global']:18s} | "
            f"{data['duration_seconds']:.2f}s"
        )

    for message in result["warnings"]:
        print(f"  ! {message}")
    for message in result["errors"]:
        print(f"  ERREUR : {message}")
    print("=" * 60)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Session de capture multimodale (clavier + souris)"
    )
    parser.add_argument("--duration", type=float, default=10.0)
    parser.add_argument("--window", type=float, default=5.0)
    parser.add_argument("--no-keyboard", action="store_true")
    parser.add_argument("--no-mouse", action="store_true")
    args = parser.parse_args()

    demo_session(
        duration=args.duration,
        window_duration=args.window,
        enable_keyboard=not args.no_keyboard,
        enable_mouse=not args.no_mouse,
    )