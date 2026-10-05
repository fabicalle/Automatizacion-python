# Analizador de Notas — Clean Architecture + LLM

Mini proyecto en Python que toma una nota de texto libre (por
ejemplo, una queja de cliente desestructurada), la envía a un
endpoint local [Omniroute](https://www.npmjs.com/package/omniroute)
compatible con OpenAI pidiendo **JSON estricto**, valida la
respuesta con **Pydantic** y guarda el resultado en un JSON.

## Demo

Entrada (`nota_sucia.txt`):

> El cliente Juan Pérez llamó el 12 de Octubre molesto porque el
> envío del producto #8841 (Teclado Mecánico) llegó con la caja
> rota. Quiere la devolución de sus $45.000 o un reemplazo urgente.
> Prioridad alta.

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

## Arquitectura (Clean Architecture)

```
analizador/
├── domain/            # Entidades y puertos (cero dependencias externas)
│   ├── schema.py      #    AnalisisResultado (Pydantic) + reglas
│   └── ports.py       #    LlmClient, FuenteTexto, DestinoResultado
├── application/       # Casos de uso (orquestación, sin HTTP)
│   └── analizar_nota.py
├── infrastructure/    # Adaptadores (implementan los puertos)
│   ├── omniroute_client.py   # HTTP + parseo SSE/JSON + reintentos
│   └── persistencia.py       # ArchivoTexto, TextoDirecto, JsonFile
└── interface/         # CLI — raíz de composición (inyección de dependencias)
    └── cli.py
```

Regla de dependencias: `domain ← application ← infrastructure/interface`.
El caso de uso depende del puerto `LlmClient`, no del cliente HTTP
real — por eso los tests unitarios corren con un fake, sin red.

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
python main.py
# o
python -m analizador

# Analizar otro archivo
python main.py otra_nota.txt

# Texto directo por CLI
python main.py --texto "El cliente Ana Gomez reclama el producto #123 por $12500..."

# Elegir el archivo de salida
python main.py nota.txt --salida mi_resultado.json
```

## Pruebas

El suite tiene tests unitarios (dominio, caso de uso con fake,
CLI) e integración (cliente Omniroute contra un servidor HTTP
simulado que imita respuestas SSE y JSON). No requiere Omniroute:

```bash
python -m unittest discover -s tests -v
```

## Auditoría y calidad

- `ruff check .` y `ruff format --check .` — lint y formato
- `mypy analizador` — tipado estático
- `bandit -r analizador` — seguridad
- CI en GitHub Actions ejecuta los tests en cada push/PR
- `.env` y `.env.*` ignorados por git (solo `.env.example` se
  versiona) — sin riesgo de fuga de API keys

## Configuración (variables de entorno)

| Variable         | Default                                       | Uso                            |
| ---------------- | --------------------------------------------- | ------------------------------ |
| `OMNI_API_KEY`   | — (requerida)                                 | Bearer token para Omniroute    |
| `OMNIROUTE_URL`  | `http://localhost:20128/v1/chat/completions` | Endpoint del servidor          |
| `OMNIROUTE_MODEL`| `auto`                                        | Modelo o alias (combo routing) |
| `OMNIROUTE_TIMEOUT` | `120` segundos                             | Timeout HTTP                   |

## Limitaciones conocidas

- **Formato de montos**: el modelo puede interpretar de forma
  ambigua montos con separador de miles latinoamericano
  (`$12.500`). Para resultados confiables, escribí los montos
  sin separadores (`$12500`) o con palabras (`12 mil quinientos`).
- Depende de un servidor Omniroute (o endpoint compatible con
  OpenAI) corriendo localmente.

## Estructura del repo

```
.
├── analizador/            # Paquete (Clean Architecture)
├── tests/
│   ├── unit/              # Dominio, caso de uso, CLI
│   └── integration/       # Cliente Omniroute con mock HTTP
├── main.py                # Entrada: python main.py
├── nota_sucia.txt         # Entrada de ejemplo
├── ejemplo_resultado.json # Salida de ejemplo
├── pyproject.toml         # Metadata + config ruff/mypy
├── requirements.txt
├── .env.example           # Plantilla de configuración
├── LICENSE
└── README.md
```
