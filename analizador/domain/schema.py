"""Entidades del dominio."""

from pydantic import BaseModel, Field, field_validator


class AnalisisResultado(BaseModel):
    """Resultado estructurado extraido de una nota de texto libre."""

    cliente: str = Field(description="Nombre del cliente")
    id_producto: str = Field(description="ID o codigo del producto")
    monto_reclamado: float = Field(
        default=0.0, description="Monto involucrado; 0 si no se menciona"
    )
    motivo_reclamo: str = Field(description="Resumen breve del problema")
    prioridad: str = Field(description="Alta, Media o Baja")
    accion_solicitada: str = Field(description="Que pide el cliente")

    @field_validator("prioridad")
    @classmethod
    def validar_prioridad(cls, valor: str) -> str:
        """Regla de negocio: la prioridad se normaliza a Alta/Media/Baja."""
        normalizada = valor.strip().capitalize()
        if normalizada not in {"Alta", "Media", "Baja"}:
            raise ValueError(f"prioridad debe ser Alta, Media o Baja (recibido: {valor!r})")
        return normalizada
