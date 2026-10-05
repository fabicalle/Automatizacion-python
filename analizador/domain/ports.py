"""Puertos (interfaces) del dominio.

El dominio define los contratos; la infraestructura los implementa.
Las capas superiores dependen de estas abstracciones, nunca al reves.
"""

from abc import ABC, abstractmethod

from .schema import AnalisisResultado


class LlmClient(ABC):
    """Contrato de un cliente LLM que extrae estructura de texto libre."""

    @abstractmethod
    def extraer_estructurado(self, texto: str) -> dict:
        """Devuelve los campos del analisis como diccionario."""
        raise NotImplementedError


class FuenteTexto(ABC):
    """Contrato de una fuente de texto a analizar."""

    @abstractmethod
    def leer(self) -> str:
        """Devuelve el texto completo a analizar."""
        raise NotImplementedError


class DestinoResultado(ABC):
    """Contrato de un destino para el resultado estructurado."""

    @abstractmethod
    def guardar(self, resultado: AnalisisResultado) -> None:
        """Persiste el resultado."""
        raise NotImplementedError
