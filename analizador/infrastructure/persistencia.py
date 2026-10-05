"""Adaptadores de persistencia: fuentes de texto y destino JSON."""

import json
import os

from ..domain.ports import DestinoResultado, FuenteTexto
from ..domain.schema import AnalisisResultado


class ArchivoTexto(FuenteTexto):
    """Lee el texto a analizar desde un archivo UTF-8."""

    def __init__(self, ruta: str) -> None:
        self._ruta = ruta

    def leer(self) -> str:
        if not os.path.exists(self._ruta):
            raise FileNotFoundError(f"El archivo {self._ruta} no existe.")
        with open(self._ruta, encoding="utf-8") as f:
            return f.read()


class TextoDirecto(FuenteTexto):
    """Envuelve un texto ya cargado en memoria."""

    def __init__(self, texto: str) -> None:
        self._texto = texto

    def leer(self) -> str:
        return self._texto


class JsonFile(DestinoResultado):
    """Persiste el resultado como JSON UTF-8 indentado."""

    def __init__(self, ruta: str) -> None:
        self._ruta = ruta

    def guardar(self, resultado: AnalisisResultado) -> None:
        with open(self._ruta, "w", encoding="utf-8") as f:
            json.dump(resultado.model_dump(), f, indent=2, ensure_ascii=False)
            f.write("\n")
