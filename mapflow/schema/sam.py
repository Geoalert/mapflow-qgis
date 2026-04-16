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
    text_prompt: Optional[str] = None


@dataclass
class SessionCreateRequest(Serializable):
    processing_id: str
    prompt_id: str


@dataclass
class InferenceCreateRequest(Serializable):
    """POST /inference — creates a new session + first inference."""
    processing_id: str
    prompt_id: str
    geometry: dict  # GeoJSON
    confidence_threshold: Optional[float] = None


@dataclass
class SessionInferenceCreateRequest(Serializable):
    """POST /sessions/{id}/inferences — add inference to existing session."""
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
    raw_raster_uri: Optional[str] = None
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
    text_prompt: Optional[str] = None
    confidence_threshold: Optional[float] = None
    inferences: Optional[List[dict]] = None
    vector_layer: Optional[VectorLayerJson] = None

    def __post_init__(self):
        if self.inferences is None:
            self.inferences = []
        self.inferences = [InferenceStatusSummary.from_dict(i) for i in self.inferences]
        if self.vector_layer:
            self.vector_layer = VectorLayerJson.from_dict(self.vector_layer)

    @classmethod
    def from_dict(cls, params_dict: dict):
        # Backend may return either text_prompt or textPrompt; normalize for UI.
        normalized = dict(params_dict)
        if "text_prompt" not in normalized and "textPrompt" in normalized:
            normalized["text_prompt"] = normalized.get("textPrompt")
        return super().from_dict(normalized)

@dataclass
class SessionPromptsResponse(SkipDataClass):
    """GET /sessions/{id}/prompts — frozen prompt snapshot."""
    text_prompt: Optional[dict] = None
    spatial_prompts: Optional[List[dict]] = None

    def __post_init__(self):
        if self.spatial_prompts is None:
            self.spatial_prompts = []
        self.spatial_prompts = [SpatialPromptResponse.from_dict(p) for p in self.spatial_prompts]


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
