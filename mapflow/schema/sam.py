"""SAM Interactive backend request/response schemas.

Follows existing conventions:
- Request schemas inherit Serializable (as_json/as_dict)
- Response schemas inherit SkipDataClass (from_dict, tolerates unknown fields)
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Union, Mapping, Any, Tuple

from ..schema.processing import PostSourceSchema, PostProviderSchema
from .base import Serializable, SkipDataClass


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


def parse_confidence_threshold(
    raw_value: Optional[Union[str, float, int]]
) -> Tuple[Optional[float], Optional[str]]:
    """Parse an optional SAM confidence threshold from UI or request input."""
    if raw_value is None:
        return None, None

    if isinstance(raw_value, str):
        raw_value = raw_value.strip()
        if not raw_value:
            return None, None

    try:
        confidence_threshold = float(raw_value)
    except (TypeError, ValueError):
        return None, "Confidence threshold must be a number between 0 and 1."

    if confidence_threshold < 0 or confidence_threshold > 1:
        return None, "Confidence threshold must be between 0 and 1."

    return confidence_threshold, None

@dataclass
class ProcessingCreateRequest(Serializable):
    name: str
    projectId: str
    geometry: Mapping[str, Any]  # GeoJSON
    params: Union[PostSourceSchema, PostProviderSchema]
    promptId: Optional[str] = None
    text_prompt: Optional[str] = None
    confidence_threshold: Optional[float] = None
    description: Optional[str] = None
    meta: Optional[dict] = None


@dataclass
class PaginationRequest(Serializable):
    """Query parameters for paginated list endpoints."""
    filter: Optional[str] = None
    limit: int = 20
    offset: int = 0


@dataclass
class PointPromptRequest(Serializable):
    processing_id: str
    geometry: dict  # GeoJSON Point
    positive: bool = True


@dataclass
class BboxPromptRequest(Serializable):
    processing_id: str
    geometry: dict  # GeoJSON Polygon
    positive: bool = True


@dataclass
class PromptCreateRequest(Serializable):
    name: Optional[str] = None
    text_prompt: Optional[str] = None


@dataclass
class PromptCopyRequest(Serializable):
    """Body for POST /prompts/{id}/copy.

    Both fields optional. Backend defaults `name` to `"<source.name> (copy)"`
    when omitted; `text_prompt` omitted/null/empty reuses the source prompt's
    `text_prompt_id` by FK reuse.
    """
    name: Optional[str] = None
    text_prompt: Optional[str] = None


@dataclass
class InferenceCreateRequest(Serializable):
    """POST /inference — creates a new session and dispatches the first
    inference batch (one Inference per workflow intersecting the AOI)."""
    processing_id: str
    prompt_id: str
    geometry: dict  # GeoJSON
    confidence_threshold: Optional[float] = None


@dataclass
class SessionInferenceCreateRequest(Serializable):
    """POST /sessions/{id}/inferences — adds a new inference batch to an
    existing session (one Inference per workflow intersecting the AOI)."""
    geometry: dict  # GeoJSON


@dataclass
class SessionNameUpdateRequest(Serializable):
    name: str


@dataclass
class PromptUpdateRequest(Serializable):
    name: Optional[str] = None
    text_prompt: Optional[str] = None


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class GeometryType(Enum):
    POINT = "point"
    BBOX = "bbox"


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

@dataclass
class MapflowProcessingResponse(SkipDataClass):
    id: str = ""
    name: str = ""
    status: str = ""
    percentCompleted: int = 0
    cost: Optional[float] = None
    created: Optional[str] = None


@dataclass
class ProcessingSummaryResponse(SkipDataClass):
    id: str = ""
    name: str = ""
    status: str = ""
    embedding_uri: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass
class ProcessingDetailResponse(SkipDataClass):
    id: str = ""
    name: str = ""
    status: str = ""
    embedding_uri: Optional[str] = None
    params: Optional[dict] = None
    text_prompt: Optional[str] = None
    confidence_threshold: Optional[float] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    sessions: Optional[List[str]] = None

    def __post_init__(self):
        if self.sessions is None:
            self.sessions = []


@dataclass
class ProcessingListResponse(SkipDataClass):
    # Backend dropped `total` to skip the COUNT(*) on large tables; pages
    # advertise whether more rows exist via `has_more` and the client
    # paginates by `offset + limit` regardless of the actual page size.
    # Note: a page may legitimately come back with fewer than `limit` items
    # even when has_more=True (rows archived during a per-page sync).
    has_more: bool = False
    limit: int = 20
    offset: int = 0
    items: Optional[List[dict]] = None

    def __post_init__(self):
        if self.items is None:
            self.items = []
        self.items = [ProcessingSummaryResponse.from_dict(i) for i in self.items]


@dataclass
class WorkflowSummaryResponse(SkipDataClass):
    id: str = ""
    external_id: Optional[int] = None
    geometry: Optional[dict] = None
    raw_raster_uri: Optional[str] = None
    embedding_uri: Optional[str] = None
    processing_id: str = ""
    status: str = ""


@dataclass
class PromptResponse(SkipDataClass):
    id: str = ""
    name: Optional[str] = None
    text_prompt_id: Optional[str] = None
    text_prompt: Optional[str] = None

    def __post_init__(self):
        if self.name is None:
            self.name = self.text_prompt


@dataclass
class SpatialPromptResponse(SkipDataClass):
    """Unified spatial prompt — distinguished by geometry_type."""
    id: str = ""
    geometry_type: str = ""  # "point" or "bbox", see GeometryType enum
    processing_id: str = ""
    embedding_uri: Optional[str] = None
    # `raster_url` is an https link to the GeoTIFF preview crop the prompt
    # was created from; the backend serves it with the same auth as the
    # rest of /sam-interactive. None when no crop is available (legacy rows
    # created before the preview pipeline existed).
    raster_url: Optional[str] = None
    geometry: Optional[dict] = None
    positive: bool = True


@dataclass
class PromptDetailResponse(SkipDataClass):
    id: str = ""
    text_prompt_id: Optional[str] = None
    text_prompt: Optional[str] = None
    spatial_prompts: Optional[List[dict]] = None

    def __post_init__(self):
        if self.spatial_prompts is None:
            self.spatial_prompts = []
        self.spatial_prompts = [SpatialPromptResponse.from_dict(p) for p in self.spatial_prompts]


@dataclass
class PromptListResponse(SkipDataClass):
    # See ProcessingListResponse — same has_more migration applied. For
    # /prompts/page the backend always returns full pages up to `limit`.
    has_more: bool = False
    limit: int = 20
    offset: int = 0
    items: Optional[List[dict]] = None

    def __post_init__(self):
        if self.items is None:
            self.items = []
        self.items = [PromptResponse.from_dict(i) for i in self.items]


@dataclass
class InferenceStatusSummary(SkipDataClass):
    """Lightweight per-inference summary inside SessionResponse.inferences.

    Returned by POST/GET /sessions/* and POST /inference. WE workflow id/
    status are deliberately not exposed — the abstract `status` is all the
    user-facing UI cares about.
    """
    id: str = ""
    status: str = ""
    geometry: Optional[dict] = None  # per-workflow clipped AOI
    created_at: Optional[str] = None

@dataclass
class VectorLayerJson(SkipDataClass):
    id: str
    tile_url: str
    tile_json_url: str


@dataclass
class TextPromptSummary(SkipDataClass):
    """Minimal text prompt info embedded in the frozen session snapshot."""
    id: str = ""
    text: str = ""


@dataclass
class SessionResponse(SkipDataClass):
    """Full session detail: metadata + frozen prompt snapshot + inferences.

    The frozen prompt snapshot (`text_prompt` + `spatial_prompts`) is
    embedded directly here — `GET /sessions/{id}/prompts` was retired.
    Backend bulk-refreshes WE statuses for non-terminal inferences before
    responding, so a single GET is always the freshest view.
    """
    id: str = ""
    processing_id: str = ""
    name: Optional[str] = None
    confidence_threshold: Optional[float] = None
    text_prompt: Optional[TextPromptSummary] = None
    spatial_prompts: Optional[List[SpatialPromptResponse]] = None
    inferences: Optional[List[InferenceStatusSummary]] = None
    vector_layer: Optional[VectorLayerJson] = None
    # Aggregates exposed by the sessions list endpoint (SessionListItem).
    # Defaulted None on the detail endpoint, where they're not meaningful.
    inferences_total: Optional[int] = None
    inferences_done: Optional[int] = None

    def __post_init__(self):
        if self.inferences is None:
            self.inferences = []
        self.inferences = [InferenceStatusSummary.from_dict(i) for i in self.inferences]
        if self.spatial_prompts:
            self.spatial_prompts = [SpatialPromptResponse.from_dict(p) for p in self.spatial_prompts]
        if self.vector_layer:
            self.vector_layer = VectorLayerJson.from_dict(self.vector_layer)
        if self.text_prompt and isinstance(self.text_prompt, dict):
            self.text_prompt = TextPromptSummary.from_dict(self.text_prompt)


@dataclass
class SessionListResponse(SkipDataClass):
    total: int = 0
    limit: int = 20
    offset: int = 0
    items: Optional[List[dict]] = None

    def __post_init__(self):
        if self.items is None:
            self.items = []
        self.items = [SessionResponse.from_dict(i) for i in self.items]


@dataclass
class InferenceResponse(SkipDataClass):
    """Full inference detail, returned by GET /inference/{id}.

    Note: POST /inference and POST /sessions/{id}/inferences return
    SessionResponse, not InferenceResponse — a single user request now
    yields N inferences, all bundled inside the session payload.
    """
    id: str = ""
    session_id: str = ""
    status: str = ""
    geometry: Optional[dict] = None
    we_workflow_id: Optional[int] = None
    we_workflow_status: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
