"""Langfuse MCP Server - Model Context Protocol server for Langfuse API access."""

import json
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Literal

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi_mcp import FastApiMCP

from src.config import get_settings
from src.langfuse import LangfuseClient
from src.langfuse.client import LangfuseClientError

# Version and metadata
MCP_VERSION = "1.0.0"
MCP_TITLE = "Langfuse MCP-Server"

_current_date = datetime.now().date().isoformat()

MCP_DESCRIPTION = f"""MCP-Server für den Zugriff auf Langfuse Observability-Daten.

Dieser Server ermöglicht den Zugriff auf:
- **Scores**: Bewertungen und Metriken von LLM-Aufrufen
- **Traces**: Vollständige Ablaufverfolgung von LLM-Interaktionen
- **Datasets**: Evaluations-Datasets und deren Runs
- **Sessions**: Gruppierte Traces nach Session-ID
- **Observations**: Einzelne Observations (Generations, Spans, Events)

**Typisches Vorgehen:**
1. Mit `list_scores` Scores filtern nach trace_id, name, oder data_type
2. Mit `get_trace` Details zu einem spezifischen Trace abrufen
3. Mit `list_datasets` verfügbare Evaluations-Datasets auflisten
4. Mit `list_observations` Observations filtern nach trace_id oder type

**Wichtige Hinweise:**
- Alle Zeitstempel sind im ISO 8601 Format (z.B. "2024-01-15T10:30:00Z")
- Pagination: page (1-indexed), limit (default 50, max 100)
- Das aktuelle Datum ist {_current_date}

**Read-Only API:** Dieser Server unterstützt nur Leseoperationen.
"""

# Configure logging
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

# Global Langfuse client instance
_langfuse_client: LangfuseClient | None = None


def get_langfuse_client() -> LangfuseClient:
    """Get or create the Langfuse client instance."""
    global _langfuse_client
    if _langfuse_client is None:
        _langfuse_client = LangfuseClient()
    return _langfuse_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan handler for startup and shutdown."""
    # Startup
    logger.info(f"Starting {MCP_TITLE} v{MCP_VERSION}")
    settings = get_settings()
    logger.info(f"Langfuse host: {settings.langfuse_host}")
    yield
    # Shutdown
    logger.info("Shutting down Langfuse MCP Server")
    client = get_langfuse_client()
    await client.close()


# Initialize FastAPI app
app = FastAPI(
    title=MCP_TITLE,
    description=MCP_DESCRIPTION,
    version=MCP_VERSION,
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["mcp-session-id", "x-session-id"],
)

# MCP resource descriptors
MCP_RESOURCES = [
    {
        "uri": "langfuse://resources/openapi",
        "name": "OpenAPI schema",
        "mimeType": "application/json",
    },
    {
        "uri": "langfuse://resources/guide",
        "name": "MCP Usage Guide",
        "description": MCP_DESCRIPTION,
        "mimeType": "text/markdown",
    },
]


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware for request logging and MCP resource handling."""
    # Handle MCP routes
    if request.url.path.startswith("/mcp") and request.method.upper() == "POST":
        try:
            body_bytes = await request.body()
            data = json.loads(body_bytes or b"{}")
            endpoint = (
                f"/{data.get('method')}" if data.get("method") else request.url.path
            ).replace("/mcp", "")

            # Handle /mcp/ready
            if endpoint == "/ready":
                return JSONResponse(
                    {
                        "jsonrpc": data.get("jsonrpc", "2.0"),
                        "id": data.get("id"),
                        "result": {"ready": True},
                    }
                )

            # Handle resources/list
            if endpoint == "/resources/list":
                return JSONResponse(
                    {
                        "jsonrpc": data.get("jsonrpc", "2.0"),
                        "id": data.get("id"),
                        "result": {"resources": MCP_RESOURCES},
                    }
                )

            # Handle resources/read
            if endpoint == "/resources/read":
                uris = (data.get("params") or {}).get("uris", [])
                out = []
                for uri in uris:
                    if uri == "langfuse://resources/openapi":
                        out.append(
                            {
                                "uri": uri,
                                "mimeType": "application/json",
                                "text": json.dumps(app.openapi(), ensure_ascii=False),
                            }
                        )
                    elif uri == "langfuse://resources/guide":
                        guide = f"# {MCP_TITLE}\n\n{MCP_DESCRIPTION}"
                        out.append(
                            {
                                "uri": uri,
                                "mimeType": "text/markdown",
                                "text": guide,
                            }
                        )
                return JSONResponse(
                    {
                        "jsonrpc": data.get("jsonrpc", "2.0"),
                        "id": data.get("id"),
                        "result": {"resources": out},
                    }
                )

            if endpoint == "/ping":
                return JSONResponse(
                    {
                        "jsonrpc": data.get("jsonrpc", "2.0"),
                        "id": data.get("id"),
                        "result": {"pong": True},
                    }
                )

            # Handle prompts/list
            if endpoint == "/prompts/list":
                return JSONResponse(
                    {
                        "jsonrpc": data.get("jsonrpc", "2.0"),
                        "id": data.get("id"),
                        "result": {"prompts": []},
                    }
                )

            # Re-inject body for downstream handlers
            async def receive():
                return {"type": "http.request", "body": body_bytes, "more_body": False}

            request = Request(request.scope, receive)
            return await call_next(request)

        except Exception:
            pass

    # Log request
    url_path = request.url.path.split("/")[-1]
    params = request.url.query
    logger.debug(f"REQUEST: /{url_path}?{params}")

    response = await call_next(request)
    logger.debug(f"RESPONSE: Status {response.status_code}")
    return response


# ========== Health Endpoints ==========


@app.get("/health")
async def health_check():
    """Health check endpoint (not exposed as MCP tool)."""
    return {"status": "ok", "message": "Langfuse MCP Server is running"}


@app.get("/ready")
async def ready_check():
    """Readiness check - verifies Langfuse connectivity."""
    try:
        client = get_langfuse_client()
        # Try to list scores with limit 1 to verify connection
        await client.list_scores(limit=1)
        return {"status": "ok", "message": "Langfuse connection successful"}
    except Exception as e:
        return {"status": "error", "message": f"Langfuse connection failed: {e}"}


# ========== Scores API ==========


@app.get("/list_scores")
async def list_scores(
    page: int | None = Query(None, description="Page number (1-indexed)"),
    limit: int | None = Query(None, description="Items per page (default 50, max 100)"),
    trace_id: str | None = Query(None, description="Filter by trace ID"),
    user_id: str | None = Query(None, description="Filter by user ID"),
    name: str | None = Query(None, description="Filter by score name"),
    data_type: Literal["NUMERIC", "CATEGORICAL", "BOOLEAN"] | None = Query(
        None, description="Filter by data type"
    ),
    source: Literal["API", "ANNOTATION", "EVAL"] | None = Query(
        None, description="Filter by source"
    ),
    from_timestamp: str | None = Query(
        None, description="Filter from timestamp (ISO 8601)"
    ),
    to_timestamp: str | None = Query(
        None, description="Filter to timestamp (ISO 8601)"
    ),
    environment: str | None = Query(
        None, description="Filter by environment (e.g. development, production, default)"
    ),
) -> dict:
    """Liste Scores mit optionalen Filtern.

    Scores sind Bewertungen von LLM-Aufrufen, z.B. Qualitätsmetriken,
    User-Feedback oder automatische Evaluationen.

    Returns:
        data: Liste von Score-Objekten
        meta: Pagination-Metadaten
    """
    try:
        client = get_langfuse_client()
        result = await client.list_scores(
            page=page,
            limit=limit,
            trace_id=trace_id,
            user_id=user_id,
            name=name,
            data_type=data_type,
            source=source,
            from_timestamp=from_timestamp,
            to_timestamp=to_timestamp,
            environment=environment,
        )
        return dict(result)
    except LangfuseClientError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=e.message)


@app.get("/get_score")
async def get_score(
    score_id: str = Query(..., description="The score ID to retrieve"),
) -> dict:
    """Hole einen einzelnen Score anhand seiner ID.

    Returns:
        Score-Objekt mit allen Details inkl. value, traceId, timestamp
    """
    try:
        client = get_langfuse_client()
        result = await client.get_score(score_id)
        return dict(result)
    except LangfuseClientError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=e.message)


# ========== Traces API ==========


@app.get("/list_traces")
async def list_traces(
    page: int | None = Query(None, description="Page number (1-indexed)"),
    limit: int | None = Query(None, description="Items per page (default 50, max 100)"),
    user_id: str | None = Query(None, description="Filter by user ID"),
    session_id: str | None = Query(None, description="Filter by session ID"),
    name: str | None = Query(None, description="Filter by trace name"),
    from_timestamp: str | None = Query(
        None, description="Filter from timestamp (ISO 8601)"
    ),
    to_timestamp: str | None = Query(
        None, description="Filter to timestamp (ISO 8601)"
    ),
    version: str | None = Query(None, description="Filter by version"),
    release: str | None = Query(None, description="Filter by release"),
    environment: str | None = Query(
        None, description="Filter by environment (e.g. development, production, default)"
    ),
) -> dict:
    """Liste Traces mit optionalen Filtern.

    Ein Trace repräsentiert eine vollständige LLM-Interaktion,
    inkl. aller Observations (Generations, Spans, Events).

    Returns:
        data: Liste von Trace-Objekten
        meta: Pagination-Metadaten
    """
    try:
        client = get_langfuse_client()
        result = await client.list_traces(
            page=page,
            limit=limit,
            user_id=user_id,
            session_id=session_id,
            name=name,
            from_timestamp=from_timestamp,
            to_timestamp=to_timestamp,
            version=version,
            release=release,
            environment=environment,
        )
        return dict(result)
    except LangfuseClientError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=e.message)


@app.get("/get_trace")
async def get_trace(
    trace_id: str = Query(..., description="The trace ID to retrieve"),
) -> dict:
    """Hole einen einzelnen Trace anhand seiner ID.

    Inkludiert alle zugehörigen Observations und Scores.

    Returns:
        Trace-Objekt mit observations[], scores[], input, output, metadata
    """
    try:
        client = get_langfuse_client()
        result = await client.get_trace(trace_id)
        return dict(result)
    except LangfuseClientError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=e.message)


# ========== Datasets API ==========


@app.get("/list_datasets")
async def list_datasets(
    page: int | None = Query(None, description="Page number (1-indexed)"),
    limit: int | None = Query(None, description="Items per page (default 50, max 100)"),
) -> dict:
    """Liste alle Datasets.

    Datasets werden für Evaluationen verwendet und enthalten
    Input/Expected-Output Paare.

    Returns:
        data: Liste von Dataset-Objekten
        meta: Pagination-Metadaten
    """
    try:
        client = get_langfuse_client()
        result = await client.list_datasets(page=page, limit=limit)
        return dict(result)
    except LangfuseClientError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=e.message)


@app.get("/get_dataset")
async def get_dataset(
    dataset_name: str = Query(..., description="The dataset name to retrieve"),
) -> dict:
    """Hole ein Dataset anhand seines Namens.

    Returns:
        Dataset-Objekt mit items[], metadata, description
    """
    try:
        client = get_langfuse_client()
        result = await client.get_dataset(dataset_name)
        return dict(result)
    except LangfuseClientError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=e.message)


@app.get("/list_dataset_runs")
async def list_dataset_runs(
    dataset_name: str = Query(..., description="The dataset name"),
    page: int | None = Query(None, description="Page number (1-indexed)"),
    limit: int | None = Query(None, description="Items per page (default 50, max 100)"),
) -> dict:
    """Liste alle Runs für ein Dataset.

    Ein Run ist eine Ausführung einer Evaluation gegen ein Dataset.

    Returns:
        data: Liste von DatasetRun-Objekten
        meta: Pagination-Metadaten
    """
    try:
        client = get_langfuse_client()
        result = await client.list_dataset_runs(
            dataset_name=dataset_name, page=page, limit=limit
        )
        return dict(result)
    except LangfuseClientError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=e.message)


# ========== Sessions API ==========


@app.get("/list_sessions")
async def list_sessions(
    page: int | None = Query(None, description="Page number (1-indexed)"),
    limit: int | None = Query(None, description="Items per page (default 50, max 100)"),
    from_timestamp: str | None = Query(
        None, description="Filter from timestamp (ISO 8601)"
    ),
    to_timestamp: str | None = Query(
        None, description="Filter to timestamp (ISO 8601)"
    ),
    environment: str | None = Query(
        None, description="Filter by environment (e.g. development, production, default)"
    ),
) -> dict:
    """Liste alle Sessions.

    Sessions gruppieren mehrere Traces, die zu einer
    User-Konversation gehören.

    Returns:
        data: Liste von Session-Objekten
        meta: Pagination-Metadaten
    """
    try:
        client = get_langfuse_client()
        result = await client.list_sessions(
            page=page,
            limit=limit,
            from_timestamp=from_timestamp,
            to_timestamp=to_timestamp,
            environment=environment,
        )
        return dict(result)
    except LangfuseClientError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=e.message)


@app.get("/get_session")
async def get_session(
    session_id: str = Query(..., description="The session ID to retrieve"),
) -> dict:
    """Hole eine Session anhand ihrer ID.

    Returns:
        Session-Objekt mit zugehörigen Traces
    """
    try:
        client = get_langfuse_client()
        result = await client.get_session(session_id)
        return dict(result)
    except LangfuseClientError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=e.message)


# ========== Observations API ==========


@app.get("/list_observations")
async def list_observations(
    page: int | None = Query(None, description="Page number (1-indexed)"),
    limit: int | None = Query(None, description="Items per page (default 50, max 100)"),
    trace_id: str | None = Query(None, description="Filter by trace ID"),
    name: str | None = Query(None, description="Filter by observation name"),
    type: Literal["GENERATION", "SPAN", "EVENT"] | None = Query(
        None, description="Filter by type (GENERATION, SPAN, EVENT)"
    ),
    user_id: str | None = Query(None, description="Filter by user ID"),
    from_start_time: str | None = Query(
        None, description="Filter from start time (ISO 8601)"
    ),
    to_start_time: str | None = Query(
        None, description="Filter to start time (ISO 8601)"
    ),
    version: str | None = Query(None, description="Filter by version"),
    environment: str | None = Query(
        None, description="Filter by environment (e.g. development, production, default)"
    ),
) -> dict:
    """Liste Observations mit optionalen Filtern (v2 API).

    Observations sind einzelne Operationen innerhalb eines Traces:
    - GENERATION: LLM-Aufrufe mit Input/Output
    - SPAN: Zeitabschnitte für Operationen
    - EVENT: Einzelne Events/Logs

    Returns:
        data: Liste von Observation-Objekten
        meta: Pagination-Metadaten
    """
    try:
        client = get_langfuse_client()
        result = await client.list_observations(
            page=page,
            limit=limit,
            trace_id=trace_id,
            name=name,
            type=type,
            user_id=user_id,
            from_start_time=from_start_time,
            to_start_time=to_start_time,
            version=version,
            environment=environment,
        )
        return dict(result)
    except LangfuseClientError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=e.message)


@app.get("/get_observation")
async def get_observation(
    observation_id: str = Query(..., description="The observation ID to retrieve"),
) -> dict:
    """Hole eine Observation anhand ihrer ID.

    Returns:
        Observation-Objekt mit model, input, output, usage, metadata
    """
    try:
        client = get_langfuse_client()
        result = await client.get_observation(observation_id)
        return dict(result)
    except LangfuseClientError as e:
        raise HTTPException(status_code=e.status_code or 500, detail=e.message)


# ========== Initialize MCP ==========

mcp = FastApiMCP(
    app,
    headers=[
        "X-Session-ID",
        "Mcp-Session-Id",
        "X-Auth-Token",
    ],
    description=MCP_DESCRIPTION,
    describe_all_responses=True,
    describe_full_response_schema=False,
    exclude_operations=[
        "health_check_health_get",
        "ready_check_ready_get",
    ],
)

mcp.mount_http()
