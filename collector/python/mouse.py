
"""
Module de capture et d'analyse des événements souris.

Responsabilités :
- Capturer les événements souris avec pynput.
- Valider les événements.
- Extraire les features globales de déplacement, clic et scroll.
- Organiser les événements en fenêtres temporelles.
- Extraire les features par fenêtre.
- Évaluer la qualité des données.

Conventions :
- Timestamps : secondes, issus de time.perf_counter().
- Distances : pixels.
- Vitesses : pixels/seconde.
- Accélérations : pixels/seconde².
- Durées comportementales : millisecondes pour les features agrégées.
- Fenêtres : intervalles [start, end[.
"""

import math
import statistics
import time
import threading

from collections import defaultdict, deque
from queue import Queue, Empty
from typing import Any, Dict, List, Optional, Tuple

from pynput import mouse


# ==============================================================================
# 1. IMPORTS ET CONSTANTES
# ==============================================================================

WINDOW_DURATION = 30.0
CAPTURE_DURATION = 30.0

MIN_MOVE_DT_SECONDS = 0.05
MIN_MOVE_DISTANCE_PX = 1.0

MIN_MOVE_SAMPLES = 3
MIN_CLICK_SAMPLES = 2

VALID_EVENT_TYPES = {
    "MOVE",
    "CLICK_PRESS",
    "CLICK_RELEASE",
    "SCROLL",
}

VALID_BUTTONS = {
    "left",
    "right",
    "middle",
}


# ==============================================================================
# 2. VALIDATION DES ÉVÉNEMENTS
# ==============================================================================

def validate_mouse_event(event: Any) -> Tuple[bool, str]:
    """Valide la structure et les valeurs d'un événement souris."""

    if not isinstance(event, dict):
        return False, "L'événement doit être un dictionnaire."

    event_type = event.get("type")

    if event_type not in VALID_EVENT_TYPES:
        return False, "Type d'événement inconnu."

    timestamp = event.get("timestamp")

    if (
        not isinstance(timestamp, (int, float))
        or isinstance(timestamp, bool)
        or not math.isfinite(timestamp)
    ):
        return False, "Timestamp invalide."

    if event_type == "MOVE":

        for coordinate in ("x", "y"):
            value = event.get(coordinate)

            if (
                not isinstance(value, (int, float))
                or isinstance(value, bool)
                or not math.isfinite(value)
            ):
                return False, f"Coordonnée {coordinate} invalide."

    elif event_type in {"CLICK_PRESS", "CLICK_RELEASE"}:

        if event.get("button") not in VALID_BUTTONS:
            return False, "Bouton de souris invalide."

    elif event_type == "SCROLL":

        for direction in ("dx", "dy"):
            value = event.get(direction)

            if (
                not isinstance(value, (int, float))
                or isinstance(value, bool)
                or not math.isfinite(value)
            ):
                return False, f"Valeur {direction} invalide."

    return True, "OK"


# ==============================================================================
# 3. CAPTURE RÉELLE ENCAPSULÉE
# ==============================================================================

def _build_callbacks(
    event_queue: Queue,
    start_perf: float,
    absolute_timestamps: bool = False,
) -> Dict[str, Any]:
    """Construit les callbacks internes de capture."""

    def get_timestamp() -> float:
        if absolute_timestamps:
            return time.perf_counter()

        return time.perf_counter() - start_perf

    def on_move(x: float, y: float) -> None:
        event_queue.put({
            "type": "MOVE",
            "timestamp": get_timestamp(),
            "x": x,
            "y": y,
        })

    def on_click(
        x: float,
        y: float,
        button: Any,
        pressed: bool,
    ) -> None:

        button_name = getattr(button, "name", None)

        if button_name not in VALID_BUTTONS:
            return

        event_type = (
            "CLICK_PRESS" if pressed else "CLICK_RELEASE"
        )

        event_queue.put({
            "type": event_type,
            "timestamp": get_timestamp(),
            "button": button_name,
            "x": x,
            "y": y,
        })

    def on_scroll(
        x: float,
        y: float,
        dx: float,
        dy: float,
    ) -> None:

        event_queue.put({
            "type": "SCROLL",
            "timestamp": get_timestamp(),
            "dx": dx,
            "dy": dy,
        })

    return {
        "on_move": on_move,
        "on_click": on_click,
        "on_scroll": on_scroll,
    }

def start_mouse_listener(
    event_queue: Queue,
) -> mouse.Listener:
    """
    Démarre un listener souris non bloquant.

    Les événements sont enregistrés dans la file
    avec des timestamps absolus issus de perf_counter().
    """

    callbacks = _build_callbacks(
        event_queue=event_queue,
        start_perf=time.perf_counter(),
        absolute_timestamps=True,
    )

    listener = mouse.Listener(
        on_move=callbacks["on_move"],
        on_click=callbacks["on_click"],
        on_scroll=callbacks["on_scroll"],
    )

    listener.start()

    return listener

def capture_mouse_session(
    duration: float = CAPTURE_DURATION,
    validate: bool = True,
    session_start: Optional[float] = None,
    stop_event: Optional[threading.Event] = None,
) -> Dict[str, Any]:
    """
    Capture les événements souris.

    session_start :
        Si fourni, les timestamps sont absolus et utilisent
        la même horloge monotone que le clavier.

        Sinon, ils sont relatifs au début de la capture.
    """

    if (
        isinstance(duration, bool)
        or not isinstance(duration, (int, float))
        or not math.isfinite(duration)
        or duration <= 0
    ):
        raise ValueError("La durée doit être positive et finie.")

    if session_start is not None:
        if (
            isinstance(session_start, bool)
            or not isinstance(session_start, (int, float))
            or not math.isfinite(session_start)
        ):
            raise ValueError("session_start doit être numérique et fini.")

    event_queue = Queue()

    capture_start = time.perf_counter()

    if session_start is not None and session_start > capture_start:
        raise ValueError("session_start ne peut pas être dans le futur.")

    callbacks = _build_callbacks(
        event_queue,
        capture_start,
        absolute_timestamps=(session_start is not None),
    )

    listener = mouse.Listener(
        on_move=callbacks["on_move"],
        on_click=callbacks["on_click"],
        on_scroll=callbacks["on_scroll"],
    )

    listener.start()
    try:
        if stop_event is None:
            time.sleep(duration)
        else:
            stop_event.wait(timeout=duration)

    finally:
        listener.stop()
        listener.join()
        capture_end = time.perf_counter()
        session_duration = capture_end - capture_start

    # Récupération des événements
    all_events = []

    while True:
        try:
            all_events.append(event_queue.get_nowait())
        except Empty:
            break

    all_events.sort(key=lambda event: event["timestamp"])

    valid_events = []
    invalid_events = []

    for index, event in enumerate(all_events):

        is_valid, message = (
            validate_mouse_event(event)
            if validate
            else (True, "OK")
        )

        timestamp = event.get("timestamp")

        if session_start is not None:
            timestamp_in_range = (
                isinstance(timestamp, (int, float))
                and not isinstance(timestamp, bool)
                and capture_start <= timestamp < capture_end
            )
        else:
            timestamp_in_range = (
                isinstance(timestamp, (int, float))
                and not isinstance(timestamp, bool)
                and 0 <= timestamp < session_duration
            )

        if is_valid and timestamp_in_range:
            valid_events.append(event)
        else:
            invalid_events.append({
                "index": index,
                "event": event,
                "reason": (
                    message
                    if not is_valid
                    else "Timestamp hors session"
                ),
            })

    return {
        "events": all_events,
        "valid_events": valid_events,
        "invalid_events": invalid_events,
        "session_duration": session_duration,
        "session_start": (
            float(session_start)
            if session_start is not None
            else capture_start
        ),
    }
# ==============================================================================
# 4. FEATURES DE DÉPLACEMENT
# ==============================================================================

def filter_movement_points(
    events: List[Dict[str, Any]],
    min_dt: float = MIN_MOVE_DT_SECONDS,
    min_distance: float = MIN_MOVE_DISTANCE_PX,
) -> List[Dict[str, Any]]:
    """
    Filtre les points MOVE selon deux critères :
    - intervalle temporel minimal ;
    - distance spatiale minimale.
    """

    if min_dt < 0:
        raise ValueError("min_dt doit être positif ou nul.")

    if min_distance < 0:
        raise ValueError("min_distance doit être positif ou nul.")

    if not events:
        return []

    sorted_events = sorted(
        events,
        key=lambda event: event["timestamp"],
    )

    accepted = [sorted_events[0]]

    for event in sorted_events[1:]:

        previous = accepted[-1]

        dt = event["timestamp"] - previous["timestamp"]

        if dt < min_dt:
            continue

        distance = math.hypot(
            event["x"] - previous["x"],
            event["y"] - previous["y"],
        )

        if distance < min_distance:
            continue

        accepted.append(event)

    return accepted


def calculate_movement_segments(
    points: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Calcule les segments entre les points acceptés."""

    segments = []

    for previous, current in zip(points[:-1], points[1:]):

        dt = current["timestamp"] - previous["timestamp"]

        if dt <= 0:
            continue

        dx = current["x"] - previous["x"]
        dy = current["y"] - previous["y"]

        distance = math.hypot(dx, dy)
        speed = distance / dt

        segments.append({
            "start_timestamp": previous["timestamp"],
            "end_timestamp": current["timestamp"],
            "dt": dt,
            "distance": distance,
            "speed": speed,
            "dx": dx,
            "dy": dy,
        })

    return segments


def calculate_accelerations(
    segments: List[Dict[str, Any]],
) -> List[float]:
    """Calcule les accélérations entre segments consécutifs."""

    accelerations = []

    for previous, current in zip(segments[:-1], segments[1:]):

        previous_midpoint = (
            previous["start_timestamp"]
            + previous["end_timestamp"]
        ) / 2

        current_midpoint = (
            current["start_timestamp"]
            + current["end_timestamp"]
        ) / 2

        dt = current_midpoint - previous_midpoint

        if dt <= 0:
            continue

        acceleration = (
            current["speed"] - previous["speed"]
        ) / dt

        accelerations.append(acceleration)

    return accelerations


def extract_movement_data(
    events: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Pipeline commun de déplacement.

    Cette fonction est utilisée pour les features globales
    et pour les features par fenêtre.
    """

    move_events = [
        event for event in events
        if event["type"] == "MOVE"
    ]

    accepted_points = filter_movement_points(
        move_events,
        min_dt=MIN_MOVE_DT_SECONDS,
        min_distance=MIN_MOVE_DISTANCE_PX,
    )

    segments = calculate_movement_segments(accepted_points)

    accelerations = calculate_accelerations(segments)

    return {
        "move_event_count": len(move_events),
        "accepted_points": accepted_points,
        "segments": segments,
        "accelerations": accelerations,
    }


def calculate_movement_features(
    segments: List[Dict[str, Any]],
    accelerations: Optional[List[float]] = None,
) -> Dict[str, Any]:
    """Calcule les statistiques de déplacement."""

    if not segments:

        return {
            "status": "no_data",
            "movement_segment_count": 0,
            "total_distance_px": 0.0,
            "total_movement_duration_s": 0.0,
            "average_speed_px_s": None,
            "mean_segment_speed_px_s": None,
            "median_speed_px_s": None,
            "min_speed_px_s": None,
            "max_speed_px_s": None,
            "speed_std_px_s": None,
            "mean_distance_px": None,
            "max_distance_px": None,
            "acceleration_count": 0,
            "mean_acceleration_px_s2": None,
            "median_acceleration_px_s2": None,
            "mean_absolute_acceleration_px_s2": None,
            "max_absolute_acceleration_px_s2": None,
        }

    distances = [segment["distance"] for segment in segments]
    speeds = [segment["speed"] for segment in segments]
    durations = [segment["dt"] for segment in segments]

    total_distance = sum(distances)
    total_duration = sum(durations)

    if accelerations is None:
        accelerations = []

    absolute_accelerations = [
        abs(value) for value in accelerations
    ]

    return {
        "status": "collected",
        "movement_segment_count": len(segments),
        "total_distance_px": total_distance,
        "total_movement_duration_s": total_duration,
        "average_speed_px_s": (
            total_distance / total_duration
            if total_duration > 0
            else None
        ),
        "mean_segment_speed_px_s": statistics.mean(speeds),
        "median_speed_px_s": statistics.median(speeds),
        "min_speed_px_s": min(speeds),
        "max_speed_px_s": max(speeds),
        "speed_std_px_s": statistics.pstdev(speeds),
        "mean_distance_px": statistics.mean(distances),
        "max_distance_px": max(distances),
        "acceleration_count": len(accelerations),
        "mean_acceleration_px_s2": (
            statistics.mean(accelerations)
            if accelerations else None
        ),
        "median_acceleration_px_s2": (
            statistics.median(accelerations)
            if accelerations else None
        ),
        "mean_absolute_acceleration_px_s2": (
            statistics.mean(absolute_accelerations)
            if absolute_accelerations else None
        ),
        "max_absolute_acceleration_px_s2": (
            max(absolute_accelerations)
            if absolute_accelerations else None
        ),
    }


# ==============================================================================
# 5. FEATURES DE CLIC
# ==============================================================================

def pair_mouse_clicks(
    events: List[Dict[str, Any]],
) -> Tuple[
    List[Dict[str, Any]],
    List[Dict[str, Any]],
    List[Dict[str, Any]],
]:
    """
    Appar ie les pressions et relâchements par bouton.

    Utilise une file par bouton afin de ne pas écraser
    un appui précédent en cas d'événements répétés.

    Retourne :
        completed_clicks
        incomplete_presses
        unmatched_releases
    """

    pending_presses = defaultdict(deque)

    completed_clicks = []
    unmatched_releases = []

    ordered_events = sorted(
        events,
        key=lambda event: event["timestamp"],
    )

    for event in ordered_events:

        event_type = event["type"]
        button = event.get("button")

        if event_type == "CLICK_PRESS":

            pending_presses[button].append(event)

        elif event_type == "CLICK_RELEASE":

            if not pending_presses[button]:
                unmatched_releases.append(event)
                continue

            press_event = pending_presses[button].popleft()

            hold_time = (
                event["timestamp"] - press_event["timestamp"]
            )

            completed_clicks.append({
                "button": button,
                "press_timestamp": press_event["timestamp"],
                "release_timestamp": event["timestamp"],
                "hold_time": hold_time,
            })

    incomplete_presses = []

    for button_events in pending_presses.values():
        incomplete_presses.extend(button_events)

    incomplete_presses.sort(
        key=lambda event: event["timestamp"]
    )

    return (
        completed_clicks,
        incomplete_presses,
        unmatched_releases,
    )


def calculate_click_statistics(
    values: List[float],
    prefix: str,
) -> Dict[str, Any]:
    """Calcule les statistiques d'une liste de durées en ms."""

    if not values:

        return {
            f"{prefix}_count": 0,
            f"{prefix}_mean_ms": None,
            f"{prefix}_median_ms": None,
            f"{prefix}_min_ms": None,
            f"{prefix}_max_ms": None,
            f"{prefix}_std_ms": None,
        }

    values_ms = [
        value * 1000 for value in values
    ]

    return {
        f"{prefix}_count": len(values_ms),
        f"{prefix}_mean_ms": statistics.mean(values_ms),
        f"{prefix}_median_ms": statistics.median(values_ms),
        f"{prefix}_min_ms": min(values_ms),
        f"{prefix}_max_ms": max(values_ms),
        f"{prefix}_std_ms": statistics.pstdev(values_ms),
    }


def calculate_click_frequency_features(
    click_press_events: List[Dict[str, Any]],
    session_duration: float,
) -> Dict[str, Any]:
    """Calcule le nombre et la fréquence des clics."""

    if session_duration <= 0:
        raise ValueError("La durée de session doit être positive.")

    click_count = len(click_press_events)

    return {
        "click_count": click_count,
        "click_frequency_per_second": (
            click_count / session_duration
        ),
        "click_frequency_per_minute": (
            click_count / session_duration
        ) * 60,
    }


def calculate_global_click_features(
    events: List[Dict[str, Any]],
    session_duration: float,
) -> Dict[str, Any]:
    """Calcule les features de clic sur toute la session."""

    press_events = [
        event for event in events
        if event["type"] == "CLICK_PRESS"
    ]

    completed, incomplete, unmatched = pair_mouse_clicks(events)

    hold_times = [
        click["hold_time"] for click in completed
    ]

    ordered_presses = sorted(
        press_events,
        key=lambda event: event["timestamp"],
    )

    inter_click_intervals = [
        ordered_presses[i]["timestamp"]
        - ordered_presses[i - 1]["timestamp"]
        for i in range(1, len(ordered_presses))
    ]

    features = {}

    features.update(
        calculate_click_statistics(
            hold_times,
            "click_hold",
        )
    )

    features.update(
        calculate_click_statistics(
            inter_click_intervals,
            "inter_click",
        )
    )

    features.update(
        calculate_click_frequency_features(
            press_events,
            session_duration,
        )
    )

    features["completed_click_count"] = len(completed)
    features["incomplete_press_count"] = len(incomplete)
    features["unmatched_release_count"] = len(unmatched)

    return features


# ==============================================================================
# 6. FEATURES DE SCROLL
# ==============================================================================

def calculate_scroll_features(
    scroll_events: List[Dict[str, Any]],
    session_duration: float,
) -> Dict[str, Any]:
    """Calcule les features de défilement sur une session."""

    if session_duration <= 0:
        raise ValueError("La durée de session doit être positive.")

    events = sorted(
        scroll_events,
        key=lambda event: event["timestamp"],
    )

    if not events:

        return {
            "status": "no_data",
            "scroll_count": 0,
            "scroll_dx_total": 0,
            "scroll_dy_total": 0,
            "scroll_dx_absolute": 0,
            "scroll_dy_absolute": 0,
            "scroll_positive_count": 0,
            "scroll_negative_count": 0,
            "scroll_zero_vertical_count": 0,
            "scroll_mean_interval_ms": None,
            "scroll_frequency_per_second": 0.0,
        }

    dx_values = [event["dx"] for event in events]
    dy_values = [event["dy"] for event in events]

    timestamps = [
        event["timestamp"] for event in events
    ]

    intervals = [
        (timestamps[i] - timestamps[i - 1]) * 1000
        for i in range(1, len(timestamps))
    ]

    return {
        "status": "collected",
        "scroll_count": len(events),
        "scroll_dx_total": sum(dx_values),
        "scroll_dy_total": sum(dy_values),
        "scroll_dx_absolute": sum(abs(v) for v in dx_values),
        "scroll_dy_absolute": sum(abs(v) for v in dy_values),
        "scroll_positive_count": sum(v > 0 for v in dy_values),
        "scroll_negative_count": sum(v < 0 for v in dy_values),
        "scroll_zero_vertical_count": sum(v == 0 for v in dy_values),
        "scroll_mean_interval_ms": (
            statistics.mean(intervals)
            if intervals else None
        ),
        "scroll_frequency_per_second": (
            len(events) / session_duration
        ),
    }


# ==============================================================================
# 7. FEATURES GLOBALES DE LA SESSION
# ==============================================================================



def extract_mouse_session_features(
    events: List[Dict[str, Any]],
    session_duration: float,
) -> Dict[str, Any]:
    """
    Extrait les features globales de toute la session.
    Chaque modalité conserve son propre statut qualité.
    """

    if (
        not isinstance(session_duration, (int, float))
        or isinstance(session_duration, bool)
        or not math.isfinite(session_duration)
        or session_duration <= 0
    ):
        raise ValueError(
            "La durée de session doit être positive et finie."
        )

    # 1. Déplacements
    movement_data = extract_movement_data(events)

    movement_features = calculate_movement_features(
        movement_data["segments"],
        movement_data["accelerations"],
    )

    movement_features["move_event_count"] = (
        movement_data["move_event_count"]
    )

    movement_features["accepted_move_point_count"] = (
        len(movement_data["accepted_points"])
    )

    # Retirer le statut interne des statistiques
    movement_features.pop("status")

    # Appliquer exactement la règle de qualité des fenêtres
    if movement_data["move_event_count"] == 0:
        movement_status = "no_data"

    elif len(movement_data["accepted_points"]) >= MIN_MOVE_SAMPLES:
        movement_status = "collected"

    else:
        movement_status = "insufficient_data"

    # 2. Clics
    click_features = calculate_global_click_features(
        events,
        session_duration,
    )

    completed_click_count = click_features.get(
        "completed_click_count", 0
    )

    click_event_count = sum(
        event["type"] in {"CLICK_PRESS", "CLICK_RELEASE"}
        for event in events
    )

    incomplete_press_count = click_features.get(
        "incomplete_press_count", 0
    )

    if click_event_count == 0 and incomplete_press_count == 0:
        click_status = "no_data"
    elif completed_click_count >= MIN_CLICK_SAMPLES:
        click_status = "collected"
    else:
        click_status = "insufficient_data"

    # 3. Défilement
    scroll_events = [
        event for event in events
        if event["type"] == "SCROLL"
    ]

    scroll_features = calculate_scroll_features(
        scroll_events,
        session_duration,
    )

    scroll_status = scroll_features.pop("status")

    # 4. Statut global
    statuses = [
        movement_status,
        click_status,
        scroll_status,
    ]

    if all(status == "collected" for status in statuses):
        global_status = "collected"
    elif all(status == "no_data" for status in statuses):
        global_status = "no_data"
    else:
        global_status = "insufficient_data"

    # 5. Résultat final
    return {
        **movement_features,
        **click_features,
        **scroll_features,
        "movement_status": movement_status,
        "click_status": click_status,
        "scroll_status": scroll_status,
        "global_status": global_status,
    }



# ==============================================================================
# 8. ORGANISATION TEMPORELLE
# ==============================================================================

def build_mouse_windows(
    events: List[Dict[str, Any]],
    session_duration: float,
    window_duration: float = WINDOW_DURATION,
) -> List[Dict[str, Any]]:
    """
    Construit les fenêtres temporelles.

    Les fenêtres utilisent les intervalles [start, end[.
    """

    if session_duration <= 0:
        raise ValueError("La durée de session doit être positive.")

    if window_duration <= 0:
        raise ValueError("La durée de fenêtre doit être positive.")

    for event in events:

        timestamp = event.get("timestamp")

        if (
            not isinstance(timestamp, (int, float))
            or isinstance(timestamp, bool)
            or not math.isfinite(timestamp)
        ):
            raise ValueError("Timestamp invalide.")

        if not 0 <= timestamp < session_duration:
            raise ValueError(
                f"Événement hors session : {timestamp}"
            )

    number_of_windows = math.ceil(
        session_duration / window_duration
    )

    windows = []

    for index in range(number_of_windows):

        start = index * window_duration

        end = min(
            start + window_duration,
            session_duration,
        )

        windows.append({
            "window_id": f"w{index:04d}",
            "start": start,
            "end": end,
            "duration": end - start,
            "is_complete": math.isclose(
                end - start,
                window_duration,
            ),
            "events": [],
        })

    for event in sorted(
        events,
        key=lambda item: item["timestamp"],
    ):

        index = int(
            event["timestamp"] // window_duration
        )

        windows[index]["events"].append(event)

    return windows


def calculate_basic_statistics(
    values: List[float],
) -> Dict[str, Any]:
    """Calcule des statistiques descriptives."""

    values = list(values)

    if not values:

        return {
            "count": 0,
            "mean": None,
            "median": None,
            "min": None,
            "max": None,
            "std": None,
        }

    return {
        "count": len(values),
        "mean": statistics.mean(values),
        "median": statistics.median(values),
        "min": min(values),
        "max": max(values),
        "std": (
            statistics.pstdev(values)
            if len(values) > 1
            else 0.0
        ),
    }


# ==============================================================================
# 9. FEATURES PAR FENÊTRE
# ==============================================================================

def calculate_window_movement_features(
    window: Dict[str, Any],
) -> Dict[str, Any]:
    """Calcule les features de déplacement d'une fenêtre."""

    movement_data = extract_movement_data(
        window["events"]
    )

    movement_features = calculate_movement_features(
        movement_data["segments"],
        movement_data["accelerations"],
    )

    return {
        **movement_features,
        "move_event_count": movement_data["move_event_count"],
        "accepted_move_point_count": len(
            movement_data["accepted_points"]
        ),
    }


def get_window_id_for_timestamp(
    timestamp: float,
    windows: List[Dict[str, Any]],
) -> Optional[str]:
    """Retourne la fenêtre contenant le timestamp."""

    for window in windows:

        if window["start"] <= timestamp < window["end"]:
            return window["window_id"]

    return None


def add_click_features_to_windows(
    windows: List[Dict[str, Any]],
    completed_clicks: List[Dict[str, Any]],
    click_press_events: Optional[List[Dict[str, Any]]] = None,
) -> Tuple[
    Dict[str, List[Dict[str, Any]]],
    Dict[str, List[float]],
]:
    """
    Répartit les clics et les intervalles entre fenêtres.

    - Un clic est attribué à la fenêtre de son appui.
    - Un intervalle est attribué à la fenêtre du deuxième appui.
    - Les intervalles utilisent tous les événements CLICK_PRESS,
      y compris les appuis incomplets.
    """

    clicks_by_window = {
        window["window_id"]: []
        for window in windows
    }

    intervals_by_window = {
        window["window_id"]: []
        for window in windows
    }

    ordered_clicks = sorted(
        completed_clicks,
        key=lambda click: click["press_timestamp"],
    )

    for click in ordered_clicks:

        window_id = get_window_id_for_timestamp(
            click["press_timestamp"],
            windows,
        )

        if window_id is not None:
            clicks_by_window[window_id].append(click)

    if click_press_events is None:

        press_timestamps = [
            click["press_timestamp"]
            for click in ordered_clicks
        ]

    else:

        press_timestamps = sorted(
            event["timestamp"]
            for event in click_press_events
        )

    for previous, current in zip(
        press_timestamps[:-1],
        press_timestamps[1:],
    ):

        interval = current - previous

        window_id = get_window_id_for_timestamp(
            current,
            windows,
        )

        if window_id is not None:
            intervals_by_window[window_id].append(interval)

    return clicks_by_window, intervals_by_window


def calculate_window_click_features(
    window: Dict[str, Any],
    clicks: List[Dict[str, Any]],
    intervals: List[float],
) -> Dict[str, Any]:
    """Calcule les features de clic d'une fenêtre."""

    press_count = sum(
        event["type"] == "CLICK_PRESS"
        for event in window["events"]
    )

    release_count = sum(
        event["type"] == "CLICK_RELEASE"
        for event in window["events"]
    )

    hold_stats = calculate_basic_statistics([
        click["hold_time"] * 1000
        for click in clicks
    ])

    interval_stats = calculate_basic_statistics([
        interval * 1000
        for interval in intervals
    ])

    return {
        "click_press_count": press_count,
        "click_release_count": release_count,
        "click_count": len(clicks),

        "click_hold_mean_ms": hold_stats["mean"],
        "click_hold_median_ms": hold_stats["median"],
        "click_hold_min_ms": hold_stats["min"],
        "click_hold_max_ms": hold_stats["max"],
        "click_hold_std_ms": hold_stats["std"],

        "inter_click_count": interval_stats["count"],
        "inter_click_mean_ms": interval_stats["mean"],
        "inter_click_median_ms": interval_stats["median"],
        "inter_click_min_ms": interval_stats["min"],
        "inter_click_max_ms": interval_stats["max"],
        "inter_click_std_ms": interval_stats["std"],
    }


def calculate_window_scroll_features(
    window: Dict[str, Any],
) -> Dict[str, Any]:
    """Calcule les features de scroll d'une fenêtre."""

    scrolls = [
        event for event in window["events"]
        if event["type"] == "SCROLL"
    ]

    dx_values = [event["dx"] for event in scrolls]
    dy_values = [event["dy"] for event in scrolls]

    timestamps = [
        event["timestamp"] for event in scrolls
    ]

    intervals = [
        (timestamps[i] - timestamps[i - 1]) * 1000
        for i in range(1, len(timestamps))
    ]

    return {
        "scroll_count": len(scrolls),
        "scroll_dx_total": sum(dx_values),
        "scroll_dy_total": sum(dy_values),
        "scroll_dx_absolute": sum(abs(v) for v in dx_values),
        "scroll_dy_absolute": sum(abs(v) for v in dy_values),
        "scroll_positive_count": sum(v > 0 for v in dy_values),
        "scroll_negative_count": sum(v < 0 for v in dy_values),
        "scroll_zero_vertical_count": sum(v == 0 for v in dy_values),
        "scroll_mean_interval_ms": (
            statistics.mean(intervals)
            if intervals else None
        ),
    }


# ==============================================================================
# 10. CONTRÔLE DE QUALITÉ
# ==============================================================================

def calculate_mouse_window_quality(
    window: Dict[str, Any],
    features: Dict[str, Any],
    incomplete_session_presses: List[Dict[str, Any]],
    unmatched_session_releases: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Évalue la qualité des trois modalités.

    Statut global :
    - collected : toutes les modalités sont collected.
    - no_data : toutes les modalités sont no_data.
    - insufficient_data : tous les autres cas.
    """

    window_start = window["start"]
    window_end = window["end"]

    move_count = features["move_event_count"]

    click_event_count = (
        features["click_press_count"]
        + features["click_release_count"]
    )

    scroll_count = features["scroll_count"]

    incomplete_press_count = sum(
        1
        for event in incomplete_session_presses
        if window_start <= event["timestamp"] < window_end
    )

    unmatched_release_count = sum(
        1
        for event in unmatched_session_releases
        if window_start <= event["timestamp"] < window_end
    )

    # Mouvement
    if move_count == 0:
        movement_status = "no_data"

    elif features["accepted_move_point_count"] >= MIN_MOVE_SAMPLES:
        movement_status = "collected"

    else:
        movement_status = "insufficient_data"

    # Clic
    if click_event_count == 0 and incomplete_press_count == 0:
        click_status = "no_data"

    elif features["click_count"] >= MIN_CLICK_SAMPLES:
        click_status = "collected"

    else:
        click_status = "insufficient_data"

    # Scroll
    if scroll_count == 0:
        scroll_status = "no_data"

    else:
        scroll_status = "collected"

    # Statut global strict
    statuses = [
        movement_status,
        click_status,
        scroll_status,
    ]

    if all(status == "collected" for status in statuses):
        global_status = "collected"

    elif all(status == "no_data" for status in statuses):
        global_status = "no_data"

    else:
        global_status = "insufficient_data"

    return {
        "movement": movement_status,
        "click": click_status,
        "scroll": scroll_status,
        "global": global_status,
        "incomplete_press_count": incomplete_press_count,
        "unmatched_release_count": unmatched_release_count,
    }


def build_mouse_window_quality(
    windows: List[Dict[str, Any]],
    mouse_window_features: Dict[str, Dict[str, Any]],
    incomplete_session_presses: List[Dict[str, Any]],
    unmatched_session_releases: List[Dict[str, Any]],
) -> Dict[str, Dict[str, Any]]:
    """Construit la qualité de toutes les fenêtres."""

    return {
        window["window_id"]: calculate_mouse_window_quality(
            window,
            mouse_window_features[window["window_id"]],
            incomplete_session_presses,
            unmatched_session_releases,
        )
        for window in windows
    }


# ==============================================================================
# 11. CONSTRUCTION ET VALIDATION DES RÉSULTATS
# ==============================================================================

def build_mouse_window_features(
    windows: List[Dict[str, Any]],
    clicks_by_window: Dict[str, List[Dict[str, Any]]],
    intervals_by_window: Dict[str, List[float]],
) -> Dict[str, Dict[str, Any]]:
    """Construit les features de chaque fenêtre."""

    mouse_window_features = {}

    for window in windows:

        window_id = window["window_id"]

        movement = calculate_window_movement_features(window)

        click = calculate_window_click_features(
            window,
            clicks_by_window.get(window_id, []),
            intervals_by_window.get(window_id, []),
        )

        scroll = calculate_window_scroll_features(window)

        mouse_window_features[window_id] = {
            **movement,
            **click,
            **scroll,
        }

    return mouse_window_features


def display_window_results(
    mouse_window_features: Dict[str, Dict[str, Any]],
    mouse_window_quality: Dict[str, Dict[str, Any]],
) -> None:
    """Affiche les features et la qualité par fenêtre."""

    for window_id, features in mouse_window_features.items():

        print("\n" + "=" * 55)
        print("FEATURES :", window_id)
        print("=" * 55)

        for name, value in features.items():

            if isinstance(value, float):
                print(f"{name}: {value:.4f}")

            else:
                print(f"{name}: {value}")

        print("\nQUALITÉ :")

        from pprint import pprint
        pprint(mouse_window_quality[window_id])


def validate_window_features_and_quality(
    windows: List[Dict[str, Any]],
    mouse_window_features: Dict[str, Dict[str, Any]],
    mouse_window_quality: Dict[str, Dict[str, Any]],
) -> None:
    """Vérifie la cohérence des résultats par fenêtre."""

    assert len(mouse_window_features) == len(windows)
    assert len(mouse_window_quality) == len(windows)

    allowed_statuses = {
        "no_data",
        "insufficient_data",
        "collected",
    }

    for window in windows:

        window_id = window["window_id"]

        features = mouse_window_features[window_id]
        quality = mouse_window_quality[window_id]

        assert features["move_event_count"] == sum(
            event["type"] == "MOVE"
            for event in window["events"]
        )

        assert features["click_press_count"] == sum(
            event["type"] == "CLICK_PRESS"
            for event in window["events"]
        )

        assert features["click_release_count"] == sum(
            event["type"] == "CLICK_RELEASE"
            for event in window["events"]
        )

        assert features["scroll_count"] == sum(
            event["type"] == "SCROLL"
            for event in window["events"]
        )

        for modality in (
            "movement",
            "click",
            "scroll",
            "global",
        ):
            assert quality[modality] in allowed_statuses

    print("Toutes les vérifications par fenêtre sont réussies.")


# ==============================================================================
# 12. PIPELINE COMPLET DE SESSION
# ==============================================================================

def process_mouse_session(
    duration: float = CAPTURE_DURATION,
    window_duration: float = WINDOW_DURATION,
) -> Dict[str, Any]:
    """
    Pipeline complet :

    capture
       ↓
    validation
       ↓
    features globales
       ↓
    découpage en fenêtres
       ↓
    features par fenêtre
       ↓
    contrôle qualité

    Retourne les résultats globaux et par fenêtre.
    """

    # 1. Capture
    capture_result = capture_mouse_session(
        duration=duration,
        validate=True,
    )

    valid_events = capture_result["valid_events"]

    session_duration = capture_result["session_duration"]

    # 2. Features globales
    global_features = extract_mouse_session_features(
        valid_events,
        session_duration,
    )

    # 3. Fenêtres
    windows = build_mouse_windows(
        valid_events,
        session_duration,
        window_duration,
    )

    # 4. Appariement des clics
    (
        completed_clicks,
        incomplete_presses,
        unmatched_releases,
    ) = pair_mouse_clicks(valid_events)

    click_press_events = [
        event for event in valid_events
        if event["type"] == "CLICK_PRESS"
    ]

    clicks_by_window, intervals_by_window = (
        add_click_features_to_windows(
            windows,
            completed_clicks,
            click_press_events,
        )
    )

    # 5. Features par fenêtre
    mouse_window_features = build_mouse_window_features(
        windows,
        clicks_by_window,
        intervals_by_window,
    )

    # 6. Qualité
    mouse_window_quality = build_mouse_window_quality(
        windows,
        mouse_window_features,
        incomplete_presses,
        unmatched_releases,
    )

    # 7. Validation interne
    validate_window_features_and_quality(
        windows,
        mouse_window_features,
        mouse_window_quality,
    )

    return {
        "session_duration": session_duration,
        "events": capture_result["events"],
        "valid_events": valid_events,
        "invalid_events": capture_result["invalid_events"],
        "global_features": global_features,
        "windows": windows,
        "mouse_window_features": mouse_window_features,
        "mouse_window_quality": mouse_window_quality,
        "completed_clicks": completed_clicks,
        "incomplete_presses": incomplete_presses,
        "unmatched_releases": unmatched_releases,
    }
