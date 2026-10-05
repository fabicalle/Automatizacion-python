"""Tests unitarios del caso de uso (con fake del puerto LlmClient)."""

import unittest

from pydantic import ValidationError

from analizador.application.analizar_nota import AnalizarNotaUseCase
from analizador.domain.ports import LlmClient


class FakeLlmClient(LlmClient):
    """Double de prueba: devuelve un dict fijo y registra el texto."""

    def __init__(self, datos: dict) -> None:
        self._datos = datos
        self.ultimo_texto: str | None = None

    def extraer_estructurado(self, texto: str) -> dict:
        self.ultimo_texto = texto
        return self._datos


DATOS_VALIDOS = {
    "cliente": "Juan Pérez",
    "id_producto": "8841",
    "monto_reclamado": 45000.0,
    "motivo_reclamo": "Caja rota",
    "prioridad": "Alta",
    "accion_solicitada": "Reemplazo",
}


class TestAnalizarNotaUseCase(unittest.TestCase):
    def test_orquesta_y_valida(self):
        caso_uso = AnalizarNotaUseCase(FakeLlmClient(DATOS_VALIDOS))
        resultado = caso_uso.ejecutar("texto de prueba")
        self.assertEqual(resultado.cliente, "Juan Pérez")

    def test_pasa_el_texto_al_cliente(self):
        fake = FakeLlmClient(DATOS_VALIDOS)
        caso_uso = AnalizarNotaUseCase(fake)
        caso_uso.ejecutar("nota del cliente")
        self.assertEqual(fake.ultimo_texto, "nota del cliente")

    def test_rechaza_datos_invalidos_del_llm(self):
        caso_uso = AnalizarNotaUseCase(FakeLlmClient({"cliente": "incompleto"}))
        with self.assertRaises(ValidationError):
            caso_uso.ejecutar("texto")


if __name__ == "__main__":
    unittest.main()
