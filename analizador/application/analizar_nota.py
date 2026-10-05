"""Casos de uso de la aplicacion."""

from ..domain.ports import LlmClient
from ..domain.schema import AnalisisResultado


class AnalizarNotaUseCase:
    """Orquesta la extraccion: texto libre -> LLM -> entidad validada.

    Depende solo del puerto LlmClient, no de la infraestructura.
    """

    def __init__(self, llm_client: LlmClient) -> None:
        self._llm_client = llm_client

    def ejecutar(self, texto: str) -> AnalisisResultado:
        """Analiza un texto y devuelve el resultado validado por Pydantic."""
        datos = self._llm_client.extraer_estructurado(texto)
        return AnalisisResultado(**datos)
