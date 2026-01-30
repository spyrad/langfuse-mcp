# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Model Context Protocol (MCP) server providing read-only access to Langfuse observability data. It exposes Langfuse API endpoints as MCP tools for use with Claude Code and other MCP-compatible clients.

## Development Commands

```bash
# Setup
python -m venv venv
venv\Scripts\activate          # Windows
source venv/bin/activate       # Linux/Mac
pip install -r requirements.txt

# Run development server
uvicorn src.main:app --host localhost --port 8010 --reload

# Run production server
uvicorn src.main:app --host 0.0.0.0 --port 8010
```

## Configuration

Copy `.env.dist` to `.env` and configure:

| Variable | Required | Description |
|----------|----------|-------------|
| `LANGFUSE_SECRET_KEY` | Yes | Langfuse Secret Key (`sk_lf_...`) |
| `LANGFUSE_PUBLIC_KEY` | Yes | Langfuse Public Key (`pk_lf_...`) |
| `LANGFUSE_HOST` | Yes | Langfuse Server URL |
| `LANGFUSE_VERIFY_SSL` | No | Set to `false` for self-signed certs |
| `MCP_SERVER_PORT` | No | Default: 8010 |
| `LOG_LEVEL` | No | Default: INFO |

## Architecture

```
src/
├── main.py              # FastAPI app + MCP setup, all endpoint definitions
├── config.py            # Pydantic-settings configuration
└── langfuse/
    ├── client.py        # Async httpx client wrapping Langfuse REST API
    └── typing.py        # TypedDict response schemas
```

### Key Design Decisions

- **Read-only API**: No write operations to Langfuse
- **Single entry point**: All MCP tools defined in `main.py` as FastAPI routes
- **Async throughout**: Uses `httpx.AsyncClient` for non-blocking API calls
- **HTTP middleware**: Custom middleware in `main.py` handles MCP-specific routes (`/mcp/ready`, `/resources/list`, `/resources/read`, `/prompts/list`)

### MCP Integration

The server uses `fastapi-mcp` to expose FastAPI routes as MCP tools. Health/ready endpoints are excluded from MCP tool listing via `exclude_operations`.

MCP resources are defined inline in `main.py`:
- `langfuse://resources/openapi` - OpenAPI schema
- `langfuse://resources/guide` - Usage guide

## API Endpoints

| Tool | Description |
|------|-------------|
| `list_scores` / `get_score` | Evaluation scores and metrics |
| `list_traces` / `get_trace` | Full LLM interaction traces |
| `list_datasets` / `get_dataset` / `list_dataset_runs` | Evaluation datasets |
| `list_sessions` / `get_session` | Grouped traces by session |
| `list_observations` / `get_observation` | Individual observations (generations, spans, events) |

All list endpoints support pagination (`page`, `limit`) and filtering parameters.

## Claude Code Integration

```json
{
  "mcpServers": {
    "langfuse": {
      "url": "http://localhost:8010/mcp"
    }
  }
}
```
