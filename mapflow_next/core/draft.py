"""The run form as data: model → area → imagery → processing request. Pure Python.

The UI edits a `RunDraft`; the draft says what is missing (`issues`), what it will cost
(`estimate`) and what to send (`payload`). Keeping this out of the widgets is what makes the
main scenario testable without QGIS.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

from .models import BillingType, DataProvider, Model, Project, UserStatus
from .tile_layers import TileOffer, TileParams, nearest_zoom, user_defined

MIN_BILLED_AREA_KM2 = 1.0


@dataclass
class AreaOfInterest:
    name: str
    geometry: dict                  # GeoJSON geometry in WGS84
    area_km2: float                 # union of the parts, ellipsoidal
    max_bbox_km2: float = 0.0       # largest lat-lon bounding box of one polygon
    polygons: int = 1
    layer_id: Optional[str] = None
    layer_features: int = 0         # polygons (features) in the layer
    selected: int = 0               # of those, selected and used as the area (0: the whole layer)


@dataclass
class ImageryChoice:
    """Where the pixels come from. Exactly one of the four kinds."""
    kind: str                                   # provider | my_imagery | catalog | tile
    label: str
    provider: Optional[DataProvider] = None     # kind == provider
    zoom: Optional[int] = None
    mosaic_id: Optional[str] = None             # kind == my_imagery
    image_ids: List[str] = field(default_factory=list)   # my_imagery (optional) or catalog
    catalog_provider: Optional[str] = None      # kind == catalog: the image's provider name
    min_area_km2: float = 0.0                   # kind == catalog: the smallest order the image's provider sells
    tile_layer_id: Optional[str] = None         # kind == tile: the QGIS layer…
    tile_name: str = ""                         # …its name
    tile_params: Optional[TileParams] = field(default=None, repr=False)     # …and what is sent for it

    @classmethod
    def from_provider(cls, provider: DataProvider, zoom: Optional[int] = None) -> "ImageryChoice":
        zoom = provider.nearest_zoom(zoom)
        return cls("provider", f"{provider.display_name} · zoom {zoom}", provider=provider, zoom=zoom)

    @classmethod
    def from_mosaic(cls, mosaic_id: str, name: str, image_id: Optional[str] = None,
                    image_name: str = "") -> "ImageryChoice":
        """A whole collection, or one image of it."""
        label = f"{name} · {image_name}" if image_id and image_name else name
        return cls("my_imagery", label, mosaic_id=mosaic_id, image_ids=[image_id] if image_id else [])

    def with_collection_name(self, old: str, new: str) -> None:
        """A chosen collection (or one of its images) was renamed: the label starts with the collection's name."""
        if self.kind == "my_imagery" and self.label.startswith(old):
            self.label = new + self.label[len(old):]

    @classmethod
    def from_catalog(cls, image_id: str, provider_name: str, zoom: Optional[int], label: str,
                     min_area_km2: float = 0.0) -> "ImageryChoice":
        return cls("catalog", label, image_ids=[image_id], catalog_provider=provider_name, zoom=zoom,
                   min_area_km2=min_area_km2 or 0.0)

    @classmethod
    def from_tile(cls, offer: TileOffer, zoom: Optional[int] = None) -> "ImageryChoice":
        """A usable QGIS tile layer, at the offered zoom nearest to `zoom` (18 when it is None)."""
        zoom = nearest_zoom(offer.params.zooms, zoom)
        return cls("tile", f"{offer.name} · zoom {zoom}", zoom=zoom, tile_layer_id=offer.layer_id,
                   tile_name=offer.name, tile_params=offer.params)

    @property
    def identity(self) -> tuple:
        """What tells one imagery choice from another (the key of the cost answer)."""
        source = (self.provider.name if self.provider else self.tile_layer_id if self.kind == "tile"
                  else self.mosaic_id)
        kind = self.tile_params.source_type if self.tile_params else ""
        address = self.tile_params.url if self.tile_params else ""
        return self.kind, source, kind, address, self.zoom, tuple(self.image_ids)

    @property
    def source_name(self) -> str:
        """The imagery's provider as a person reads it."""
        if self.kind == "tile":
            return "QGIS tile layer"
        if self.kind == "provider" and self.provider:
            return self.provider.display_name
        if self.kind == "catalog":
            return (self.catalog_provider or "Catalog").replace("_", " ").title()
        return "My imagery"

    @property
    def price_per_km2(self) -> Optional[float]:
        """Known locally for basemaps; your own imagery is free; catalog prices come from /cost."""
        if self.kind == "provider" and self.provider:
            return self.provider.price_at(self.zoom)
        if self.kind == "my_imagery":
            return 0.0
        return None

    def source_params(self, credentials: Optional[Tuple[str, str]] = None) -> dict:
        """The `sourceParams` of the request. `credentials` (login, password) go into a tile layer's
        `userDefined` and nowhere else."""
        if self.kind == "tile":
            return {"userDefined": user_defined(self.tile_params, self.zoom, credentials)}
        if self.kind == "provider":
            return {"dataProvider": {"providerName": self.provider.name, "zoom": str(self.zoom)}}
        if self.kind == "my_imagery":
            # One or the other, never both (the API rejects the pair as an invalid body):
            # the chosen images, or the whole collection
            if self.image_ids:
                return {"myImagery": {"imageIds": list(self.image_ids)}}
            return {"myImagery": {"mosaicId": self.mosaic_id}}
        if self.kind == "catalog":
            params = {"dataProvider": (self.catalog_provider or "").lower(), "imageIds": list(self.image_ids)}
            if self.zoom is not None:
                params["zoom"] = int(self.zoom)
            return {"imagerySearch": params}
        raise ValueError(f"Unknown imagery kind {self.kind}")


def processing_meta(imagery: "ImageryChoice", version: str = "") -> Dict[str, str]:
    """Where the processing came from, as the current plugin reports it (values are strings)."""
    if imagery.kind == "provider":
        source = imagery.provider.name.lower()
    elif imagery.kind == "my_imagery":
        source = "my imagery"
    elif imagery.kind == "tile":
        source = imagery.tile_params.meta_source
    else:
        source = "imagery search"
    meta = {"source-app": "qgis", "source": source}
    if version:
        meta["version"] = version
    return meta


@dataclass
class Estimate:
    billed_km2: float
    model_price: float
    options_price: float
    imagery_price: Optional[float]

    @property
    def per_km2(self) -> Optional[float]:
        if self.imagery_price is None:
            return None
        return self.model_price + self.options_price + self.imagery_price

    @property
    def credits(self) -> Optional[int]:
        """Mapflow rounds the total up to whole credits."""
        if self.per_km2 is None:
            return None
        return int(math.ceil(round(self.billed_km2 * self.per_km2, 6)))


@dataclass
class Issue:
    """Something that stops the run. `field` tells the form which step to point at."""
    field: str      # model | area | imagery | account
    text: str
    # Ways out, shown as links next to the text: (label, where) with where one of "top_up",
    # "pricing" or "support". The form knows the addresses.
    links: Tuple[Tuple[str, str], ...] = ()


@dataclass
class Coverage:
    """How the area meets the chosen imagery that has a footprint (My imagery, or one catalog image). Worked
    out on the map side (it takes geometry)."""
    name: str                                       # the collection or the image
    overlaps: bool
    clipped: Optional[AreaOfInterest] = None        # the part of the area inside the imagery


@dataclass
class RunDraft:
    model: Optional[Model] = None
    options: Set[str] = field(default_factory=set)
    aoi: Optional[AreaOfInterest] = None
    imagery: Optional[ImageryChoice] = None
    name: str = ""
    name_edited: bool = False
    scenario_id: Optional[str] = None
    coverage: Optional[Coverage] = None             # set for imagery with a footprint; None for basemaps
    description: str = ""

    # ---- derived ----

    @property
    def processed_area(self) -> Optional[AreaOfInterest]:
        """What gets processed and billed: for imagery with a footprint (My imagery, or one catalog image),
        the part of the area inside the imagery; otherwise the area itself."""
        if self.aoi and self.coverage and self.coverage.overlaps and self.coverage.clipped:
            return self.coverage.clipped
        return self.aoi

    def default_name(self) -> str:
        parts = [self.model.short_name if self.model else "Processing"]
        if self.aoi:
            parts.append(self.aoi.name)
        return " · ".join(parts)

    def effective_name(self) -> str:
        return (self.name.strip() if self.name_edited and self.name.strip() else self.default_name())[:255]

    def estimate(self) -> Optional[Estimate]:
        if not self.model or not self.aoi:
            return None
        imagery_price = self.imagery.price_per_km2 if self.imagery else None
        return Estimate(billed_km2=max(self.processed_area.area_km2, MIN_BILLED_AREA_KM2),
                        model_price=self.model.base_price,
                        options_price=self.model.price(self.options) - self.model.base_price,
                        imagery_price=imagery_price)

    def issues(self, project: Optional[Project], status: Optional[UserStatus],
               server_cost: Optional[int] = None) -> List[Issue]:
        found: List[Issue] = []
        if project is not None and not project.role.can_run:
            found.append(Issue("account", "You can view this shared project but not start processings in it."))
        if not self.model:
            found.append(Issue("model", "Choose what to map."))
        if not self.aoi:
            found.append(Issue("area", "Choose an area on the map."))
        elif self.coverage and not self.coverage.overlaps:
            found.append(Issue("area", f"The area doesn't overlap “{self.coverage.name}”. Choose an area inside "
                                       "the imagery, or use its extent."))
        else:
            area = self.processed_area
            if area.area_km2 <= 0:
                found.append(Issue("area", "The area layer has no polygons."))
            limit = project.aoi_area_limit_km2 if project else 0
            if limit and area.area_km2 > limit:
                found.append(Issue("area", f"The area is {area.area_km2:,.2f} km², your plan allows "
                                           f"{limit:,.2f} km² per processing."))
            elif limit and area.max_bbox_km2 > limit:
                found.append(Issue("area", f"One polygon's bounding box is {area.max_bbox_km2:,.2f} km², "
                                           f"over the {limit:,.2f} km² limit. Split it into smaller polygons."))
            if status and status.max_aois and area.polygons > status.max_aois:
                found.append(Issue("area", f"Use up to {status.max_aois} polygons in one processing "
                                           f"(this layer has {area.polygons})."))
        if not self.imagery:
            found.append(Issue("imagery", "Choose imagery."))
        else:
            if self.imagery.kind == "catalog" and status is not None \
                    and not status.can_search(self.imagery.catalog_provider):
                found.append(Issue("account", f"{self.imagery.source_name} imagery isn't included in your plan. "
                                              "Switch to a Premium plan, or ask support to enable it.",
                                   (("See plans", "pricing"), ("Contact support", "support"))))
            minimum, source = self.imagery.min_area_km2, self.imagery.source_name
            if self.imagery.kind == "provider" and self.imagery.provider:
                minimum = max(minimum, self.imagery.provider.min_area_km2)
            elif self.imagery.kind == "catalog" and status is not None:
                minimum = max(minimum, status.min_area_for(self.imagery.catalog_provider))
            if self.aoi and minimum and self.processed_area.area_km2 < minimum:
                found.append(Issue("imagery", f"{source} sells at least {minimum:,.2f} km² per order; the area is "
                                              f"{self.processed_area.area_km2:,.2f} km². Choose a larger area."))
        if status and not found:
            if status.billing is BillingType.credits:
                estimate = self.estimate()
                cost = server_cost if server_cost is not None else (estimate.credits if estimate else None)
                if cost is not None and cost > status.remaining_credits:
                    found.append(Issue("account", f"This run needs {cost:,} credits; you have "
                                                  f"{status.remaining_credits:,}.", (("Top up", "top_up"),)))
            elif status.billing is BillingType.area and self.aoi:
                if self.processed_area.area_km2 > status.remaining_area_km2:
                    found.append(Issue("account", f"This run needs {self.processed_area.area_km2:,.2f} km²; you have "
                                                  f"{status.remaining_area_km2:,.2f} km² left."))
        return found

    def payload(self, project_id: str, version: str = "", credentials: Optional[Tuple[str, str]] = None) -> dict:
        """The `POST /processings/v2` body (also accepted by `/processing/cost/v2`). `credentials`: the login and
        password of a tile layer, for the start only; the cost request has none."""
        if not (self.model and self.aoi and self.imagery):
            raise ValueError("The draft is incomplete")
        body = {
            "name": self.effective_name(),
            "projectId": project_id,
            "wdId": self.model.id,
            "geometry": self.processed_area.geometry,
            "params": {"sourceParams": self.imagery.source_params(credentials)},
            "blocks": self.model.blocks_payload(self.options),
            "meta": processing_meta(self.imagery, version),
        }
        if self.description.strip():
            body["description"] = self.description.strip()
        return body
