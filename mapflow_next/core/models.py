"""Domain objects parsed from Mapflow API responses. Pure Python: no Qt, no QGIS.

Every parser tolerates missing and extra keys, so a non-breaking API change never drops data.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


def parse_datetime(value: Any) -> Optional[datetime]:
    if not value:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _num(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


class BillingType(str, Enum):
    credits = "CREDITS"
    area = "AREA"
    none = "NONE"

    @classmethod
    def parse(cls, value: Any) -> "BillingType":
        try:
            return cls(str(value or "AREA").upper())
        except ValueError:
            return cls.area


class Role(str, Enum):
    readonly = "readonly"
    contributor = "contributor"
    maintainer = "maintainer"
    owner = "owner"

    @property
    def can_run(self) -> bool:
        return self is not Role.readonly

    @property
    def can_manage(self) -> bool:
        """Rename, delete and restart processings."""
        return self in (Role.maintainer, Role.owner)


# ---------- models (workflow definitions) ----------

@dataclass
class Block:
    name: str
    display_name: str
    price: float
    optional: bool

    @classmethod
    def from_api(cls, data: dict) -> "Block":
        return cls(name=data.get("name", ""),
                   display_name=data.get("displayName") or data.get("name", ""),
                   price=_num(data.get("price")),
                   optional=bool(data.get("optional")))


@dataclass
class Model:
    """A workflow definition: one AI model (or pipeline) with optional blocks."""
    id: str
    name: str
    description: str = ""
    base_price: float = 0.0
    blocks: List[Block] = field(default_factory=list)

    @classmethod
    def from_api(cls, data: dict) -> "Model":
        blocks = [Block.from_api(b) for b in data.get("blocks") or []]
        # Mapflow puts the model's own price in pricePerSqKm and lists its required blocks at 0, so
        # their sum is only a fallback for a definition without pricePerSqKm.
        if data.get("pricePerSqKm") is not None:
            base = _num(data.get("pricePerSqKm"), 0.0)
        else:
            base = sum(b.price for b in blocks if not b.optional)
        return cls(id=str(data.get("id", "")), name=data.get("name", ""),
                   description=data.get("description") or "", base_price=base, blocks=blocks)

    @property
    def options(self) -> List[Block]:
        return [b for b in self.blocks if b.optional]

    def price(self, enabled: Optional[set] = None) -> float:
        enabled = enabled or set()
        return self.base_price + sum(b.price for b in self.options if b.name in enabled)

    def blocks_payload(self, enabled: Optional[set] = None) -> List[dict]:
        enabled = enabled or set()
        return [{"name": b.name, "enabled": b.name in enabled} for b in self.options]

    @property
    def short_name(self) -> str:
        """The name without the leading emoji the API puts on default models."""
        text = self.name.strip()
        while text and not text[0].isalnum() and text[0] not in "[(":
            text = text[1:].lstrip()
        return text or self.name


# ---------- imagery sources ----------

ZOOM_MIN, ZOOM_MAX = 17, 21
DEFAULT_ZOOM = 18


@dataclass
class DataProvider:
    """A basemap provider served by Mapflow (Mapbox, ArcGIS World Imagery, …): price depends on zoom."""
    id: str
    name: str            # API name, sent in the processing request
    display_name: str
    prices: Dict[int, float] = field(default_factory=dict)   # zoom -> credits per km²
    preview_url: Optional[str] = None
    preview_max_zoom: Optional[int] = None
    min_area_km2: float = 0.0

    @classmethod
    def from_api(cls, data: dict) -> "DataProvider":
        prices = {}
        for entry in data.get("price") or []:
            try:
                prices[int(entry.get("zoom"))] = _num(entry.get("priceSqKm"))
            except (TypeError, ValueError):
                continue
        return cls(id=str(data.get("id", "")), name=data.get("name", ""),
                   display_name=data.get("displayName") or data.get("name", ""),
                   prices=prices, preview_url=data.get("previewUrl"),
                   preview_max_zoom=data.get("previewUrlMaxZoom"),
                   min_area_km2=_num(data.get("minAreaSqKm", data.get("minAreaSqkm")), 0.0))

    @property
    def zooms(self) -> List[int]:
        """Zoom levels offered for processing: z17–z21 where the provider has them (Mapflow models
        need building-level detail; coarser zooms only lose quality)."""
        offered = [z for z in sorted(self.prices) if ZOOM_MIN <= z <= ZOOM_MAX]
        if offered:
            return offered
        if self.prices:
            return [max(self.prices)]                 # a provider that stops below z17: its sharpest zoom
        return list(range(ZOOM_MIN, ZOOM_MAX + 1))    # no zoom-specific prices: the whole range

    def nearest_zoom(self, wanted: Optional[int]) -> int:
        if wanted is None:
            return max(self.zooms)
        return min(self.zooms, key=lambda z: (abs(z - wanted), -z))

    def price_at(self, zoom: Optional[int]) -> float:
        return self.prices.get(int(zoom), 0.0) if zoom is not None else 0.0


@dataclass
class UserStatus:
    billing: BillingType = BillingType.area
    remaining_credits: int = 0
    remaining_area_km2: float = 0.0
    data_providers: List[DataProvider] = field(default_factory=list)
    search_providers: List[str] = field(default_factory=list)
    review_enabled: bool = False
    max_aois: int = 10

    @classmethod
    def from_api(cls, data: dict) -> "UserStatus":
        providers, seen = [], set()
        for item in data.get("dataProviders") or []:
            provider = DataProvider.from_api(item)
            if provider.name and provider.name not in seen:
                seen.add(provider.name)
                providers.append(provider)
        search = [p.get("name") if isinstance(p, dict) else str(p)
                  for p in data.get("searchDataProviders") or []]
        return cls(billing=BillingType.parse(data.get("billingType")),
                   remaining_credits=int(_num(data.get("remainingCredits"))),
                   remaining_area_km2=_num(data.get("remainingArea")) / 1e6,
                   data_providers=providers,
                   search_providers=[s for s in search if s],
                   review_enabled=bool(data.get("reviewWorkflowEnabled")),
                   max_aois=int(_num(data.get("maxAoisPerProcessing"), 10)) or 10)


# ---------- projects ----------

@dataclass
class Project:
    id: str
    name: str
    is_default: bool = False
    models: List[Model] = field(default_factory=list)
    owner_email: str = ""
    user_id: Optional[str] = None
    aoi_area_limit_km2: float = 0.0     # 0 = unknown, the backend decides
    role: Role = Role.owner
    description: str = ""
    succeeded: int = 0
    failed: int = 0
    in_progress: int = 0
    total: Optional[int] = None         # processings, when the API reports it
    updated: Optional[datetime] = None
    created: Optional[datetime] = None
    _share: dict = field(default_factory=dict, repr=False)

    @classmethod
    def from_api(cls, data: dict, current_email: str = "") -> "Project":
        user = data.get("user") or {}
        project = cls(id=str(data.get("id", "")), name=data.get("name", ""),
                      is_default=bool(data.get("isDefault")),
                      models=[Model.from_api(m) for m in data.get("workflowDefs") or []],
                      owner_email=user.get("email") or "", user_id=user.get("id"),
                      aoi_area_limit_km2=_num(user.get("aoiAreaLimit")) / 1e6,
                      description=(data.get("description") or "").strip(),
                      updated=parse_datetime(data.get("updated")), created=parse_datetime(data.get("created")),
                      _share=data.get("shareProject") or {})
        counts = data.get("processingCounts") or {}
        project.succeeded = int(_num(counts.get("succeeded")))
        project.failed = int(_num(counts.get("failed")))
        project.in_progress = int(_num(counts.get("inProgress", counts.get("in_progress"))))
        if counts.get("total") is not None:
            project.total = int(_num(counts.get("total")))
        project.role = project.role_of(current_email)
        return project

    def role_of(self, email: str) -> Role:
        """The signed-in user's role. No share section means the user's own project."""
        if not self._share:
            return Role.owner
        email = (email or "").strip().lower()
        if not email:
            return Role.readonly
        for owner in self._share.get("owners") or []:
            if (owner.get("email") or "").strip().lower() == email:
                return Role.owner
        for user in self._share.get("users") or []:
            if (user.get("email") or "").strip().lower() == email:
                try:
                    return Role(user.get("role"))
                except ValueError:
                    return Role.readonly
        return Role.readonly

    def model(self, model_id: str) -> Optional[Model]:
        return next((m for m in self.models if m.id == model_id), None)

    @property
    def members(self) -> int:
        """People who share the project besides its owners."""
        return len(self._share.get("users") or [])

    @property
    def shared(self) -> bool:
        """Shared with other people, or shared with me by someone else."""
        return self.members > 0 or self.role is not Role.owner

    @property
    def processings_count(self) -> int:
        return self.total if self.total is not None else self.succeeded + self.failed + self.in_progress


# ---------- processings ----------

class Status(str, Enum):
    ok = "OK"
    in_progress = "IN_PROGRESS"
    failed = "FAILED"
    refunded = "REFUNDED"
    cancelled = "CANCELLED"
    awaiting = "AWAITING"
    unprocessed = "UNPROCESSED"

    @classmethod
    def parse(cls, value: Any) -> "Status":
        try:
            return cls(str(value).upper())
        except ValueError:
            return cls.unprocessed

    @property
    def is_terminal(self) -> bool:
        return self in (Status.ok, Status.failed, Status.refunded, Status.cancelled)


@dataclass
class Message:
    code: str
    params: Dict[str, Any] = field(default_factory=dict)
    text: str = ""


@dataclass
class SourceInfo:
    """What imagery a processing ran on, normalised from the v2 `params.sourceParams` shape."""
    kind: str = "unknown"            # provider | my_imagery | catalog | custom | unknown
    provider: str = ""
    zoom: Optional[int] = None
    mosaic_id: Optional[str] = None
    image_ids: List[str] = field(default_factory=list)

    @classmethod
    def from_params(cls, params: Optional[dict]) -> "SourceInfo":
        source = (params or {}).get("sourceParams")
        if not isinstance(source, dict):
            return cls()

        def zoom(value):
            try:
                return int(value)
            except (TypeError, ValueError):
                return None

        if source.get("dataProvider"):
            p = source["dataProvider"]
            return cls("provider", provider=p.get("providerName") or "", zoom=zoom(p.get("zoom")))
        if source.get("myImagery"):
            p = source["myImagery"]
            return cls("my_imagery", mosaic_id=p.get("mosaicId"), image_ids=list(p.get("imageIds") or []))
        if source.get("imagerySearch"):
            p = source["imagerySearch"]
            return cls("catalog", provider=p.get("dataProvider") or "", zoom=zoom(p.get("zoom")),
                       image_ids=list(p.get("imageIds") or []))
        if source.get("userDefined"):
            return cls("custom", zoom=zoom(source["userDefined"].get("zoom")))
        return cls()


@dataclass
class Processing:
    id: str
    name: str
    project_id: str = ""
    status: Status = Status.unprocessed
    percent: int = 0
    model_id: str = ""
    model_name: str = ""
    area_km2: float = 0.0
    cost: int = 0
    created: Optional[datetime] = None
    description: str = ""
    raster_tile_url: str = ""
    raster_tilejson_url: str = ""
    vector_tile_url: str = ""
    vector_tilejson_url: str = ""
    messages: List[Message] = field(default_factory=list)
    source: SourceInfo = field(default_factory=SourceInfo)
    enabled_blocks: List[str] = field(default_factory=list)
    review_status: Optional[str] = None
    style_name: Optional[str] = None

    @classmethod
    def from_api(cls, data: dict) -> "Processing":
        wd = data.get("workflowDef") or {}
        raster = data.get("rasterLayer") or {}
        vector = data.get("vectorLayer") or {}
        review = data.get("reviewStatus") or {}
        messages = []
        for m in data.get("messages") or []:
            if isinstance(m, dict):
                messages.append(Message(code=m.get("code", ""), params=m.get("parameters") or m.get("params") or {},
                                        text=m.get("message") or ""))
        return cls(id=str(data.get("id", "")), name=data.get("name") or "",
                   project_id=str(data.get("projectId") or ""),
                   status=Status.parse(data.get("status")),
                   percent=int(_num(data.get("percentCompleted"))),
                   model_id=str(wd.get("id") or ""), model_name=wd.get("name") or "",
                   area_km2=_num(data.get("aoiArea")) / 1e6, cost=int(_num(data.get("cost"))),
                   created=parse_datetime(data.get("created")), description=data.get("description") or "",
                   raster_tile_url=raster.get("tileUrl") or "", raster_tilejson_url=raster.get("tileJsonUrl") or "",
                   vector_tile_url=vector.get("tileUrl") or "", vector_tilejson_url=vector.get("tileJsonUrl") or "",
                   messages=messages, source=SourceInfo.from_params(data.get("params")),
                   enabled_blocks=[b.get("name") for b in data.get("blocks") or []
                                   if isinstance(b, dict) and b.get("enabled")],
                   review_status=review.get("reviewStatus"),
                   style_name=wd.get("styleName") or vector.get("styleName"))

    @property
    def is_done(self) -> bool:
        return self.status is Status.ok

    @property
    def is_running(self) -> bool:
        return not self.status.is_terminal

    @property
    def needs_review(self) -> bool:
        return self.review_status == "IN_REVIEW"

    @property
    def is_final(self) -> bool:
        """Nothing will change without the user: polling can stop."""
        return self.status.is_terminal and self.review_status != "NOT_ACCEPTED"


def aois_geojson(data: Any) -> dict:
    """GET /processings/{id}/aois as a FeatureCollection. Mapflow answers with a list of AOIs; an
    {"aois": [...]} object is read too."""
    aois = data.get("aois") if isinstance(data, dict) else data
    features = [{"type": "Feature", "geometry": a["geometry"], "properties": {"id": a.get("id")}}
                for a in aois or [] if isinstance(a, dict) and a.get("geometry")]
    return {"type": "FeatureCollection", "features": features}


# ---------- imagery catalog and My imagery ----------

@dataclass
class CatalogImage:
    id: str
    provider: str = ""
    product_type: str = ""
    acquired: Optional[datetime] = None
    cloud: Optional[float] = None
    off_nadir: Optional[float] = None
    resolution: Optional[float] = None
    zoom: Optional[int] = None
    preview_type: str = ""
    preview_url: str = ""
    footprint: Optional[dict] = None
    coverage: Optional[float] = None
    min_area_km2: float = 0.0

    @classmethod
    def from_api(cls, data: dict) -> "CatalogImage":
        def opt(key):
            value = data.get(key)
            return None if value is None else _num(value)

        zoom = data.get("zoom")
        try:
            zoom = int(zoom) if zoom not in (None, "") else None
        except (TypeError, ValueError):
            zoom = None
        return cls(id=str(data.get("id", "")), provider=data.get("providerName") or "",
                   product_type=data.get("productType") or "", acquired=parse_datetime(data.get("acquisitionDate")),
                   cloud=opt("cloudCover"), off_nadir=opt("offNadirAngle"), resolution=opt("pixelResolution"),
                   zoom=zoom, preview_type=(data.get("previewType") or "").lower(),
                   preview_url=data.get("previewUrl") or "", footprint=data.get("footprint"),
                   coverage=opt("aoiIntersectionPercent"), min_area_km2=_num(data.get("minAreaSqkm")))

    @property
    def is_mosaic(self) -> bool:
        return self.product_type.lower() == "mosaic"


@dataclass
class Mosaic:
    id: str
    name: str
    created: Optional[datetime] = None
    size_bytes: int = 0
    footprint_wkt: str = ""
    tile_url: str = ""
    tilejson_url: str = ""
    image_count: Optional[int] = None    # None until known

    @classmethod
    def from_api(cls, data: dict) -> "Mosaic":
        raster = data.get("rasterLayer") or {}
        summary = data.get("status_summary") or data.get("statusSummary") or {}
        count = summary.get("total", data.get("imagesCount", data.get("images_count")))
        return cls(id=str(data.get("id", "")), name=data.get("name") or "",
                   image_count=int(_num(count)) if count is not None else None,
                   created=parse_datetime(data.get("created_at")), size_bytes=int(_num(data.get("sizeInBytes"))),
                   footprint_wkt=data.get("footprint") or "", tile_url=raster.get("tileUrl") or "",
                   tilejson_url=raster.get("tileJsonUrl") or "")


@dataclass
class MosaicImage:
    """One image in a My imagery collection."""
    id: str
    mosaic_id: str = ""
    filename: str = ""
    preview_s: str = ""
    preview_l: str = ""
    uploaded: Optional[datetime] = None
    size_bytes: int = 0
    pixel_size: Optional[float] = None
    footprint_wkt: str = ""

    @classmethod
    def from_api(cls, data: dict) -> "MosaicImage":
        meta = data.get("meta_data") or {}
        pixel = meta.get("pixel_size")
        if isinstance(pixel, (list, tuple)) and pixel:
            pixel = pixel[0]
        return cls(id=str(data.get("id", "")), mosaic_id=str(data.get("mosaic_id") or ""),
                   filename=data.get("filename") or "", preview_s=data.get("preview_url_s") or "",
                   preview_l=data.get("preview_url_l") or "", uploaded=parse_datetime(data.get("uploaded_at")),
                   size_bytes=int(_num(data.get("file_size"))),
                   pixel_size=_num(pixel) if pixel is not None else None, footprint_wkt=data.get("footprint") or "")
