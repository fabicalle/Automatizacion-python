"""analizador — Extraccion estructurada de texto libre via LLM.

Arquitectura limpia:
    domain/         Entidades y puertos (sin dependencias externas)
    application/    Casos de uso (orquestacion)
    infrastructure/ Adaptadores (HTTP, archivos)
    interface/      CLI (raiz de composicion)
"""

__version__ = "0.1.0"
