# Analizador de Notas — Extracción estructurada con LLM

Mini proyecto en Python que toma una nota de texto libre (por ejemplo, una
queja de cliente desestructurada), la envía a un endpoint local
[Omniroute](https://www.npmjs.com/package/omniroute) compatible con OpenAI
pidiendo **JSON estricto**, valida la respuesta con **Pydantic** y guarda
el resultado en un archivo JSON.

## Demo

Entrada (`nota_sucia.txt`):

> El cliente Juan Pérez llamó el 12 de Octubre molesto porque el envío del
> producto #8841 (Teclado Mecánico) llegó con la caja rota. Quiere la
> devolución de sus $45.000 o un reemplazo urgente. Prioridad alta.

Salida (`resultado_estructurado.json`):

```json
{
  "cliente": "Juan Pérez",
  "id_producto": "8841",
  "monto_reclamado": 45000.0,
  "motivo_reclamo": "El envío llegó con la caja rota",
  "prioridad": "Alta",
  "accion_solicitada": "Devolución del dinero o reemplazo urgente"
}
```

## Requisitos

- Python 3.10+
- Un servidor Omniroute corriendo localmente (o cualquier endpoint
  compatible con OpenAI `/v1/chat/completions`)

## Instalación

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/macOS
pip install -r requirements.txt
cp .env.example .env          # y editar OMNI_API_KEY
```

## Uso

```bash
# Analizar el archivo de ejemplo (default: nota_sucia.txt)
python analizador.py

# Analizar otro archivo
python analizador.py otra_nota.txt

# Analizar texto directo por CLI
python analizador.py --texto "El cliente Ana Gómez reclama el producto #123..."

# Elegir el archivo de salida
python analizador.py nota.txt --salida mi_resultado.json
```

## Pruebas (sin Omniroute)

El suite levanta un servidor HTTP simulado que imita las respuestas SSE de
Omniroute, así se puede verificar el proyecto completo sin el servidor real:

```bash
python -m unittest discover -s tests
```

Cubre: validación de campos, payload/Bearer enviados, respuesta JSON normal,
respuesta SSE, limpieza de delimitadores Markdown y rechazo de esquemas inválidos.

## Estructura

```
.
├── analizador.py              # Script principal (CLI)
├── nota_sucia.txt             # Entrada de ejemplo
├── ejemplo_resultado.json     # Salida de ejemplo
├── tests/test_analizador.py   # Tests con mock de Omniroute
├── requirements.txt
├── .env.example               # Plantilla de configuración
└── README.md
```

## Cómo funciona

1. Lee texto libre desde un archivo o por CLI.
2. POST a `/v1/chat/completions` con un system prompt que exige JSON estricto
   (temperature 0.1 para consistencia).
3. Parsea la respuesta (SSE o JSON) y limpia posibles delimitadores Markdown.
4. Valida con un modelo Pydantic (`AnalisisResultado`): `cliente`,
   `id_producto`, `monto_reclamado`, `motivo_reclamo`, `prioridad`,
   `accion_solicitada`.
5. Guarda el resultado en `resultado_estructurado.json`.

## Limitaciones conocidas

- **Formato de montos**: el modelo puede interpretar de forma ambigua
  montos con separador de miles latinoamericano (`$12.500`). Para
  resultados confiables, escribí los montos sin separadores
  (`$12500`) o con palabras (`12 mil quinientos`).
- Depende de un servidor Omniroute (o endpoint compatible con OpenAI)
  corriendo localmente.

## Notas

- El endpoint y modelo se pueden sobreescribir con las variables de entorno
  `OMNIROUTE_URL` y `OMNIROUTE_MODEL`.
- En Omniroute, el modelo `auto` usa el combo routing y selecciona un modelo
  con credenciales activas.
- `.env` está en `.gitignore`: nunca commitear claves de API.
