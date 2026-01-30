"""TypedDict schemas for Langfuse API responses."""

from typing import Any, TypedDict


class Score(TypedDict, total=False):
    """Langfuse Score object."""

    id: str
    name: str
    value: float | None
    stringValue: str | None
    traceId: str
    observationId: str | None
    timestamp: str
    source: str
    dataType: str
    comment: str | None
    authorUserId: str | None
    configId: str | None
    queueId: str | None
    createdAt: str
    updatedAt: str


class ScoreListResponse(TypedDict):
    """Response from GET /api/public/scores."""

    data: list[Score]
    meta: dict[str, Any]


class TraceUsage(TypedDict, total=False):
    """Usage statistics for a trace."""

    input: int
    output: int
    total: int


class Trace(TypedDict, total=False):
    """Langfuse Trace object."""

    id: str
    name: str | None
    timestamp: str
    userId: str | None
    sessionId: str | None
    release: str | None
    version: str | None
    input: Any
    output: Any
    metadata: dict[str, Any] | None
    tags: list[str]
    public: bool
    latency: float | None
    totalCost: float | None
    level: str
    observations: list[dict[str, Any]]
    scores: list[Score]
    htmlPath: str
    projectId: str


class TraceListResponse(TypedDict):
    """Response from GET /api/public/traces."""

    data: list[Trace]
    meta: dict[str, Any]


class DatasetItem(TypedDict, total=False):
    """Langfuse Dataset Item object."""

    id: str
    input: Any
    expectedOutput: Any
    metadata: dict[str, Any] | None
    sourceTraceId: str | None
    sourceObservationId: str | None
    status: str
    createdAt: str
    updatedAt: str


class Dataset(TypedDict, total=False):
    """Langfuse Dataset object."""

    id: str
    name: str
    description: str | None
    metadata: dict[str, Any] | None
    projectId: str
    createdAt: str
    updatedAt: str
    items: list[DatasetItem]


class DatasetListResponse(TypedDict):
    """Response from GET /api/public/v2/datasets."""

    data: list[Dataset]
    meta: dict[str, Any]


class DatasetRunItem(TypedDict, total=False):
    """Langfuse Dataset Run Item object."""

    id: str
    datasetItemId: str
    traceId: str
    observationId: str | None
    createdAt: str
    updatedAt: str


class DatasetRun(TypedDict, total=False):
    """Langfuse Dataset Run object."""

    id: str
    name: str
    description: str | None
    metadata: dict[str, Any] | None
    datasetId: str
    datasetName: str
    createdAt: str
    updatedAt: str


class DatasetRunListResponse(TypedDict):
    """Response from GET /api/public/datasets/{name}/runs."""

    data: list[DatasetRun]
    meta: dict[str, Any]


class Session(TypedDict, total=False):
    """Langfuse Session object."""

    id: str
    createdAt: str
    projectId: str
    traces: list[Trace]


class SessionListResponse(TypedDict):
    """Response from GET /api/public/sessions."""

    data: list[Session]
    meta: dict[str, Any]


class ObservationUsage(TypedDict, total=False):
    """Usage statistics for an observation."""

    input: int
    output: int
    total: int
    inputCost: float
    outputCost: float
    totalCost: float
    unit: str


class Observation(TypedDict, total=False):
    """Langfuse Observation object."""

    id: str
    traceId: str
    name: str | None
    type: str
    startTime: str
    endTime: str | None
    completionStartTime: str | None
    model: str | None
    modelParameters: dict[str, Any] | None
    input: Any
    output: Any
    metadata: dict[str, Any] | None
    level: str
    statusMessage: str | None
    parentObservationId: str | None
    promptId: str | None
    promptName: str | None
    promptVersion: int | None
    usage: ObservationUsage | None
    version: str | None
    createdAt: str
    updatedAt: str
    projectId: str


class ObservationListResponse(TypedDict):
    """Response from GET /api/public/v2/observations."""

    data: list[Observation]
    meta: dict[str, Any]
