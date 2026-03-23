"""Langfuse API Client wrapper."""

import logging
from typing import Any

import httpx

from ..config import Settings, get_settings
from .typing import (
    Dataset,
    DatasetListResponse,
    DatasetRunListResponse,
    Observation,
    ObservationListResponse,
    Score,
    ScoreListResponse,
    Session,
    SessionListResponse,
    Trace,
    TraceListResponse,
)

logger = logging.getLogger(__name__)


class LangfuseClientError(Exception):
    """Custom exception for Langfuse API errors."""

    def __init__(self, message: str, status_code: int | None = None):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class LangfuseClient:
    """Async client for Langfuse API."""

    def __init__(self, settings: Settings | None = None):
        """Initialize Langfuse client.

        Args:
            settings: Application settings. If None, loads from environment.
        """
        self.settings = settings or get_settings()
        self._client: httpx.AsyncClient | None = None

    @property
    def base_url(self) -> str:
        """Return the base URL for Langfuse API."""
        return self.settings.langfuse_base_url

    @property
    def auth(self) -> tuple[str, str]:
        """Return Basic Auth credentials (public_key, secret_key)."""
        return (self.settings.langfuse_public_key, self.settings.langfuse_secret_key)

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                auth=self.auth,
                verify=self.settings.langfuse_verify_ssl,
                timeout=httpx.Timeout(30.0, connect=10.0),
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make an API request to Langfuse.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            params: Query parameters

        Returns:
            JSON response as dictionary

        Raises:
            LangfuseClientError: If the request fails
        """
        client = await self._get_client()

        # Filter out None values from params
        if params:
            params = {k: v for k, v in params.items() if v is not None}

        try:
            response = await client.request(method, endpoint, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            error_detail = ""
            try:
                error_detail = e.response.text
            except Exception:
                pass
            logger.error(
                f"Langfuse API error: {e.response.status_code} - {error_detail}"
            )
            raise LangfuseClientError(
                f"API request failed: {error_detail or str(e)}",
                status_code=e.response.status_code,
            ) from e
        except httpx.RequestError as e:
            logger.error(f"Langfuse connection error: {e}")
            raise LangfuseClientError(f"Connection error: {e}") from e

    # ========== Scores API ==========

    async def list_scores(
        self,
        page: int | None = None,
        limit: int | None = None,
        trace_id: str | None = None,
        user_id: str | None = None,
        name: str | None = None,
        data_type: str | None = None,
        config_id: str | None = None,
        from_timestamp: str | None = None,
        to_timestamp: str | None = None,
        source: str | None = None,
        operator: str | None = None,
        value: float | None = None,
        environment: str | None = None,
    ) -> ScoreListResponse:
        """List scores with optional filters.

        Args:
            page: Page number (1-indexed)
            limit: Number of items per page (default 50, max 100)
            trace_id: Filter by trace ID
            user_id: Filter by user ID
            name: Filter by score name
            data_type: Filter by data type (NUMERIC, CATEGORICAL, BOOLEAN)
            config_id: Filter by config ID
            from_timestamp: Filter from timestamp (ISO 8601)
            to_timestamp: Filter to timestamp (ISO 8601)
            source: Filter by source (API, ANNOTATION, EVAL)
            operator: Comparison operator for value filter
            value: Value to filter by (requires operator)

        Returns:
            ScoreListResponse with data and meta
        """
        params = {
            "page": page,
            "limit": limit,
            "traceId": trace_id,
            "userId": user_id,
            "name": name,
            "dataType": data_type,
            "configId": config_id,
            "fromTimestamp": from_timestamp,
            "toTimestamp": to_timestamp,
            "source": source,
            "operator": operator,
            "value": value,
            "environment": environment,
        }
        result = await self._request("GET", "/api/public/scores", params=params)
        return ScoreListResponse(data=result.get("data", []), meta=result.get("meta", {}))

    async def get_score(self, score_id: str) -> Score:
        """Get a single score by ID.

        Args:
            score_id: The score ID

        Returns:
            Score object
        """
        result = await self._request("GET", f"/api/public/scores/{score_id}")
        return Score(**result)

    # ========== Traces API ==========

    async def list_traces(
        self,
        page: int | None = None,
        limit: int | None = None,
        user_id: str | None = None,
        session_id: str | None = None,
        name: str | None = None,
        from_timestamp: str | None = None,
        to_timestamp: str | None = None,
        order_by: str | None = None,
        tags: list[str] | None = None,
        version: str | None = None,
        release: str | None = None,
        environment: str | None = None,
    ) -> TraceListResponse:
        """List traces with optional filters.

        Args:
            page: Page number (1-indexed)
            limit: Number of items per page (default 50, max 100)
            user_id: Filter by user ID
            session_id: Filter by session ID
            name: Filter by trace name
            from_timestamp: Filter from timestamp (ISO 8601)
            to_timestamp: Filter to timestamp (ISO 8601)
            order_by: Order by field (e.g., "timestamp")
            tags: Filter by tags
            version: Filter by version
            release: Filter by release

        Returns:
            TraceListResponse with data and meta
        """
        params: dict[str, Any] = {
            "page": page,
            "limit": limit,
            "userId": user_id,
            "sessionId": session_id,
            "name": name,
            "fromTimestamp": from_timestamp,
            "toTimestamp": to_timestamp,
            "orderBy": order_by,
            "version": version,
            "release": release,
            "environment": environment,
        }
        # Handle tags as repeated query params
        if tags:
            params["tags"] = tags

        result = await self._request("GET", "/api/public/traces", params=params)
        return TraceListResponse(data=result.get("data", []), meta=result.get("meta", {}))

    async def get_trace(self, trace_id: str) -> Trace:
        """Get a single trace by ID.

        Args:
            trace_id: The trace ID

        Returns:
            Trace object with observations and scores
        """
        result = await self._request("GET", f"/api/public/traces/{trace_id}")
        return Trace(**result)

    # ========== Datasets API ==========

    async def list_datasets(
        self,
        page: int | None = None,
        limit: int | None = None,
    ) -> DatasetListResponse:
        """List datasets with pagination.

        Args:
            page: Page number (1-indexed)
            limit: Number of items per page (default 50, max 100)

        Returns:
            DatasetListResponse with data and meta
        """
        params = {
            "page": page,
            "limit": limit,
        }
        result = await self._request("GET", "/api/public/v2/datasets", params=params)
        return DatasetListResponse(data=result.get("data", []), meta=result.get("meta", {}))

    async def get_dataset(self, dataset_name: str) -> Dataset:
        """Get a dataset by name.

        Args:
            dataset_name: The dataset name

        Returns:
            Dataset object
        """
        result = await self._request("GET", f"/api/public/v2/datasets/{dataset_name}")
        return Dataset(**result)

    async def list_dataset_runs(
        self,
        dataset_name: str,
        page: int | None = None,
        limit: int | None = None,
    ) -> DatasetRunListResponse:
        """List runs for a dataset.

        Args:
            dataset_name: The dataset name
            page: Page number (1-indexed)
            limit: Number of items per page (default 50, max 100)

        Returns:
            DatasetRunListResponse with data and meta
        """
        params = {
            "page": page,
            "limit": limit,
        }
        result = await self._request(
            "GET", f"/api/public/datasets/{dataset_name}/runs", params=params
        )
        return DatasetRunListResponse(data=result.get("data", []), meta=result.get("meta", {}))

    # ========== Sessions API ==========

    async def list_sessions(
        self,
        page: int | None = None,
        limit: int | None = None,
        from_timestamp: str | None = None,
        to_timestamp: str | None = None,
        environment: str | None = None,
    ) -> SessionListResponse:
        """List sessions with optional filters.

        Args:
            page: Page number (1-indexed)
            limit: Number of items per page (default 50, max 100)
            from_timestamp: Filter from timestamp (ISO 8601)
            to_timestamp: Filter to timestamp (ISO 8601)

        Returns:
            SessionListResponse with data and meta
        """
        params = {
            "page": page,
            "limit": limit,
            "fromTimestamp": from_timestamp,
            "toTimestamp": to_timestamp,
            "environment": environment,
        }
        result = await self._request("GET", "/api/public/sessions", params=params)
        return SessionListResponse(data=result.get("data", []), meta=result.get("meta", {}))

    async def get_session(self, session_id: str) -> Session:
        """Get a session by ID.

        Args:
            session_id: The session ID

        Returns:
            Session object with traces
        """
        result = await self._request("GET", f"/api/public/sessions/{session_id}")
        return Session(**result)

    # ========== Observations API ==========

    async def list_observations(
        self,
        page: int | None = None,
        limit: int | None = None,
        trace_id: str | None = None,
        name: str | None = None,
        type: str | None = None,
        user_id: str | None = None,
        from_start_time: str | None = None,
        to_start_time: str | None = None,
        parent_observation_id: str | None = None,
        version: str | None = None,
        environment: str | None = None,
    ) -> ObservationListResponse:
        """List observations (v2 API) with optional filters.

        Args:
            page: Page number (1-indexed)
            limit: Number of items per page (default 50, max 100)
            trace_id: Filter by trace ID
            name: Filter by observation name
            type: Filter by type (GENERATION, SPAN, EVENT)
            user_id: Filter by user ID
            from_start_time: Filter from start time (ISO 8601)
            to_start_time: Filter to start time (ISO 8601)
            parent_observation_id: Filter by parent observation ID
            version: Filter by version

        Returns:
            ObservationListResponse with data and meta
        """
        params = {
            "page": page,
            "limit": limit,
            "traceId": trace_id,
            "name": name,
            "type": type,
            "userId": user_id,
            "fromStartTime": from_start_time,
            "toStartTime": to_start_time,
            "parentObservationId": parent_observation_id,
            "version": version,
            "environment": environment,
        }
        result = await self._request("GET", "/api/public/v2/observations", params=params)
        return ObservationListResponse(data=result.get("data", []), meta=result.get("meta", {}))

    async def get_observation(self, observation_id: str) -> Observation:
        """Get an observation by ID.

        Args:
            observation_id: The observation ID

        Returns:
            Observation object
        """
        result = await self._request("GET", f"/api/public/observations/{observation_id}")
        return Observation(**result)
