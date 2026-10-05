"""Interfaz CLI — raiz de composicion de la aplicacion."""

import argparse
import json
import sys

from dotenv import load_dotenv

from ..application.analizar_nota import AnalizarNotaUseCase
from ..infrastructure.omniroute_client import OmnirouteLlmClient
from ..infrastructure.persistencia import ArchivoTexto, JsonFile, TextoDirecto


def construir_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Extrae informacion estructurada de una nota de texto libre."
    )
    parser.add_argument(
        "archivo",
        nargs="?",
        default="nota_sucia.txt",
        help="Archivo de texto a analizar (default: nota_sucia.txt)",
    )
    parser.add_argument("--texto", help="Texto a analizar (ignora el archivo)")
    parser.add_argument(
        "--salida",
        default="resultado_estructurado.json",
        help="Archivo JSON de salida (default: resultado_estructurado.json)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = construir_parser().parse_args(argv)

    try:
        load_dotenv()
        caso_uso = AnalizarNotaUseCase(OmnirouteLlmClient.desde_env())
        fuente = TextoDirecto(args.texto) if args.texto is not None else ArchivoTexto(args.archivo)
        destino = JsonFile(args.salida)

        resultado = caso_uso.ejecutar(fuente.leer())
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    print(json.dumps(resultado.model_dump(), indent=2, ensure_ascii=False))
    destino.guardar(resultado)
    print(f"\nResultado guardado en {args.salida}")
    return 0
