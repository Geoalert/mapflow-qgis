"""SAM Interactive backend request/response schemas.

Follows existing conventions:
- Request schemas inherit Serializable (as_json/as_dict)
- Response schemas inherit SkipDataClass (from_dict, tolerates unknown fields)
"""
from dataclasses import dataclass, field
from typing import Optional, List, Union, Mapping, Any

from ..schema.processing import PostSourceSchema, PostProviderSchema
from .base import Serializable, SkipDataClass


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------

@dataclass
class ProcessingCreateRequest(Serializable):
    name: str
    projectId: str
    geometry: Mapping[str, Any]  # GeoJSON
    params: Union[PostSourceSchema, PostProviderSchema]
    promptId: Optional[str] = None
    text_prompt: Optional[str] = None
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
    text_prompt: Optional[str] = None


@dataclass
class SessionCreateRequest(Serializable):
    processing_id: str
    prompt_id: str


@dataclass
class InferenceCreateRequest(Serializable):
    """POST /inference — creates a new session + first inference."""
    prompt_id: str
    workflow_id: str
    geometry: dict  # GeoJSON


@dataclass
class SessionInferenceCreateRequest(Serializable):
    """POST /sessions/{id}/inferences — add inference to existing session."""
    workflow_id: str
    geometry: dict  # GeoJSON


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
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    sessions: Optional[List[str]] = None

    def __post_init__(self):
        if self.sessions is None:
            self.sessions = []


@dataclass
class ProcessingListResponse(SkipDataClass):
    total: int = 0
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
    text_prompt_id: Optional[str] = None
    text_prompt: Optional[str] = None


@dataclass
class SpatialPromptResponse(SkipDataClass):
    """Shared schema for both point_prompts and bbox_prompts."""
    id: str = ""
    processing_id: str = ""
    embedding_uri: Optional[str] = None
    geometry: Optional[dict] = None
    positive: bool = True


@dataclass
class PromptDetailResponse(SkipDataClass):
    id: str = ""
    text_prompt_id: Optional[str] = None
    text_prompt: Optional[str] = None
    point_prompts: Optional[List[dict]] = None
    bbox_prompts: Optional[List[dict]] = None

    def __post_init__(self):
        if self.point_prompts is None:
            self.point_prompts = []
        if self.bbox_prompts is None:
            self.bbox_prompts = []
        self.point_prompts = [SpatialPromptResponse.from_dict(p) for p in self.point_prompts]
        self.bbox_prompts = [SpatialPromptResponse.from_dict(p) for p in self.bbox_prompts]


@dataclass
class PromptListResponse(SkipDataClass):
    total: int = 0
    limit: int = 20
    offset: int = 0
    items: Optional[List[dict]] = None

    def __post_init__(self):
        if self.items is None:
            self.items = []
        self.items = [PromptResponse.from_dict(i) for i in self.items]


@dataclass
class InferenceStatusSummary(SkipDataClass):
    id: str = ""
    status: str = ""

@dataclass
class VectorLayerJson(SkipDataClass):
    id: str
    tile_url: str
    tile_json_url: str

@dataclass
class SessionResponse(SkipDataClass):
    id: str = ""
    processing_id: str = ""
    name: Optional[str] = None
    inferences: Optional[List[dict]] = None
    vector_layer: Optional[VectorLayerJson] = None

    def __post_init__(self):
        if self.inferences is None:
            self.inferences = []
        self.inferences = [InferenceStatusSummary.from_dict(i) for i in self.inferences]


@dataclass
class SessionPromptsResponse(SkipDataClass):
    """GET /sessions/{id}/prompts — frozen prompt snapshot."""
    text_prompt: Optional[dict] = None
    point_prompts: Optional[List[dict]] = None
    bbox_prompts: Optional[List[dict]] = None

    def __post_init__(self):
        if self.point_prompts is None:
            self.point_prompts = []
        if self.bbox_prompts is None:
            self.bbox_prompts = []
        self.point_prompts = [SpatialPromptResponse.from_dict(p) for p in self.point_prompts]
        self.bbox_prompts = [SpatialPromptResponse.from_dict(p) for p in self.bbox_prompts]


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
    id: str = ""
    session_id: str = ""
    status: str = ""
    geometry: Optional[dict] = None
    we_workflow_id: Optional[int] = None
    we_workflow_status: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass
class ResultResponse(SkipDataClass):
    id: str = ""
    geometry: Optional[dict] = None
    layer_id: Optional[str] = None
    processing_id: Optional[str] = None
    session_id: Optional[str] = None
