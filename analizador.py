"""analizador.py — Extrae información estructurada de notas de texto libre.

Lee un archivo de texto (o texto pasado por CLI), lo envia a un endpoint
compatible con OpenAI (Omniroute local) pidiendo JSON estricto, valida la
respuesta con Pydantic y guarda el resultado en un archivo JSON.
"""
import argparse
import json
import os
import sys

import requests
from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()

# ---------------------------------------------------------
# 1. Configuracion de Omniroute
# ---------------------------------------------------------
OMNIROUTE_URL = os.getenv(
    "OMNIROUTE_URL", "http://localhost:20128/v1/chat/completions"
)
MODEL_NAME = os.getenv("OMNIROUTE_MODEL", "auto")  # "auto" = combo routing de Omniroute


# ---------------------------------------------------------
# 2. Esquema de datos esperado (validacion con Pydantic)
# ---------------------------------------------------------
class AnalisisResultado(BaseModel):
    cliente: str = Field(description="Nombre del cliente")
    id_producto: str = Field(description="ID o codigo del producto")
    monto_reclamado: float = Field(default=0.0, description="Monto involucrado; 0 si no se menciona")
    motivo_reclamo: str = Field(description="Resumen breve del problema")
    prioridad: str = Field(description="Alta, Media o Baja")
    accion_solicitada: str = Field(description="Que pide el cliente")


SYSTEM_PROMPT = (
    "Eres un extractor de informacion experto. Analiza el siguiente texto "
    "desestructurado y responde UNICAMENTE con un objeto JSON valido con la "
    "siguiente estructura:\n"
    "{\n"
    '  "cliente": "string",\n'
    '  "id_producto": "string",\n'
    '  "monto_reclamado": float,\n'
    '  "motivo_reclamo": "string",\n'
    '  "prioridad": "Alta" | "Media" | "Baja",\n'
    '  "accion_solicitada": "string"\n'
    "}\n"
    "No incluyas formateo Markdown como ```json ni explicaciones adicionales. "
    "Nota: los montos usan formato latinoamericano donde el punto es "
    "separador de miles (ej: $45.000 = 45000). Devuelve el numero sin "
    "separadores ni simbolos."
)


def _extraer_contenido(response: requests.Response) -> str:
    """Omniroute puede responder JSON normal o SSE (text/event-stream) con
    chunks "data: {...}". Devuelve el texto completo del asistente."""
    if "text/event-stream" in response.headers.get("Content-Type", ""):
        # Decodificar desde bytes: text/event-stream sin charset hace que
        # requests asuma ISO-8859-1 y corrompa los acentos.
        contenido = ""
        for linea in response.content.decode("utf-8").splitlines():
            linea = linea.strip()
            if not linea.startswith("data:"):
                continue
            datos = linea[len("data:"):].strip()
            if not datos or datos == "[DONE]":
                continue
            delta = json.loads(datos).get("choices", [{}])[0].get("delta", {})
            contenido += delta.get("content", "") or ""
        return contenido
    return response.json()["choices"][0]["message"]["content"]


def analizar_texto(texto: str) -> AnalisisResultado:
    """Envía texto libre a Omniroute y devuelve el resultado validado."""
    api_key = os.getenv("OMNI_API_KEY")
    if not api_key:
        raise EnvironmentError("OMNI_API_KEY no esta definida en .env")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": texto},
        ],
        "temperature": 0.1,  # Baja temperatura para consistencia estructurada
    }

    print(f"Enviando peticion a Omniroute (modelo: {MODEL_NAME})...")
    try:
        response = requests.post(OMNIROUTE_URL, headers=headers, json=payload, timeout=120)
    except requests.exceptions.ConnectionError:
        raise ConnectionError(
            f"No se pudo conectar a Omniroute en {OMNIROUTE_URL}. "
            "Verifica que el servidor este corriendo (omniroute serve)."
        ) from None

    if response.status_code != 200:
        raise RuntimeError(
            f"Error en la API de Omniroute [{response.status_code}]: {response.text}"
        )

    respuesta_raw = _extraer_contenido(response)
    # Limpiar posibles delimitadores Markdown si el modelo los devuelve
    respuesta_limpia = respuesta_raw.replace("```json", "").replace("```", "").strip()
    return AnalisisResultado(**json.loads(respuesta_limpia))


def analizar_archivo(ruta_archivo: str) -> AnalisisResultado:
    if not os.path.exists(ruta_archivo):
        raise FileNotFoundError(f"El archivo {ruta_archivo} no existe.")
    with open(ruta_archivo, "r", encoding="utf-8") as f:
        return analizar_texto(f.read())


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Extrae informacion estructurada de una nota de texto libre."
    )
    parser.add_argument(
        "archivo", nargs="?", default="nota_sucia.txt",
        help="Archivo de texto a analizar (default: nota_sucia.txt)",
    )
    parser.add_argument("--texto", help="Texto a analizar (ignora el archivo)")
    parser.add_argument(
        "--salida", default="resultado_estructurado.json",
        help="Archivo JSON de salida (default: resultado_estructurado.json)",
    )
    args = parser.parse_args(argv)

    try:
        if args.texto is not None:
            resultado = analizar_texto(args.texto)
        else:
            resultado = analizar_archivo(args.archivo)
    except Exception as e:
        print(f"\nError durante el procesamiento: {e}", file=sys.stderr)
        return 1

    print("\n--- Analisis estructurado exitoso ---")
    print(json.dumps(resultado.model_dump(), indent=2, ensure_ascii=False))

    with open(args.salida, "w", encoding="utf-8") as f_out:
        json.dump(resultado.model_dump(), f_out, indent=2, ensure_ascii=False)
    print(f"\nResultado guardado en {args.salida}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
