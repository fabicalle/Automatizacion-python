"""Tests unitarios de la interfaz CLI."""

import unittest

from analizador.interface.cli import construir_parser


class TestCliParser(unittest.TestCase):
    def test_valores_por_defecto(self):
        args = construir_parser().parse_args([])
        self.assertEqual(args.archivo, "nota_sucia.txt")
        self.assertIsNone(args.texto)
        self.assertEqual(args.salida, "resultado_estructurado.json")

    def test_argumentos_explícitos(self):
        args = construir_parser().parse_args(
            ["nota.txt", "--texto", "hola", "--salida", "out.json"]
        )
        self.assertEqual(args.archivo, "nota.txt")
        self.assertEqual(args.texto, "hola")
        self.assertEqual(args.salida, "out.json")


if __name__ == "__main__":
    unittest.main()
