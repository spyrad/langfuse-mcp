# Plan: Langfuse MCP Server

## Ziel
Erstelle einen MCP-Server für Langfuse-Zugriff in `C:\Users\SpyraD\Desktop\Projekte\langfuse-mcp`.

## Technologie-Stack
- **Framework:** FastAPI + FastApiMCP (wie mcp-server-mis)
- **Python:** 3.13
- **Langfuse SDK:** `langfuse` Python Package für API-Zugriff

## Langfuse API Endpoints (zu implementieren)

### Priorität 1: Scores & Evaluation (MVP)
| Tool | Langfuse API | Beschreibung |
|------|--------------|--------------|
| `list_scores` | GET /api/public/scores | Scores mit Filtern abrufen |
| `get_score` | GET /api/public/scores/{id} | Einzelnen Score abrufen |

**Hinweis:** Read-only - keine Schreiboperationen.

### Priorität 2: Traces
| Tool | Langfuse API | Beschreibung |
|------|--------------|--------------|
| `list_traces` | GET /api/public/traces | Traces auflisten |
| `get_trace` | GET /api/public/traces/{id} | Trace-Details abrufen |

### Priorität 3: Datasets & Runs
| Tool | Langfuse API | Beschreibung |
|------|--------------|--------------|
| `list_datasets` | GET /api/public/v2/datasets | Datasets auflisten |
| `get_dataset` | GET /api/public/v2/datasets/{name} | Dataset abrufen |
| `list_dataset_runs` | GET /api/public/datasets/{name}/runs | Runs eines Datasets |

### Priorität 4: Sessions & Observations
| Tool | Langfuse API | Beschreibung |
|------|--------------|--------------|
| `list_sessions` | GET /api/public/sessions | Sessions auflisten |
| `list_observations` | GET /api/public/v2/observations | Observations (v2 API) |

## Projektstruktur

```
langfuse-mcp/
├── README.md                 # Projektdokumentation
├── PLAN.md                   # Dieser Plan (Kopie)
├── requirements.txt          # Dependencies
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

## Implementierungsschritte

### Phase 1: Projekt-Setup ✅
1. Verzeichnisstruktur erstellen
2. `requirements.txt` mit Dependencies
3. `.env.dist` mit Konfigurations-Template
4. `src/config.py` mit pydantic-settings
5. `.gitignore` erstellen

### Phase 2: Langfuse Client ✅
1. `src/langfuse/client.py` - API-Wrapper mit:
   - Authentifizierung (Secret Key + Public Key)
   - HTTP-Client mit Timeout/Retry
   - Error Handling

### Phase 3: MCP Tools (Scores) - MVP ✅
1. `list_scores` - Filter: trace_id, name, user_id, data_type
2. `get_score` - Einzelner Score by ID

### Phase 4: MCP Tools (Traces & Datasets) ✅
1. `list_traces` - Mit Pagination
2. `get_trace` - Inkl. Observations
3. `list_datasets` / `get_dataset`
4. `list_dataset_runs`

### Phase 5: MCP Server Setup ✅
1. `src/main.py` - FastAPI + FastApiMCP
2. Health/Ready Endpoints
3. CORS Middleware
4. MCP Resources (OpenAPI, Guide)

## Kritische Dateien

| Datei | Zweck |
|-------|-------|
| `src/main.py` | MCP Server Entry Point |
| `src/langfuse/client.py` | Langfuse API Integration |
| `src/config.py` | Environment Configuration |
| `requirements.txt` | Dependencies |

## Environment Variables

```bash
# Langfuse API
LANGFUSE_SECRET_KEY=sk_lf_...
LANGFUSE_PUBLIC_KEY=pk_lf_...
LANGFUSE_HOST=https://langfuse.example.com

# Server
MCP_SERVER_PORT=8010
LOG_LEVEL=INFO

# SSL (für self-signed Zertifikate)
LANGFUSE_VERIFY_SSL=true  # auf false setzen für self-signed
```

## Dependencies (requirements.txt)

```
fastapi>=0.115.0
fastapi-mcp>=0.4.0
uvicorn>=0.34.0
pydantic>=2.8.0
pydantic-settings>=2.5.2
httpx>=0.27.0
python-dotenv>=1.0.0
```

## Verifikation

1. **Server startet:** `uvicorn src.main:app --port 8010`
2. **Health Check:** GET http://localhost:8010/health → 200
3. **MCP Endpoint:** POST http://localhost:8010/mcp funktioniert
4. **Tool Test:** `list_scores` gibt Langfuse-Daten zurück
5. **Integration:** Claude Code kann MCP-Server als Tool nutzen

## Entscheidungen

- **Schreibzugriff:** Nur Lesen (read-only) - keine create/delete Operationen
- **SSL:** Konfigurierbar via `LANGFUSE_VERIFY_SSL` Environment Variable
- **Priorität:** Scores zuerst (MVP), dann Traces & Datasets erweitern

## Status

✅ **Implementierung abgeschlossen** (2025-01-20)

Alle geplanten Features wurden implementiert:
- Scores API (list, get)
- Traces API (list, get)
- Datasets API (list, get, runs)
- Sessions API (list, get)
- Observations API (list, get)
