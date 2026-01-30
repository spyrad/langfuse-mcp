# Langfuse MCP Server

Ein Model Context Protocol (MCP) Server für den Zugriff auf Langfuse Observability-Daten.

## Features

- **Scores**: Bewertungen und Metriken von LLM-Aufrufen abrufen
- **Traces**: Vollständige Ablaufverfolgung von LLM-Interaktionen
- **Datasets**: Evaluations-Datasets und deren Runs
- **Sessions**: Gruppierte Traces nach Session-ID
- **Observations**: Einzelne Observations (Generations, Spans, Events)

## Installation

```bash
# Repository klonen / Verzeichnis wechseln
cd langfuse-mcp

# Virtual Environment erstellen
python -m venv venv

# Aktivieren (Windows)
venv\Scripts\activate

# Aktivieren (Linux/Mac)
source venv/bin/activate

# Dependencies installieren
pip install -r requirements.txt
```

## Konfiguration

Kopiere `.env.dist` nach `.env` und konfiguriere die Umgebungsvariablen:

```bash
cp .env.dist .env
```

Erforderliche Variablen:

| Variable | Beschreibung | Beispiel |
|----------|--------------|----------|
| `LANGFUSE_SECRET_KEY` | Langfuse Secret Key | `sk_lf_...` |
| `LANGFUSE_PUBLIC_KEY` | Langfuse Public Key | `pk_lf_...` |
| `LANGFUSE_HOST` | Langfuse Server URL | `https://langfuse.example.com` |

Optionale Variablen:

| Variable | Beschreibung | Default |
|----------|--------------|---------|
| `MCP_SERVER_PORT` | Server Port | `8010` |
| `LOG_LEVEL` | Log Level | `INFO` |
| `LANGFUSE_VERIFY_SSL` | SSL-Zertifikat verifizieren | `true` |

## Server starten

```bash
# Development
uvicorn src.main:app --host localhost --port 8010 --reload

# Production
uvicorn src.main:app --host 0.0.0.0 --port 8010
```

## API Endpoints

### Health & Ready

| Endpoint | Beschreibung |
|----------|--------------|
| `GET /health` | Health Check |
| `GET /ready` | Readiness Check (prüft Langfuse-Verbindung) |

### MCP Tools

| Tool | Endpoint | Beschreibung |
|------|----------|--------------|
| `list_scores` | `GET /list_scores` | Scores mit Filtern abrufen |
| `get_score` | `GET /get_score` | Einzelnen Score abrufen |
| `list_traces` | `GET /list_traces` | Traces auflisten |
| `get_trace` | `GET /get_trace` | Trace-Details abrufen |
| `list_datasets` | `GET /list_datasets` | Datasets auflisten |
| `get_dataset` | `GET /get_dataset` | Dataset abrufen |
| `list_dataset_runs` | `GET /list_dataset_runs` | Runs eines Datasets |
| `list_sessions` | `GET /list_sessions` | Sessions auflisten |
| `get_session` | `GET /get_session` | Session abrufen |
| `list_observations` | `GET /list_observations` | Observations auflisten |
| `get_observation` | `GET /get_observation` | Observation abrufen |

### MCP Endpoint

Der MCP-Endpoint ist unter `POST /mcp` verfügbar.

## Verwendung mit Claude Code

Füge den Server als MCP-Server in deiner Claude Code Konfiguration hinzu:

```json
{
  "mcpServers": {
    "langfuse": {
      "url": "http://localhost:8010/mcp"
    }
  }
}
```

## API Dokumentation

Wenn der Server läuft:

- Swagger UI: http://localhost:8010/docs
- ReDoc: http://localhost:8010/redoc
- OpenAPI JSON: http://localhost:8010/openapi.json

## Projektstruktur

```
langfuse-mcp/
├── README.md                 # Diese Datei
├── PLAN.md                   # Implementierungsplan
├── requirements.txt          # Python Dependencies
├── .env.dist                 # Environment-Template
├── .gitignore
└── src/
    ├── __init__.py
    ├── main.py               # FastAPI + MCP Setup
    ├── config.py             # Settings (pydantic-settings)
    └── langfuse/
        ├── __init__.py
        ├── client.py         # Langfuse API Client Wrapper
        └── typing.py         # TypedDict Response-Schemas
```

## Technologie-Stack

- **Framework:** FastAPI + FastApiMCP
- **Python:** 3.13
- **HTTP Client:** httpx (async)
- **Settings:** pydantic-settings

## Lizenz

MIT
