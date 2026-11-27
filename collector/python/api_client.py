"""
Module de communication avec l'API Backend.

Responsabilités :
- Configurer la connexion HTTP (URL, endpoints, clé API, timeout).
- Vérifier la disponibilité du Backend.
- Envoyer le payload JSON d'une fenêtre (avec réessais limités).
- Envoyer tous les payloads d'une session.
- Interpréter les réponses HTTP et remonter les erreurs de communication.

Ce module ne contient AUCUNE logique de capture ni de calcul de features.
Il n'invente ni URL ni format d'endpoint : tout est configurable, en
attendant le contrat définitif avec le Backend.

Deux formats d'envoi (payload_format) :
- "window_json" (défaut) : envoie directement l'objet JSON métier
  (schema_version, user_id, session_id, window_id "w0000", features...).
- "envelope" : envoie l'enveloppe produite par windows.py
  {"window_id": 0, "json": "<JSON métier sous forme de chaîne>"}.

Confidentialité : le contenu des payloads n'est jamais écrit dans les logs
ni dans les messages d'erreur (données comportementales). Le corps des
réponses d'erreur HTTP n'est PAS inclus dans les exceptions.

Idempotence : les réessais automatiques sur un POST ne garantissent pas
une livraison "exactement une fois". Si le Backend accepte un en-tête
d'idempotence (ex. "Idempotency-Key"), il peut être transmis via
extra_headers, ou intégré au contrat après confirmation avec le
responsable Backend (clé basée sur session_id + window_id).

Dépendances : bibliothèque standard uniquement (urllib).
"""

import json
import logging
import math
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)


# ==============================================================================
# CONSTANTES
# ==============================================================================

PAYLOAD_FORMAT_WINDOW_JSON = "window_json"
PAYLOAD_FORMAT_ENVELOPE = "envelope"
VALID_PAYLOAD_FORMATS = (PAYLOAD_FORMAT_WINDOW_JSON, PAYLOAD_FORMAT_ENVELOPE)

DEFAULT_TIMEOUT: float = 10.0
DEFAULT_MAX_RETRIES: int = 2
DEFAULT_BACKOFF_SECONDS: float = 0.5

# Codes HTTP pour lesquels un nouvel essai a un sens
RETRYABLE_STATUS_CODES = frozenset({408, 429, 500, 502, 503, 504})

# Hôtes locaux autorisés en HTTP non chiffré
LOCAL_HOSTS = frozenset({"localhost", "127.0.0.1", "::1"})

# Taille maximale du corps de réponse conservé (caractères)
MAX_RESPONSE_CHARS = 2000


# ==============================================================================
# TYPES
# ==============================================================================

class APIError(Exception):
    """Erreur liée à la communication avec l'API."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        retryable: bool = False,
        attempts: int = 0,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.retryable = retryable
        self.attempts = attempts


@dataclass
class SendResult:
    """Résultat d'envoi d'une fenêtre."""

    ok: bool
    window_id: Any
    status_code: Optional[int] = None
    attempts: int = 0
    response: Any = None
    error: Optional[str] = None


# ==============================================================================
# CLIENT
# ==============================================================================

class APIClient:
    """Client HTTP configurable pour le Backend."""

    def __init__(
        self,
        base_url: str,
        window_endpoint: str,
        health_endpoint: Optional[str] = None,
        api_key: Optional[str] = None,
        api_key_header: str = "X-API-Key",
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        backoff_seconds: float = DEFAULT_BACKOFF_SECONDS,
        payload_format: str = PAYLOAD_FORMAT_WINDOW_JSON,
        extra_headers: Optional[Dict[str, str]] = None,
    ) -> None:
        parsed = urlparse(base_url or "")
        if parsed.scheme not in ("http", "https") or not parsed.hostname:
            raise ValueError(
                "base_url doit commencer par http:// ou https:// "
                "et contenir un hôte."
            )
        if parsed.scheme == "http" and parsed.hostname not in LOCAL_HOSTS:
            logger.warning(
                "Connexion HTTP non chiffrée vers un hôte distant : "
                "utiliser HTTPS pour des données comportementales."
            )
        if not window_endpoint or not isinstance(window_endpoint, str):
            raise ValueError("window_endpoint est obligatoire.")
        if payload_format not in VALID_PAYLOAD_FORMATS:
            raise ValueError(
                f"payload_format doit être l'un de {VALID_PAYLOAD_FORMATS}."
            )
        if (
            isinstance(timeout, bool)
            or not isinstance(timeout, (int, float))
            or not math.isfinite(timeout)
            or timeout <= 0
        ):
            raise ValueError("timeout doit être un nombre fini positif.")
        if (
            isinstance(max_retries, bool)
            or not isinstance(max_retries, int)
            or max_retries < 0
        ):
            raise ValueError("max_retries doit être un entier >= 0.")
        if (
            isinstance(backoff_seconds, bool)
            or not isinstance(backoff_seconds, (int, float))
            or not math.isfinite(backoff_seconds)
            or backoff_seconds < 0
        ):
            raise ValueError("backoff_seconds doit être un nombre >= 0.")

        # Validation des en-têtes (prévention de l'injection CRLF)
        if not isinstance(api_key_header, str) or not api_key_header:
            raise ValueError("api_key_header doit être une chaîne non vide.")
        self._validate_header_name(api_key_header)

        if api_key is not None:
            if not isinstance(api_key, str) or not api_key:
                raise ValueError("api_key doit être une chaîne non vide.")
            self._validate_header_value(api_key)

        if extra_headers is not None:
            if not isinstance(extra_headers, dict):
                raise ValueError("extra_headers doit être un dictionnaire.")
            for key, value in extra_headers.items():
                if not isinstance(key, str) or not isinstance(value, str):
                    raise ValueError(
                        "Les clés et valeurs de extra_headers doivent "
                        "être des chaînes."
                    )
                self._validate_header_name(key)
                self._validate_header_value(value)

        self.base_url = base_url.rstrip("/")
        self.window_endpoint = window_endpoint
        self.health_endpoint = health_endpoint
        self.api_key = api_key
        self.api_key_header = api_key_header
        self.timeout = float(timeout)
        self.max_retries = max_retries
        self.backoff_seconds = float(backoff_seconds)
        self.payload_format = payload_format
        self.extra_headers = dict(extra_headers or {})

    # --------------------------------------------------------------------------
    # Validation des en-têtes
    # --------------------------------------------------------------------------

    @staticmethod
    def _validate_header_name(name: str) -> None:
        """Refuse les noms d'en-tête vides ou contenant CR/LF."""
        if "\r" in name or "\n" in name:
            raise ValueError(
                "Un nom d'en-tête ne doit pas contenir CR ou LF."
            )

    @staticmethod
    def _validate_header_value(value: str) -> None:
        """Refuse les valeurs d'en-tête contenant CR/LF."""
        if "\r" in value or "\n" in value:
            raise ValueError(
                "Une valeur d'en-tête ne doit pas contenir CR ou LF."
            )

    # --------------------------------------------------------------------------
    # Outils internes
    # --------------------------------------------------------------------------

    def _build_url(self, endpoint: str) -> str:
        return f"{self.base_url}/{endpoint.lstrip('/')}"

    def _headers(self, has_body: bool) -> Dict[str, str]:
        headers = {"Accept": "application/json"}
        if has_body:
            headers["Content-Type"] = "application/json; charset=utf-8"
        if self.api_key:
            headers[self.api_key_header] = self.api_key
        headers.update(self.extra_headers)
        return headers

    @staticmethod
    def _parse_body(raw: bytes) -> Any:
        """Décode une réponse : JSON si possible, sinon texte tronqué."""
        text = raw.decode("utf-8", errors="replace").strip()
        if not text:
            return None
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return text[:MAX_RESPONSE_CHARS]

    @staticmethod
    def _reject_json_constant(value: str) -> None:
        raise ValueError("Constante numérique JSON non autorisée.")

    def _request(
        self,
        method: str,
        url: str,
        body: Optional[bytes] = None,
    ) -> Any:
        """
        Exécute UNE requête HTTP (sans réessai).

        Returns:
            (status_code, réponse décodée)

        Raises:
            APIError: statut HTTP >= 400 ou erreur réseau.
            Le message d'erreur ne contient NI le corps de la réponse
            NI le détail technique de l'erreur réseau (confidentialité).
        """
        request = Request(
            url,
            data=body,
            headers=self._headers(body is not None),
            method=method,
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                raw = response.read(MAX_RESPONSE_CHARS + 1)
                if len(raw) > MAX_RESPONSE_CHARS:
                    return response.status, {
                        "truncated": True,
                        "text": raw[:MAX_RESPONSE_CHARS].decode(
                            "utf-8", errors="replace"
                        ),
                    }
                return response.status, self._parse_body(raw)
        except HTTPError as exc:
            status = exc.code
            exc.close()
            raise APIError(
                f"Le Backend a répondu HTTP {status}.",
                status_code=status,
                retryable=status in RETRYABLE_STATUS_CODES,
            ) from exc
        except (URLError, TimeoutError, ConnectionError, OSError) as exc:
            raise APIError(
                "Backend injoignable ou délai de connexion dépassé.",
                retryable=True,
            ) from exc

    def _prepare_body(self, payload: Dict[str, Any]) -> bytes:
        """Construit le corps JSON selon payload_format."""
        if (
            not isinstance(payload, dict)
            or "window_id" not in payload
            or "json" not in payload
        ):
            raise ValueError(
                "Le payload doit contenir les champs window_id et json."
            )

        if self.payload_format == PAYLOAD_FORMAT_ENVELOPE:
            data = payload
        else:
            if not isinstance(payload["json"], str):
                raise ValueError("Le champ json doit être une chaîne.")
            try:
                data = json.loads(
                    payload["json"],
                    parse_constant=self._reject_json_constant,
                )
            except (TypeError, json.JSONDecodeError, ValueError) as exc:
                raise ValueError(
                    "Le champ json ne contient pas un JSON valide."
                ) from exc
            if not isinstance(data, dict):
                raise ValueError(
                    "Le JSON métier doit représenter un objet."
                )

        return json.dumps(
            data,
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")

    # --------------------------------------------------------------------------
    # API publique
    # --------------------------------------------------------------------------

    def check_health(self) -> bool:
        """
        Vérifie la disponibilité du Backend.

        Returns:
            True si le endpoint de santé répond avec un code 2xx,
            False sinon (ne lève jamais d'exception réseau).

        Raises:
            ValueError: si health_endpoint n'est pas configuré.
        """
        if not self.health_endpoint:
            raise ValueError("health_endpoint n'est pas configuré.")
        try:
            status, _ = self._request(
                "GET", self._build_url(self.health_endpoint)
            )
        except APIError as exc:
            logger.info("Health check échoué : %s", exc)
            return False
        return 200 <= status < 300

    def send_window(self, payload: Dict[str, Any]) -> SendResult:
        """
        Envoie le payload d'une fenêtre, avec réessais limités.

        Réessais (backoff exponentiel) uniquement pour les erreurs réseau,
        les timeouts et les codes 408/429/5xx. Un code 4xx (contrat non
        respecté) n'est jamais réessayé.

        Attention : un POST peut avoir été traité par le Backend même si
        la réponse s'est perdue ; le réessai peut donc créer un doublon.
        L'idempotence (ex. en-tête "Idempotency-Key") doit être confirmée
        avec le Backend.

        Raises:
            ValueError: payload mal formé (jamais envoyé).
            APIError: échec définitif de communication.
        """
        body = self._prepare_body(payload)
        url = self._build_url(self.window_endpoint)
        window_id = payload["window_id"]

        last_error: Optional[APIError] = None
        total_attempts = self.max_retries + 1
        attempt = 0

        for attempt in range(1, total_attempts + 1):
            try:
                status, response = self._request("POST", url, body)
                return SendResult(
                    ok=True,
                    window_id=window_id,
                    status_code=status,
                    attempts=attempt,
                    response=response,
                )
            except APIError as exc:
                last_error = exc
                if not exc.retryable or attempt == total_attempts:
                    break
                delay = self.backoff_seconds * (2 ** (attempt - 1))
                logger.info(
                    "Envoi fenêtre %s : échec (essai %d/%d), nouvel essai "
                    "dans %.1fs.", window_id, attempt, total_attempts, delay,
                )
                time.sleep(delay)

        assert last_error is not None
        raise APIError(
            f"Échec d'envoi de la fenêtre {window_id} après "
            f"{attempt} essai(s) : {last_error}",
            status_code=last_error.status_code,
            retryable=last_error.retryable,
            attempts=attempt,
        ) from last_error

    def send_payloads(
        self,
        payloads: List[Dict[str, Any]],
        stop_on_error: bool = False,
    ) -> List[SendResult]:
        """
        Envoie une liste de payloads, dans l'ordre.

        Une erreur de communication n'interrompt pas l'envoi des suivants
        (sauf stop_on_error=True). Chaque résultat indique ok/erreur, ce qui
        permet à l'appelant de conserver les fenêtres non envoyées.

        Note : avec stop_on_error=True, les fenêtres situées après la
        première erreur ne sont PAS tentées et n'apparaissent pas dans la
        liste des résultats.
        """
        if not isinstance(payloads, list):
            raise ValueError("payloads doit être une liste.")
        results: List[SendResult] = []
        for payload in payloads:
            window_id = (
                payload.get("window_id")
                if isinstance(payload, dict)
                else None
            )
            try:
                result = self.send_window(payload)
                results.append(result)
            except (APIError, ValueError) as exc:
                results.append(
                    SendResult(
                        ok=False,
                        window_id=window_id,
                        status_code=getattr(exc, "status_code", None),
                        attempts=getattr(exc, "attempts", 0),
                        error=str(exc),
                    )
                )
                if stop_on_error:
                    break
        return results

    def send_session_result(
        self,
        session_result: Dict[str, Any],
        stop_on_error: bool = False,
    ) -> List[SendResult]:
        """
        Envoie les payloads du dictionnaire retourné par run_session().

        Raises:
            ValueError: si la session n'a pas été finalisée.
        """
        if not session_result.get("finalized", False):
            raise ValueError(
                "Session non finalisée : aucun payload à envoyer."
            )
        return self.send_payloads(
            session_result.get("payloads", []),
            stop_on_error=stop_on_error,
        )