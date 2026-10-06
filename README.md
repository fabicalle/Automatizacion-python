# Note Analyzer — Clean Architecture + LLM

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![CI](https://github.com/your-username/analizador-notas/actions/workflows/tests.yml/badge.svg)](https://github.com/your-username/analizador-notas/actions)

> Extracts structured data from unstructured text notes using a local
> [Omniroute](https://www.npmjs.com/package/omniroute) server
> (OpenAI-compatible), validates the response with **Pydantic**,
> and persists the result as JSON.

## Highlights

- **Clean Architecture** — domain, application, infrastructure, and
  interface layers with enforced dependency direction
- **Strict JSON extraction** — system-prompt driven schema contract
  with low temperature for deterministic output
- **Robust transport** — handles both JSON and SSE
  (`text/event-stream`) responses, explicit UTF-8 decoding,
  connection retries with backoff
- **Dependency injection** — the use case depends on the `LlmClient`
  port, not on HTTP; unit tests run fully offline with a fake
- **Zero-secret repo** — `.env` and `.env.*` are git-ignored; only
  `.env.example` is versioned

## Demo

Input (`nota_sucia.txt`):

> El cliente Juan Pérez llamó el 12 de Octubre molesto porque el
> envío del producto #8841 (Teclado Mecánico) llegó con la caja
> rota. Quiere la devolución de sus $45.000 o un reemplazo urgente.
> Prioridad alta.

Output (`resultado_estructurado.json`):

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

## Architecture

```
analizador/
├── domain/            # Entities and ports (zero external dependencies)
│   ├── schema.py      #    AnalisisResultado (Pydantic) + business rules
│   └── ports.py       #    LlmClient, FuenteTexto, DestinoResultado
├── application/       # Use cases (orchestration, no I/O)
│   └── analizar_nota.py
├── infrastructure/    # Adapters (implement the ports)
│   ├── omniroute_client.py   # HTTP + SSE/JSON parsing + retries
│   └── persistencia.py       # ArchivoTexto, TextoDirecto, JsonFile
└── interface/         # CLI — composition root (dependency injection)
    └── cli.py
```

**Dependency rule:** `domain ← application ← infrastructure/interface`.
`AnalizarNotaUseCase` only knows the `LlmClient` abstraction, so the
HTTP client, storage, or LLM provider can be swapped without touching
business logic.

## Requirements

- Python 3.10+
- A local Omniroute server (or any OpenAI-compatible
  `/v1/chat/completions` endpoint)

## Installation

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux/macOS
pip install -r requirements.txt
cp .env.example .env            # then edit OMNI_API_KEY
```

## Usage

```bash
# Analyze the sample file (default: nota_sucia.txt)
python main.py
# or
python -m analizador

# Analyze another file
python main.py otra_nota.txt

# Pass text directly via CLI
python main.py --texto "El cliente Ana Gomez reclama el producto #123 por $12500..."

# Custom output file
python main.py nota.txt --salida mi_resultado.json
```

## Testing

18 tests — unit (domain rules, use case with a fake `LlmClient`,
CLI arg parsing) and integration (Omniroute client against a local
HTTP server that mimics real SSE and JSON responses). No running
Omniroute required:

```bash
python -m unittest discover -s tests -v
```

## Quality & security

| Check | Command | Status |
| ----- | ------- | ------ |
| Lint & format | `ruff check .` / `ruff format --check .` | clean |
| Static typing | `mypy analizador` | clean |
| Security scan | `bandit -r analizador -ll` | 0 issues |
| Test suite | `python -m unittest discover -s tests` | 18/18 |
| Secret leakage | `git check-ignore .env` | ignored |

CI (GitHub Actions) runs the suite on every push and PR
(`.github/workflows/tests.yml`).

## Configuration

| Variable          | Default                                       | Purpose                    |
| ----------------- | --------------------------------------------- | -------------------------- |
| `OMNI_API_KEY`    | — (required)                                  | Bearer token for Omniroute |
| `OMNIROUTE_URL`   | `http://localhost:20128/v1/chat/completions` | Server endpoint           |
| `OMNIROUTE_MODEL` | `auto`                                        | Model or alias (combo routing) |
| `OMNIROUTE_TIMEOUT` | `120` (seconds)                             | HTTP timeout               |

## Known limitations

- **Amount formats:** the LLM can misparse amounts using the
  Latin-American thousands separator (`$12.500`). For reliable
  results, write amounts without separators (`$12500`) or in words
  (`12 mil quinientos`).
- Requires a local Omniroute server (or an OpenAI-compatible
  endpoint) to be running.

## Repository structure

```
.
├── analizador/             # Package (Clean Architecture)
├── tests/
│   ├── unit/               # Domain, use case, CLI
│   └── integration/        # Omniroute client with HTTP mock
├── main.py                 # Entry point: python main.py
├── nota_sucia.txt          # Sample input
├── ejemplo_resultado.json  # Sample output
├── pyproject.toml          # Metadata + ruff/mypy config
├── requirements.txt
├── .env.example            # Configuration template
├── LICENSE
└── README.md
```

## License

[MIT](LICENSE) © Fabian Calle
