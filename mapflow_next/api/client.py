"""Mapflow REST endpoints used by the plugin, returning domain objects.

The endpoint set is the current plugin's, minus what the new design leaves out (planned
processings/templates, custom XYZ providers, review workflow actions).
"""
from __future__ import annotations

from typing import Callable, List, Optional
from urllib.parse import quote, urlencode

from ..config import PROCESSINGS_PAGE_SIZE, PROJECTS_PAGE_SIZE, RESULT_TIMEOUT_S, SEARCH_PAGE_SIZE
from ..core.models import CatalogImage, Mosaic, MosaicImage, Processing, Project, UserStatus, aois_geojson
from .http import Http

OnError = Optional[Callable]


class MapflowApi:
    def __init__(self, http: Http):
        self.http = http

    # ---------- account ----------

    def version(self, on_done: Callable[[str], None], on_error: OnError = None) -> None:
        self.http.get("version", on_success=on_done, on_error=on_error, parse="text", timeout=10)

    def default_project(self, on_done: Callable[[dict], None], on_error: OnError = None) -> None:
        """Also the sign-in check: it answers only for valid credentials, with the user section."""
        self.http.get("projects/default", on_success=on_done, on_error=on_error)

    def user_status(self, on_done: Callable[[UserStatus], None], on_error: OnError = None) -> None:
        self.http.get("user/status", on_success=lambda d: on_done(UserStatus.from_api(d or {})), on_error=on_error)

    # ---------- projects ----------

    def projects(self, email: str, on_done: Callable[[List[Project]], None], on_error: OnError = None) -> None:
        self.projects_page(email, lambda projects, _total: on_done(projects), on_error=on_error)

    def abort(self, request_id: int) -> None:
        """Cancel a pending request by the id an endpoint method returned."""
        self.http.abort(request_id)

    def projects_page(self, email: str, on_done: Callable[[List[Project], int], None], on_error: OnError = None,
                      query: str = "", offset: int = 0, limit: int = PROJECTS_PAGE_SIZE) -> int:
        """One page of projects, most recently updated first; `query` filters by name on the server."""
        body = {"limit": limit, "offset": offset, "sortBy": "UPDATED", "sortOrder": "DESC"}
        if query.strip():
            body["filter"] = query.strip()
        return self.http.post("projects/page", body, on_error=on_error,
                              on_success=lambda d: on_done(
                                  [Project.from_api(p, email) for p in (d or {}).get("results") or []],
                                  int((d or {}).get("total") or 0)))

    def starred_projects(self, email: str, on_done: Callable[[List[Project]], None], on_error: OnError = None) -> None:
        """The projects the user starred, here or in Mapflow Web (POST /projects/starred, paged like
        /projects/page; a plain list is read too)."""
        def done(data):
            items = data if isinstance(data, list) else (data or {}).get("results") or []
            on_done([Project.from_api(p, email) for p in items if isinstance(p, dict)])
        self.http.post("projects/starred", {"limit": 100, "offset": 0, "sortBy": "UPDATED", "sortOrder": "DESC"},
                       on_success=done, on_error=on_error)

    def star_project(self, project_id: str, starred: bool, on_done: Callable, on_error: OnError = None) -> None:
        """Pin (star) a project, as Mapflow Web does: POST to star it, DELETE to unstar."""
        call = self.http.post if starred else self.http.delete
        call(f"projects/{project_id}/starred", on_success=on_done, on_error=on_error)

    def create_project(self, name: str, description: str, email: str, on_done: Callable[[Project], None],
                       on_error: OnError = None) -> None:
        body = {"name": name}
        if description:
            body["description"] = description
        self.http.post("projects", body, on_error=on_error,
                       on_success=lambda d: on_done(Project.from_api(d or {}, email)))

    def project(self, project_id: str, email: str, on_done: Callable[[Project], None],
                on_error: OnError = None) -> None:
        self.http.get(f"projects/{project_id}", on_error=on_error,
                      on_success=lambda d: on_done(Project.from_api(d or {}, email)))

    # ---------- processings ----------

    def processings(self, project_id: str, on_done: Callable[[List[Processing], int], None],
                    on_error: OnError = None, limit: int = PROCESSINGS_PAGE_SIZE, offset: int = 0) -> None:
        body = {"limit": limit, "offset": offset, "sortBy": "CREATED", "sortOrder": "DESC"}
        self.http.post(f"projects/{project_id}/processings/v2/page", body, on_error=on_error,
                       on_success=lambda d: on_done([Processing.from_api(p) for p in (d or {}).get("results") or []],
                                                    int((d or {}).get("total") or 0)))

    def processing(self, processing_id: str, on_done: Callable[[Processing], None], on_error: OnError = None) -> None:
        self.http.get(f"processings/{processing_id}/v2", on_error=on_error,
                      on_success=lambda d: on_done(Processing.from_api(d or {})))

    def cost(self, payload: dict, on_done: Callable[[int], None], on_error: OnError = None) -> int:
        return self.http.post("processing/cost/v2", payload, parse="text", on_error=on_error,
                              on_success=lambda text: on_done(int(float(text.strip().strip('"')))))

    def start(self, payload: dict, on_done: Callable[[Optional[Processing]], None], on_error: OnError = None) -> None:
        def done(data):
            on_done(Processing.from_api(data) if isinstance(data, dict) and data.get("id") else None)
        self.http.post("processings/v2", payload, on_success=done, on_error=on_error, timeout=60)

    def restart(self, processing_id: str, on_done: Callable, on_error: OnError = None) -> None:
        self.http.post(f"processings/{processing_id}/restart/v2", on_success=on_done, on_error=on_error)

    def rename(self, processing: Processing, name: str, description: str, on_done: Callable,
               on_error: OnError = None) -> None:
        self.http.put(f"processings/{processing.id}/v2", {"name": name, "description": description},
                      on_success=on_done, on_error=on_error)

    def delete(self, processing_id: str, on_done: Callable, on_error: OnError = None) -> None:
        self.http.delete(f"processings/{processing_id}", on_success=on_done, on_error=on_error, parse="text")

    def rate(self, processing_id: str, rating: int, feedback: str, on_done: Callable, on_error: OnError = None) -> None:
        self.http.put(f"processings/{processing_id}/rate", {"rating": rating, "feedback": feedback},
                      on_success=on_done, on_error=on_error, parse="text")

    def download_result(self, processing_id: str, target: str, on_done: Callable[[str], None],
                        on_error: OnError = None, on_progress: Optional[Callable] = None) -> None:
        """The processing's features as GeoJSON, streamed to `target`."""
        self.http.download(f"processings/{processing_id}/result", target, on_success=on_done,
                           on_error=on_error, timeout=RESULT_TIMEOUT_S, on_progress=on_progress)

    def processing_aois(self, processing_id: str, on_done: Callable[[dict], None], on_error: OnError = None) -> None:
        """The processing's area as a FeatureCollection."""
        self.http.get(f"processings/{processing_id}/aois", on_success=lambda data: on_done(aois_geojson(data)),
                      on_error=on_error)

    def tilejson(self, url: str, on_done: Callable[[dict], None], on_error: OnError = None) -> None:
        self.http.get(url, on_success=on_done, on_error=on_error, timeout=20)

    # ---------- imagery ----------

    def search_catalog(self, request: dict, on_done: Callable[[List[CatalogImage], int], None],
                       on_error: OnError = None, offset: int = 0) -> None:
        body = {"limit": SEARCH_PAGE_SIZE, "offset": offset, "hideUnavailable": False, **request}
        self.http.post("catalog/meta", body, timeout=60, on_error=on_error,
                       on_success=lambda d: on_done([CatalogImage.from_api(i) for i in (d or {}).get("images") or []],
                                                    int((d or {}).get("total") or 0)))

    def mosaic_page(self, offset: int, limit: int, query: str, on_done: Callable[[List[Mosaic], int, bool], None],
                    on_error: OnError = None) -> None:
        """One page of the user's collections, newest first (GET rasters/mosaic/page). `query` searches the
        collections' and their images' names on the server; empty matches all (an empty name_contains is
        refused with 422, so it isn't sent). `on_done` gets (collections, total, has_next)."""
        params = {"offset": offset, "limit": limit, "sort": "created_at", "order": "desc"}
        if query.strip():
            params["name_contains"] = query.strip()

        def done(data) -> None:
            data = data if isinstance(data, dict) else {}
            items = [Mosaic.from_api(m) for m in data.get("items") or [] if isinstance(m, dict)]
            total = data.get("total")
            on_done(items, int(total) if isinstance(total, (int, float)) else len(items), bool(data.get("has_next")))
        self.http.get(f"rasters/mosaic/page?{urlencode(params)}", on_success=done, on_error=on_error)

    def mosaic(self, mosaic_id: str, on_done: Callable[[Mosaic], None], on_error: OnError = None) -> None:
        """One collection by id (GET rasters/mosaic/{id}); a 404 means it was deleted."""
        self.http.get(f"rasters/mosaic/{mosaic_id}", on_error=on_error,
                      on_success=lambda d: on_done(Mosaic.from_api(d if isinstance(d, dict) else {})))

    def mosaic_images(self, mosaic_id: str, on_done: Callable[[List[MosaicImage]], None],
                      on_error: OnError = None) -> None:
        self.http.get(f"rasters/mosaic/{mosaic_id}/image", on_error=on_error,
                      on_success=lambda d: on_done([MosaicImage.from_api(i) for i in (d or []) if isinstance(i, dict)]))

    def mosaic_image(self, image_id: str, on_done: Callable[[MosaicImage], None], on_error: OnError = None) -> None:
        self.http.get(f"rasters/image/{image_id}", on_error=on_error,
                      on_success=lambda d: on_done(MosaicImage.from_api(d or {})))

    def upload_to_new_mosaic(self, file_path: str, name: str, on_done: Callable[[dict], None],
                             on_error: OnError = None, on_progress: Optional[Callable] = None) -> None:
        self.http.upload(f"rasters/mosaic/image?name={quote(name)}&tags=", file_path,
                         on_success=on_done, on_error=on_error, on_progress=on_progress)

    def create_mosaic(self, name: str, tags: List[str], on_done: Callable[[dict], None],
                      on_error: OnError = None) -> None:
        """An empty My imagery collection (POST /rasters/mosaic {name, tags})."""
        self.http.post("rasters/mosaic", {"name": name, "tags": list(tags)}, on_success=on_done, on_error=on_error)

    def upload_to_mosaic(self, mosaic_id: str, file_path: str, on_done: Callable[[dict], None],
                         on_error: OnError = None, on_progress: Optional[Callable] = None,
                         allow_duplicate: bool = False) -> None:
        """One file into a collection. Without `allow_duplicate`, Mapflow refuses a file the collection already
        has (the error's params name it: filename, existing_image_id)."""
        query = "?allow_duplicate=true" if allow_duplicate else ""
        self.http.upload(f"rasters/mosaic/{mosaic_id}/image{query}", file_path,
                         on_success=on_done, on_error=on_error, on_progress=on_progress)

    def delete_mosaic(self, mosaic_id: str, on_done: Callable[[object], None], on_error: OnError = None) -> None:
        """A collection and its images (DELETE rasters/mosaic/{id})."""
        self.http.delete(f"rasters/mosaic/{mosaic_id}", on_success=on_done, on_error=on_error)

    def delete_image(self, image_id: str, on_done: Callable[[object], None], on_error: OnError = None) -> None:
        """One image of a collection; the collection stays, even empty (DELETE rasters/image/{id})."""
        self.http.delete(f"rasters/image/{image_id}", on_success=on_done, on_error=on_error)

    def validate_image(self, metadata: dict, on_done: Callable[[dict], None], on_error: OnError = None) -> None:
        """Ask Mapflow whether an image is acceptable before uploading it (POST rasters/validate-image-metadata,
        body: rasters.validation_request; answer: {compatible, reasons[], warnings[], needs_preprocessing, …})."""
        self.http.post("rasters/validate-image-metadata", metadata, on_success=lambda d: on_done(d or {}),
                       on_error=on_error)

    def preview(self, url: str, on_done: Callable[[bytes], None], on_error: OnError = None) -> None:
        self.http.get(url, on_success=on_done, on_error=on_error, parse="bytes", timeout=30)
