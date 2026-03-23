# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Read-only MCP server exposing Langfuse observability data (scores, traces, datasets, sessions, observations) as MCP tools via FastAPI. No write operations to Langfuse.

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

No test suite exists. No linter/formatter configured.

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

All MCP tools are defined as FastAPI `GET` routes in `main.py`. `fastapi-mcp` automatically exposes these as MCP tools. Health/ready endpoints are excluded via `exclude_operations`.

### Request Flow

1. All requests hit the HTTP middleware in `main.py` first
2. MCP protocol requests (`POST /mcp`) are intercepted by middleware for: `/ready`, `/resources/list`, `/resources/read`, `/prompts/list`, `/ping`
3. MCP tool calls are forwarded to FastAPI route handlers
4. Route handlers call `LangfuseClient` methods, which all funnel through `client.py:_request()` — the single point for HTTP calls to Langfuse

### Key Patterns

- **Global singleton client**: `LangfuseClient` is lazily created via `get_langfuse_client()` in `main.py`, closed on shutdown via lifespan handler
- **Parameter name mapping**: Python snake_case params are mapped to Langfuse camelCase in `client.py` (e.g., `trace_id` → `traceId`, `from_timestamp` → `fromTimestamp`)
- **Settings**: `config.py` uses `pydantic-settings` with `@lru_cache` — settings are loaded once from `.env` and cached
- **Response types**: `typing.py` defines `TypedDict` schemas matching Langfuse API responses (all use `total=False` for optional fields)
- **Error handling**: `LangfuseClientError` wraps httpx errors with status codes, route handlers convert these to `HTTPException`

### MCP Resources

Defined inline in `main.py` (not as files):
- `langfuse://resources/openapi` — serves the live OpenAPI schema
- `langfuse://resources/guide` — serves `MCP_DESCRIPTION` as markdown

## Adding a New Endpoint

1. Add the client method in `client.py` (follow existing pattern: params dict → `_request()` → typed response)
2. Add TypedDict response types in `typing.py` if needed
3. Add the FastAPI route in `main.py` (GET route with Query params, try/except LangfuseClientError)
4. The route is automatically exposed as an MCP tool by `fastapi-mcp`

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
