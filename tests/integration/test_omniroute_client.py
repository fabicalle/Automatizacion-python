"""Tests de integracion del cliente Omniroute con servidor HTTP simulado.

No requiere Omniroute corriendo: se levanta un servidor local que
imitan las respuestas SSE y JSON del endpoint real.
"""

import json
import os
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest import mock

from analizador.infrastructure.omniroute_client import (
    OmnirouteError,
    OmnirouteLlmClient,
)

MOCK_JSON = json.dumps(
    {
        "cliente": "Juan Pérez",
        "id_producto": "8841",
        "monto_reclamado": 45000.0,
        "motivo_reclamo": "El envío llegó con la caja rota",
        "prioridad": "Alta",
        "accion_solicitada": "Devolución o reemplazo urgente",
    },
    ensure_ascii=False,
)


class _MockOmnirouteHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        self.server.last_payload = json.loads(self.rfile.read(length))
        self.server.last_auth = self.headers.get("Authorization", "")

        if getattr(self.server, "fallar_conexion", False):
            self.close_connection = True
            return

        contenido = MOCK_JSON
        if self.server.contenido_raw is not None:
            contenido = self.server.contenido_raw
        if getattr(self.server, "wrap_markdown", False):
            contenido = f"```json\n{contenido}\n```"

        if getattr(self.server, "mode", "sse") == "json":
            cuerpo = json.dumps(
                {"choices": [{"message": {"content": contenido}}]},
                ensure_ascii=False,
            ).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(cuerpo)))
            self.end_headers()
            self.wfile.write(cuerpo)
            return

        if getattr(self.server, "status_code", 200) != 200:
            self.send_response(self.server.status_code)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"error":"upstream error"}')
            return

        chunks = [
            {"choices": [{"delta": {"role": "assistant"}}]},
            {"choices": [{"delta": {"content": contenido}}]},
            {"choices": [{"delta": {}, "finish_reason": "stop"}]},
        ]
        sse = "".join(f"data: {json.dumps(c, ensure_ascii=False)}\n\n" for c in chunks).encode(
            "utf-8"
        )
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Content-Length", str(len(sse)))
        self.end_headers()
        self.wfile.write(sse)

    def log_message(self, *args):
        pass


class TestOmnirouteLlmClient(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), _MockOmnirouteHandler)
        cls.server.mode = "sse"
        cls.server.wrap_markdown = False
        cls.server.contenido_raw = None
        cls.server.status_code = 200
        cls.server.fallar_conexion = False
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.cliente = OmnirouteLlmClient(
            url=f"http://127.0.0.1:{cls.server.server_address[1]}/v1/chat/completions",
            api_key="sk-test-local",
            model="auto",
            intentos=1,
        )

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def _reset(self):
        self.server.mode = "sse"
        self.server.wrap_markdown = False
        self.server.contenido_raw = None
        self.server.status_code = 200
        self.server.fallar_conexion = False

    def test_extrae_campos_desde_sse(self):
        self._reset()
        datos = self.cliente.extraer_estructurado("nota de prueba")
        self.assertEqual(datos["cliente"], "Juan Pérez")
        self.assertEqual(datos["monto_reclamado"], 45000.0)

    def test_extrae_campos_desde_json(self):
        self._reset()
        self.server.mode = "json"
        datos = self.cliente.extraer_estructurado("texto")
        self.assertEqual(datos["cliente"], "Juan Pérez")

    def test_limpia_delimitadores_markdown(self):
        self._reset()
        self.server.wrap_markdown = True
        datos = self.cliente.extraer_estructurado("texto")
        self.assertEqual(datos["cliente"], "Juan Pérez")

    def test_envia_payload_y_bearer_correctos(self):
        self._reset()
        self.cliente.extraer_estructurado("texto de la nota")
        self.assertEqual(self.server.last_payload["model"], "auto")
        self.assertEqual(
            self.server.last_payload["messages"][1]["content"],
            "texto de la nota",
        )
        self.assertEqual(self.server.last_auth, "Bearer sk-test-local")

    def test_error_estado_http(self):
        self._reset()
        self.server.status_code = 500
        with self.assertRaises(OmnirouteError):
            self.cliente.extraer_estructurado("texto")

    def test_error_json_invalido(self):
        self._reset()
        self.server.contenido_raw = "esto no es json"
        with self.assertRaises(OmnirouteError):
            self.cliente.extraer_estructurado("texto")

    def test_reintento_y_error_conexion(self):
        self._reset()
        self.server.fallar_conexion = True
        cliente = OmnirouteLlmClient(
            url=f"http://127.0.0.1:{self.server.server_address[1]}/v1/chat/completions",
            api_key="sk-test-local",
            model="auto",
            intentos=2,
        )
        with self.assertRaises(OmnirouteError):
            cliente.extraer_estructurado("texto")

    def test_desde_env_requiere_api_key(self):
        self._reset()
        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(EnvironmentError):
                OmnirouteLlmClient.desde_env()


if __name__ == "__main__":
    unittest.main()
