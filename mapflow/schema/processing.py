from enum import Enum

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Optional, Mapping, Any, Union, Iterable, List
from uuid import UUID, uuid4

from .base import SkipDataClass, Serializable, parse_api_datetime_utc
from .status import ProcessingStatus, ProcessingReviewStatus
from .layer import RasterLayer, VectorLayer
from .workflow_def import WorkflowDef
from ..entity.provider.provider import SourceType
from ..errors import ErrorMessage
from ..functional.geometry import geojson_feature_area_sqkm, make_distance_calculator

@dataclass
class PostSourceSchema(Serializable, SkipDataClass):
    url: str
    source_type: str
    projection: Optional[str] = None
    raster_login: Optional[str] = None
    raster_password: Optional[str] = None
    zoom: Optional[str] = None    


@dataclass
class BlockOption(Serializable, SkipDataClass):
    name: str
    displayName: str
    enabled: bool


@dataclass
class PostProviderSchema(Serializable, SkipDataClass):
    # Data provider name
    data_provider: str
    url: Optional[str] = None
    zoom: Optional[str] = None


@dataclass
class PostProcessingSchema(Serializable):
    name: str
    wdId: Optional[str]
    params: Union[PostSourceSchema, PostProviderSchema]
    blocks: Optional[Iterable[BlockOption]]
    geometry: Mapping[str, Any]
    meta: Optional[Mapping[str, Any]]
    projectId: Optional[str] = None

    def __post_init__(self):
        if self.blocks:
            self.blocks = [BlockOption(**item) for item in self.blocks]
        else:
            self.blocks = []


@dataclass
class UpdateProcessingSchema(Serializable):
    name: str
    description: str


@dataclass
class DataProviderSchema(Serializable):
    providerName: str
    zoom: str


@dataclass
class DataProviderParams(Serializable):
    dataProvider: DataProviderSchema


@dataclass
class MyImagerySchema(Serializable):
    imageIds: List[str]
    mosaicId: str


@dataclass
class MyImageryParams(Serializable):
    myImagery: MyImagerySchema


@dataclass
class ImagerySearchSchema(Serializable):
    dataProvider: str
    imageIds: List[str]
    zoom: int
    searchId: Optional[str] = None


@dataclass
class ImagerySearchParams(Serializable):
    imagerySearch: ImagerySearchSchema


@dataclass
class UserDefinedSchema(Serializable):
    sourceType: SourceType
    url: str
    zoom: Optional[int]
    crs: Optional[str]
    rasterLogin: Optional[str]
    rasterPassword: Optional[str]


@dataclass
class UserDefinedParams(Serializable):
    userDefined: UserDefinedSchema


@dataclass
class ProcessingParams(Serializable, SkipDataClass):
    sourceParams: Union[DataProviderParams,
                        MyImageryParams,
                        ImagerySearchParams,
                        UserDefinedParams]
    
    @classmethod
    def from_dict(cls, params_dict: Optional[dict]):
        if not params_dict:
            return None
        # The template `/processings` endpoint returns legacy flat params
        # (e.g. {"url", "zoom", "data_provider"}) instead of the v2 {"sourceParams": {...}}
        # shape. Without sourceParams there is nothing to resolve — return None rather
        # than raise (a raise here would drop the whole processing from the list).
        source_params = params_dict.get("sourceParams")
        if not isinstance(source_params, dict):
            return None

        if source_params.get("dataProvider"):
            source_params = DataProviderParams(DataProviderSchema(**source_params.get("dataProvider")))
        elif source_params.get("myImagery"):
            source_params = MyImageryParams(MyImagerySchema(**source_params.get("myImagery")))
        elif source_params.get("imagerySearch"):
            #! print (str(source_params))
            source_params = ImagerySearchParams(ImagerySearchSchema(**source_params.get("imagerySearch")))
        elif source_params.get("userDefined"):
            source_params = UserDefinedParams(UserDefinedSchema(**source_params.get("userDefined")))
        else:
            source_params = "Unidentified"
        return ProcessingParams(sourceParams=source_params)


@dataclass
class PostProcessingSchemaV2(Serializable):
    name: str
    description: Optional[str]
    projectId: str
    wdId: Optional[str]
    geometry: Mapping[str, Any]
    params: ProcessingParams
    meta: Optional[Mapping[str, Any]]
    blocks: Optional[Iterable[BlockOption]]


def _parse_iso_datetime(dt_str: str) -> datetime:
    """Parse ISO 8601 datetime strings with or without microseconds."""
    return parse_api_datetime_utc(dt_str)


@dataclass
class SearchParams(Serializable, SkipDataClass):
    aoiDetails: Optional[Mapping[str, Any]] = None
    aoi: Optional[Mapping[str, Any]] = None
    acquisitionDateFrom: Optional[str] = None
    acquisitionDateTo: Optional[str] = None
    minResolution: Optional[float] = None
    maxResolution: Optional[float] = None
    maxCloudCover: Optional[float] = None
    minOffNadirAngle: Optional[float] = None
    maxOffNadirAngle: Optional[float] = None
    minAoiIntersectionPercent: Optional[float] = None
    maxAoiIntersectionPercent: Optional[float] = None
    returnErrors: Optional[bool] = None
    limit: Optional[int] = None
    offset: Optional[int] = None
    hideUnavailable: Optional[bool] = None
    dataProviders: Optional[List[str]] = None
    productTypes: Optional[List[str]] = None


@dataclass
class ProcessingTemplateDTO(Serializable, SkipDataClass):
    id: UUID
    name: str
    status: str
    createdAt: datetime
    userId: UUID
    searchParams: SearchParams
    projectId: UUID
    activeUntil: datetime
    processingParams: Optional[Mapping[str, Any]] = None
    lastCheckedAt: Optional[datetime] = None
    newImagesCount: Optional[int] = None
    isActive: bool = False
    isArchived: bool = False
    maxAoiIntersectionPercent: Optional[float] = None
    area: Optional[float] = None  # AOI area in square metres, as reported by the backend

    def __post_init__(self):
        self.createdAt = _parse_iso_datetime(self.createdAt)
        if self.lastCheckedAt:
            self.lastCheckedAt = _parse_iso_datetime(self.lastCheckedAt)
        self.activeUntil = _parse_iso_datetime(self.activeUntil)
        if isinstance(self.searchParams, dict):
            self.searchParams = SearchParams.from_dict(self.searchParams)

    @property
    def is_template(self) -> bool:
        return True

    def _aoi_features(self):
        """Return template AOI features from either aoiDetails or aoi shape."""
        if isinstance(self.searchParams, SearchParams):
            aoi_details = self.searchParams.aoiDetails
            if aoi_details:
                return (aoi_details or {}).get("features", [])
            if self.searchParams.aoi:
                return [{
                    "type": "Feature",
                    "geometry": self.searchParams.aoi,
                    "properties": {},
                }]
            return []

        search_params = self.searchParams or {}
        aoi_details = search_params.get("aoiDetails", {})
        if aoi_details:
            return (aoi_details or {}).get("features", [])

        aoi = search_params.get("aoi")
        if aoi:
            return [{
                "type": "Feature",
                "geometry": aoi,
                "properties": {},
            }]
        return []

    @property
    def aoi_area(self) -> Optional[float]:
        """Total AOI area in sq km.

        Prefers the backend-provided ``area`` (square metres), which the project
        template list returns even though it omits ``searchParams``. Falls back to
        computing from ``searchParams.aoiDetails`` when ``area`` is absent.
        """
        if self.area is not None:
            try:
                return round(float(self.area) / 1e6, 4)
            except (TypeError, ValueError):
                pass
        try:
            features = self._aoi_features()
            if not features:
                return None
            calculator = make_distance_calculator()
            total = sum(geojson_feature_area_sqkm(f, calculator) for f in features)
            return round(total, 4) if total else None
        except Exception:
            return None

    @property
    def table_status(self) -> str:
        """Template status for the processings/templates list:
        - ``Searching`` while the initial (or a re-run) search is in progress;
        - ``Failed`` on error;
        - ``Created`` once ready but not yet checked (``lastCheckedAt`` is null);
        - ``Updated`` after the first daily check, with a ``(newImagesCount)`` tag when there
          are unseen images.
        """
        status = (self.status or "").upper()
        if status == "FAILED":
            return "Failed"
        if status == "SEARCHING":
            return "Searching"
        if not self.isActive:
            return "Inactive"
        if not self.lastCheckedAt:
            return "Created"
        if self.newImagesCount and self.newImagesCount > 0:
            return f"Updated ({self.newImagesCount})"
        return "Updated"

    def as_processing_table_dict(self):
        return {
            "name": self.name,
            "workflowDef": "Planned", #! Translate
            "status": self.table_status,
            "percentCompleted": "N/A",
            "aoiArea": self.aoi_area,
            "cost": None,
            "created": self.createdAt.astimezone().strftime('%Y-%m-%d %H:%M'),
            "reviewUntil": None,
            "id": self.id,
        }

    def aoi_dtos(self) -> "List[TemplateAoiDTO]":
        """Parse the template's AOIs (with names and linked processings) from aoiDetails."""
        return [TemplateAoiDTO.from_feature(f) for f in self._aoi_features()]


# Backend rejects AOI names longer than this; mirror the check client-side.
AOI_NAME_MAX_LENGTH = 64


@dataclass
class AoiProcessingLink(Serializable, SkipDataClass):
    """A processing launched for a template AOI (from aoiDetails feature properties).

    Carries enough to display the processing as a grouped row under its AOI and to draw
    its footprint on the map. For actions that need layers (load results), look the full
    processing up by ``processingId`` in the ``/processings`` list (``TemplateProcessingSchema``).
    """
    processingId: Optional[str] = None
    processingName: Optional[str] = None
    processingStatus: Optional[str] = None
    area: Optional[float] = None  # square metres, as reported by the backend
    projectId: Optional[str] = None
    geometry: Optional[Mapping[str, Any]] = None

    @property
    def is_aoi_processing(self) -> bool:
        return True

    @property
    def id(self) -> str:
        """Row id (matches ``as_processing_table_dict``); used for table selection restore."""
        return str(self.processingId) if self.processingId else ""

    @property
    def aoi_area(self) -> Optional[float]:
        if self.area is None:
            return None
        try:
            return round(float(self.area) / 1e6, 4)
        except (TypeError, ValueError):
            return None

    @property
    def display_status(self) -> str:
        raw = self.processingStatus or ""
        try:
            return ProcessingStatus(raw).display_value
        except (ValueError, KeyError):
            return raw

    def as_processing_table_dict(self):
        return {
            "name": self.processingName,
            "workflowDef": "",  # not provided by aoiDetails; grouped under its AOI
            "status": self.display_status,
            "percentCompleted": "N/A",
            "aoiArea": self.aoi_area,
            "cost": None,
            "created": "",
            "reviewUntil": None,
            "id": str(self.processingId) if self.processingId else "",
        }


@dataclass
class TemplateAoiDTO(Serializable, SkipDataClass):
    """One AOI of a template, parsed from an aoiDetails GeoJSON feature.

    Mirrors the backend ``TemplateAoiProperties`` (id, name, processings, hasNewImages).
    ``table_id`` is a stable-per-render key for the processings table: the real AOI id
    when present, otherwise a synthetic one (AOIs without ids cannot be renamed/deleted).
    """
    id: Optional[str] = None
    name: Optional[str] = None
    geometry: Optional[Mapping[str, Any]] = None
    processings: List[AoiProcessingLink] = field(default_factory=list)
    hasNewImages: bool = False
    table_id: str = ""

    def __post_init__(self):
        if not self.table_id:
            self.table_id = str(self.id) if self.id else f"aoi-{uuid4().hex}"

    @classmethod
    def from_feature(cls, feature: Mapping[str, Any]) -> "TemplateAoiDTO":
        feature = feature or {}
        props = feature.get("properties") or {}
        aoi_id = feature.get("id") or props.get("id")
        processings = [
            AoiProcessingLink.from_dict(p)
            for p in (props.get("processings") or [])
            if isinstance(p, dict)
        ]
        return cls(
            id=str(aoi_id) if aoi_id else None,
            name=props.get("name"),
            geometry=feature.get("geometry"),
            processings=processings,
            hasNewImages=bool(props.get("hasNewImages", False)),
        )

    @property
    def is_aoi(self) -> bool:
        return True

    @property
    def can_rename(self) -> bool:
        """Only AOIs with a persisted id can be renamed/deleted via the per-AOI endpoint."""
        return self.id is not None

    @property
    def display_name(self) -> str:
        return self.name if self.name else "(unnamed)"  #! Translate

    @property
    def aoi_area(self) -> Optional[float]:
        if not self.geometry:
            return None
        try:
            calculator = make_distance_calculator()
            total = geojson_feature_area_sqkm(
                {"type": "Feature", "geometry": self.geometry, "properties": {}},
                calculator,
            )
            return round(total, 4) if total else None
        except Exception:
            return None

    @property
    def table_status(self) -> str:
        """Aggregate status of the AOI's processings:
        - any in progress / awaiting → ``In progress (ok/total)``;
        - else any failed → ``Failed (ok/total)``;
        - else all ok → ``OK (total)``.
        """
        statuses = [(p.processingStatus or "").upper() for p in self.processings]
        total = len(statuses)
        if total == 0:
            return "—"
        ok = sum(1 for s in statuses if s == "OK")
        in_progress = sum(1 for s in statuses if s in ("IN_PROGRESS", "AWAITING"))
        failed = sum(1 for s in statuses if s == "FAILED")
        if in_progress:
            return f"In progress ({ok}/{total})"  #! Translate
        if failed:
            return f"Failed ({ok}/{total})"  #! Translate
        if ok == total:
            return f"OK ({total})"  #! Translate
        return f"OK ({ok}/{total})"  #! Translate

    def as_processing_table_dict(self):
        return {
            "name": self.display_name,
            "workflowDef": "AOI",  #! Translate
            "status": self.table_status,
            "percentCompleted": "N/A",
            "aoiArea": self.aoi_area,
            "cost": None,
            "created": "",
            "reviewUntil": None,
            "id": self.table_id,
        }


@dataclass
class NoAoiProcessingsRow(Serializable, SkipDataClass):
    """Separator row introducing processings attached to the template but not intersecting
    any of its AOIs (the backend omits them from ``aoiDetails``)."""
    id: str = ""

    @property
    def is_separator(self) -> bool:
        return True

    def as_processing_table_dict(self):
        return {
            "name": "No AOI",  #! Translate
            "workflowDef": "",
            "status": "",
            "percentCompleted": "",
            "aoiArea": None,
            "cost": None,
            "created": "",
            "reviewUntil": None,
            "id": "",
        }


@dataclass
class UpdateAoiSchema(Serializable, SkipDataClass):
    name: Optional[str] = None
    geometry: Optional[Mapping[str, Any]] = None


@dataclass
class AddSingleAoiSchema(Serializable, SkipDataClass):
    geometry: Mapping[str, Any]
    name: Optional[str] = None


@dataclass
class AddAoisSchema(Serializable, SkipDataClass):
    aois: List[AddSingleAoiSchema]


@dataclass
class DeleteAoisSchema(Serializable, SkipDataClass):
    aoiIds: List[str]


@dataclass
class ProcessingTemplateDetails(Serializable, SkipDataClass):
    template: ProcessingTemplateDTO

    def __post_init__(self):
        if isinstance(self.template, dict):
            self.template = ProcessingTemplateDTO.from_dict(self.template)


@dataclass
class CreateProcessingTemplateSchema(Serializable, SkipDataClass):
    name: str
    searchParams: Mapping[str, Any]
    projectId: str
    activeUntil: str
    processingParams: Optional[Mapping[str, Any]] = None


@dataclass
class UpdateProcessingTemplateSchema(Serializable, SkipDataClass):
    name: str
    searchParams: Mapping[str, Any]
    processingParams: Mapping[str, Any]
    activeUntil: str


@dataclass
class RunTemplateProcessingSchema(Serializable, SkipDataClass):
    name: str
    description: Optional[str]
    wdName: Optional[str]
    wdId: Optional[str]
    geometry: Mapping[str, Any]
    params: Mapping[str, Any]
    meta: Mapping[str, Any]
    blocks: List[Mapping[str, Any]]
    updateTemplateGeometry: bool


@dataclass
class ProcessingUIParams(Serializable, SkipDataClass):
    name: Optional[str]
    data_source_index: int
    zoom: Optional[int]
    wd_name: str
    model_options: list[BlockOption]


@dataclass
class ProcessingDTO(Serializable, SkipDataClass):
    id: UUID
    name: str
    projectId: UUID
    status: ProcessingStatus
    description: Optional[str]
    workflowDef: WorkflowDef
    aoiArea: int
    cost: int
    created: datetime
    rasterLayer: RasterLayer
    vectorLayer: VectorLayer
    messages: list[ErrorMessage]
    params: ProcessingParams
    blocks: List[BlockOption]

    percentCompleted: Optional[int] = None
    reviewStatus: Optional[ProcessingReviewStatus] = None

    def __post_init__(self):
        self.status = ProcessingStatus(self.status)
        self.created = _parse_iso_datetime(self.created)
        self.params = ProcessingParams.from_dict(self.params)
        self.blocks = [BlockOption.from_dict(block) for block in self.blocks]
        self.workflowDef = WorkflowDef.from_dict(self.workflowDef)
        self.messages = [ErrorMessage.from_response(message) for message in self.messages]
        self.rasterLayer = RasterLayer.from_dict(self.rasterLayer)
        self.vectorLayer = VectorLayer.from_dict(self.vectorLayer)
        if self.reviewStatus is None:
            self.reviewStatus = ProcessingReviewStatus()
        else:
            self.reviewStatus = ProcessingReviewStatus.from_dict(self.reviewStatus)

    @property
    def review_expires(self):
        if not isinstance(self.reviewStatus.inReviewUntil, datetime)\
                or not self.reviewStatus.is_in_review:
            return False
        now = datetime.now(timezone.utc)
        one_day = timedelta(1)
        return self.reviewStatus.inReviewUntil - now < one_day

    @property
    def reviewUntil(self):
        """
        backwards compatibility
        """
        return self.reviewStatus.inReviewUntil

    @property
    def is_final_state(self):
        """
        means that the processing is reached final state and can't change it without user interaction
        """
        return  self.status.is_terminal and not self.reviewStatus.is_not_accepted

    def error_message(self, raw=False):
        if not self.messages:
            return ""
        return "\n".join([error.to_str(raw=raw) for error in self.messages])

    def as_processing_table_dict(self):
        return {
            "name": self.name,
            "workflowDef": self.workflowDef.name,
            "status": self.reviewStatus.reviewStatus.display_value
                      if (self.reviewStatus and not self.reviewStatus.is_none)
                      else self.status.display_value,
            "percentCompleted": self.percentCompleted,
            "aoiArea": self.aoiArea/1000000,
            "cost": self.cost,
            "created": self.created.astimezone().strftime('%Y-%m-%d %H:%M'),
            "reviewUntil": self.reviewUntil,
            "id": self.id
        }


@dataclass
class TemplateProcessingSchema(Serializable, SkipDataClass):
    """A processing as returned by ``GET /processings/template/{id}/processings``.

    This endpoint serves the v1 ``ProcessingJson`` shape, whose ``params`` is a flat
    ``Map[String,String]`` (e.g. ``{url, zoom, data_provider}``) — NOT the v2
    ``{sourceParams: {...}}`` used elsewhere. There is no v2 variant of this endpoint, so
    a dedicated schema keeps the flat params instead of forcing it through ``ProcessingDTO``
    (whose ``ProcessingParams`` parsing would discard or choke on the flat shape).

    It still carries the result layers, so a processing listed here can be loaded.
    """
    id: UUID
    name: str
    projectId: UUID
    status: ProcessingStatus
    workflowDef: WorkflowDef
    created: datetime
    rasterLayer: RasterLayer
    vectorLayer: VectorLayer
    params: Optional[Mapping[str, str]] = None  # v1 flat params, kept as-is
    description: Optional[str] = None
    aoiArea: Optional[int] = None
    area: Optional[int] = None
    cost: Optional[int] = None
    percentCompleted: Optional[int] = None
    blocks: Optional[List[BlockOption]] = None
    messages: Optional[List[ErrorMessage]] = None
    reviewStatus: Optional[ProcessingReviewStatus] = None

    def __post_init__(self):
        self.status = ProcessingStatus(self.status)
        self.created = _parse_iso_datetime(self.created)
        self.rasterLayer = RasterLayer.from_dict(self.rasterLayer)
        self.vectorLayer = VectorLayer.from_dict(self.vectorLayer)
        self.workflowDef = WorkflowDef.from_dict(self.workflowDef)
        self.blocks = [BlockOption.from_dict(b) for b in (self.blocks or [])]
        self.messages = [ErrorMessage.from_response(m) for m in (self.messages or [])]
        if self.reviewStatus is None:
            self.reviewStatus = ProcessingReviewStatus()
        else:
            self.reviewStatus = ProcessingReviewStatus.from_dict(self.reviewStatus)

    @property
    def is_final_state(self) -> bool:
        return self.status.is_terminal and not self.reviewStatus.is_not_accepted

    def as_processing_table_dict(self):
        area = (self.aoiArea if self.aoiArea is not None else self.area) or 0
        return {
            "name": self.name,
            "workflowDef": self.workflowDef.name if self.workflowDef else "",
            "status": self.status.display_value,
            "percentCompleted": self.percentCompleted,
            "aoiArea": area / 1e6,
            "cost": self.cost,
            "created": self.created.astimezone().strftime('%Y-%m-%d %H:%M'),
            "reviewUntil": None,
            "id": self.id,
        }


class ProcessingSortBy(str, Enum):
    scenario = "SCENARIO"
    name = "NAME"
    project = "PROJECT"
    email = "EMAIL"
    created = "CREATED"
    status = "STATUS"
    progress = "PROGRESS"
    completed = "COMPLETED"
    cost = "COST"
    area = "AREA"
    provider = "PROVIDER"


class ProcessingSortOrder(str, Enum):
    ascending = "ASC"
    descending = "DESC"


@dataclass
class ProcessingsRequest(Serializable):
    limit: int = 30
    offset: int = 0
    terms: Optional[str] = None
    sortBy: Optional[str] = None
    sortOrder: Optional[str] = None


@dataclass
class ProcessingsResult(SkipDataClass):
    results: Optional[List] = None
    total: int = 0
    count: int = 0

    def __post_init__(self):
        if self.results:
            self.results = [ProcessingDTO.from_dict(p) for p in self.results]
        else:
            self.results = []
