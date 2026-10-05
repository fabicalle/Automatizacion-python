"""Tests unitarios del dominio."""

import unittest

from pydantic import ValidationError

from analizador.domain.schema import AnalisisResultado


class TestAnalisisResultado(unittest.TestCase):
    DATOS = {
        "cliente": "Juan Pérez",
        "id_producto": "8841",
        "monto_reclamado": 45000.0,
        "motivo_reclamo": "Caja rota",
        "prioridad": "Alta",
        "accion_solicitada": "Reemplazo",
    }

    def test_creacion_completa(self):
        resultado = AnalisisResultado(**self.DATOS)
        self.assertEqual(resultado.cliente, "Juan Pérez")
        self.assertEqual(resultado.monto_reclamado, 45000.0)

    def test_monto_por_defecto(self):
        datos = {**self.DATOS, "monto_reclamado": 0.0}
        self.assertEqual(AnalisisResultado(**datos).monto_reclamado, 0.0)

    def test_prioridad_se_normaliza(self):
        for cruda, esperada in [
            ("ALTA", "Alta"),
            (" media ", "Media"),
            ("baja", "Baja"),
        ]:
            datos = {**self.DATOS, "prioridad": cruda}
            self.assertEqual(AnalisisResultado(**datos).prioridad, esperada)

    def test_prioridad_invalida_rechazada(self):
        datos = {**self.DATOS, "prioridad": "Urgente"}
        with self.assertRaises(ValidationError):
            AnalisisResultado(**datos)

    def test_campos_requeridos(self):
        with self.assertRaises(ValidationError):
            AnalisisResultado(**{"cliente": "solo un campo"})


if __name__ == "__main__":
    unittest.main()
