"""Adaptador de infraestructura: cliente HTTP para Omniroute.

Implementa el puerto LlmClient hablando con un endpoint
compatible con OpenAI (/v1/chat/completions). Soporta respuestas
JSON y SSE (text/event-stream) con decodificacion UTF-8 explicita.
"""

import json
import os
import time

import requests

from ..domain.ports import LlmClient

DEFAULT_URL = "http://localhost:20128/v1/chat/completions"
DEFAULT_MODEL = "auto"
DEFAULT_TIMEOUT = 120.0
DEFAULT_INTENTOS = 2
REINTENTO_ESPERA = 1.5

SYSTEM_PROMPT = (
    "Eres un extractor de informacion experto. Analiza el siguiente texto "
    "desestructurado y responde UNICAMENTE con un objeto JSON valido con la "
    "siguiente estructura:\n"
    "{\n"
    '  "cliente": "string",\n'
    '  "id_producto": "string",\n'
    '  "monto_reclamado": float,\n'
    '  "motivo_reclamo": "string",\n'
    '  "prioridad": "Alta" | "Media" | "Baja",\n'
    '  "accion_solicitada": "string"\n'
    "}\n"
    "No incluyas formateo Markdown como ```json ni explicaciones adicionales. "
    "Nota: los montos usan formato latinoamericano donde el punto es "
    "separador de miles (ej: $45.000 = 45000). Devuelve el numero sin "
    "separadores ni simbolos."
)


class OmnirouteError(RuntimeError):
    """Error de comunicacion o de respuesta del servidor Omniroute."""


class OmnirouteLlmClient(LlmClient):
    """Cliente LLM contra un servidor Omniroute local."""

    def __init__(
        self,
        url: str,
        api_key: str,
        model: str,
        timeout: float = DEFAULT_TIMEOUT,
        intentos: int = DEFAULT_INTENTOS,
    ) -> None:
        self._url = url
        self._api_key = api_key
        self._model = model
        self._timeout = timeout
        self._intentos = max(1, intentos)

    @classmethod
    def desde_env(cls) -> "OmnirouteLlmClient":
        """Construye el cliente desde variables de entorno / .env."""
        api_key = os.getenv("OMNI_API_KEY")
        if not api_key:
            raise OSError("OMNI_API_KEY no esta definida en .env")
        return cls(
            url=os.getenv("OMNIROUTE_URL", DEFAULT_URL),
            api_key=api_key,
            model=os.getenv("OMNIROUTE_MODEL", DEFAULT_MODEL),
            timeout=float(os.getenv("OMNIROUTE_TIMEOUT", str(DEFAULT_TIMEOUT))),
        )

    def extraer_estructurado(self, texto: str) -> dict:
        """Envía el texto y devuelve el JSON extraido como dict."""
        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": texto},
            ],
            "temperature": 0.1,
        }
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        respuesta = self._enviar(payload, headers)

        if respuesta.status_code != 200:
            raise OmnirouteError(
                f"Error en la API de Omniroute [{respuesta.status_code}]: {respuesta.text[:500]}"
            )

        contenido = self._extraer_contenido(respuesta)
        limpio = contenido.replace("```json", "").replace("```", "").strip()
        try:
            datos: dict = json.loads(limpio)
        except json.JSONDecodeError as e:
            raise OmnirouteError(f"El modelo no devolvio JSON valido: {limpio[:300]}") from e
        return datos

    def _enviar(self, payload: dict, headers: dict) -> requests.Response:
        """POST con reintentos ante fallos de conexion."""
        ultimo_error: Exception | None = None
        for _ in range(self._intentos):
            try:
                return requests.post(
                    self._url,
                    headers=headers,
                    json=payload,
                    timeout=self._timeout,
                )
            except requests.exceptions.ConnectionError as e:
                ultimo_error = e
                time.sleep(REINTENTO_ESPERA)
        raise OmnirouteError(
            f"No se pudo conectar a Omniroute en {self._url}. "
            "Verifica que el servidor este corriendo (omniroute serve)."
        ) from ultimo_error

    @staticmethod
    def _extraer_contenido(respuesta: requests.Response) -> str:
        """Omniroute responde JSON normal o SSE con chunks "data: {...}"."""
        if "text/event-stream" not in respuesta.headers.get("Content-Type", ""):
            contenido: str = respuesta.json()["choices"][0]["message"]["content"]
            return contenido
        # Decodificar desde bytes: text/event-stream sin charset hace que
        # requests asuma ISO-8859-1 y corrompa los acentos.
        contenido = ""
        for linea in respuesta.content.decode("utf-8").splitlines():
            linea = linea.strip()
            if not linea.startswith("data:"):
                continue
            datos = linea[len("data:") :].strip()
            if not datos or datos == "[DONE]":
                continue
            delta = json.loads(datos).get("choices", [{}])[0].get("delta", {})
            contenido += delta.get("content", "") or ""
        return contenido
