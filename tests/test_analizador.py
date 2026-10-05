"""Pruebas de analizador.py con un servidor Omniroute simulado.

No requiere Omniroute corriendo: se levanta un servidor HTTP local que
imitan las respuestas SSE del endpoint real.

Ejecutar:  python -m unittest discover -s tests
"""
import json
import os
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import analizador

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

        contenido = MOCK_JSON
        if getattr(self.server, "wrap_markdown", False):
            contenido = f"```json\n{MOCK_JSON}\n```"

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

        chunks = [
            {"choices": [{"delta": {"role": "assistant"}}]},
            {"choices": [{"delta": {"content": contenido}}]},
            {"choices": [{"delta": {}, "finish_reason": "stop"}]},
        ]
        sse = "".join(
            f"data: {json.dumps(c, ensure_ascii=False)}\n\n" for c in chunks
        ).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Content-Length", str(len(sse)))
        self.end_headers()
        self.wfile.write(sse)

    def log_message(self, *args):
        pass


class TestAnalizadorConMock(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ["OMNI_API_KEY"] = "sk-test-local"
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), _MockOmnirouteHandler)
        cls.server.mode = "sse"
        cls.server.wrap_markdown = False
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls._url_original = analizador.OMNIROUTE_URL
        analizador.OMNIROUTE_URL = f"http://127.0.0.1:{cls.server.server_address[1]}/v1/chat/completions"

    @classmethod
    def tearDownClass(cls):
        analizador.OMNIROUTE_URL = cls._url_original
        cls.server.shutdown()
        cls.server.server_close()

    def test_valida_todos_los_campos(self):
        resultado = analizador.analizar_texto("nota de prueba")
        self.assertEqual(resultado.cliente, "Juan Pérez")
        self.assertEqual(resultado.id_producto, "8841")
        self.assertEqual(resultado.monto_reclamado, 45000.0)
        self.assertEqual(resultado.motivo_reclamo, "El envío llegó con la caja rota")
        self.assertEqual(resultado.prioridad, "Alta")
        self.assertEqual(resultado.accion_solicitada, "Devolución o reemplazo urgente")

    def test_envia_payload_y_bearer_correctos(self):
        analizador.analizar_texto("texto de la nota")
        self.assertEqual(self.server.last_payload["model"], analizador.MODEL_NAME)
        self.assertEqual(
            self.server.last_payload["messages"][1]["content"], "texto de la nota"
        )
        self.assertEqual(self.server.last_auth, "Bearer sk-test-local")

    def test_parsea_respuesta_json_normal(self):
        self.server.mode = "json"
        resultado = analizador.analizar_texto("texto")
        self.assertEqual(resultado.cliente, "Juan Pérez")

    def test_limpia_delimitadores_markdown(self):
        self.server.wrap_markdown = True
        resultado = analizador.analizar_texto("texto")
        self.assertEqual(resultado.cliente, "Juan Pérez")

    def test_rechaza_texto_invalido(self):
        # Pydantic debe rechazar JSON que no tenga los campos requeridos
        with self.assertRaises(Exception):
            analizador.AnalisisResultado(**{"cliente": "solo un campo"})


if __name__ == "__main__":
    unittest.main()
