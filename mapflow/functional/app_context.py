from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, TYPE_CHECKING

from qgis.core import QgsGeometry, QgsVectorLayer, QgsProject, QgsSettings
from ..config import Config
from ..schema.project import UserRole
from ..schema.project import MapflowProject
from ..entity.provider import ProviderInterface

if TYPE_CHECKING:
    # Imported only for the string annotations below; kept under TYPE_CHECKING to
    # avoid runtime import cycles.
    from ..schema.billing import BillingType
    from ..schema.data_catalog import MosaicReturnSchema, ImageReturnSchema


@dataclass
class AppContext:
    """
    Shared application state accessible by all services.
    Represents current session state - not persisted.
    """
    
    # === Infrastructure ===
    server: str = ""
    project: Optional[QgsProject] = None
    plugin_name: str = ""
    plugin_version: str = ""
    temp_dir: Optional[str] = None
    config: Optional[Config] = None
    settings = QgsSettings()
    
    # === Project & Processing Selection ===
    project_id: Optional[str] = None
    current_project: Optional["MapflowProject"] = None
    user_role: Optional["UserRole"] = UserRole.owner
    selected_processing_ids: List[str] = field(default_factory=list)

    # === AOI State ===
    aoi: Optional[QgsGeometry] = None  # full AOI, used for search/metadata requests
    # AOI actually processed: the full AOI cropped to the selected image footprint(s). This is
    # what is sent for processing/cost (matches the displayed area); falls back to `aoi`.
    processing_aoi: Optional[QgsGeometry] = None
    aoi_size: Optional[float] = None
    aoi_layers: List[QgsVectorLayer] = field(default_factory=list)
    
    # === User/Account State ===
    is_admin: bool = False
    logged_in: bool = False
    username: str = ""
    password: str = ""
    # The logged-in user's id (from the login `user` section). Used to check template
    # ownership so a contributor can edit their OWN templates (template.userId == user_id).
    user_id: Optional[str] = None
    
    # === Billing & Limits ===
    billing_type: Optional["BillingType"] = None
    remaining_limit: float = 0.0
    remaining_credits: float = 0.0
    # None until a project is open; set from the open project's owner (user.aoiAreaLimit).
    aoi_area_limit: Optional[float] = None
    template_area_limit: float = 0.0
    # Max AOI area (sq.km) allowed for an immediate imagery search; above it the user is
    # offered a Planned Search instead. Zero/absent disables the client-side check.
    search_area_limit: float = 0.0
    max_aois_per_processing: int = 1
    review_workflow_enabled: bool = False

    # === Provider State ===
    data_provider: Optional["ProviderInterface"] = None
    # Minimum AOI area (sq km) per provider, by lowercased provider name — from /user/status.
    provider_min_areas: Dict[str, float] = field(default_factory=dict)
    # api-names of the search providers available to the user (from /user/status
    # `searchDataProviders`). Used by the local filter to hide results whose provider is not
    # available when "Search only through available providers" is on.
    search_data_providers: List[str] = field(default_factory=list)
    
    # === Imagery Search State ===
    search_provider: Optional["ProviderInterface"] = None
    # Id of the template whose results are currently shown in the search table (None for a
    # regular search). Used to decide whether "Start" runs a planned (template) processing.
    open_template_results_id: Optional[str] = None
    metadata_aoi: Optional[QgsGeometry] = None
    metadata_layer: Optional[QgsVectorLayer] = None
    meta_layer_table_connection = None
    search_footprints: Dict[str, Any] = field(default_factory=dict)
    search_page_offset: int = 0
    # Raw imagery-search results as returned by the API for the current view (regular search
    # or template) — a GeoJSON FeatureCollection with a per-feature ``local_index``. Retained
    # so the instant local filter can reorder/re-render the table (fit rows first, unfit rows
    # greyed at the bottom) without issuing a new request.
    search_result_geojson: Optional[Dict] = None
    # The filter parameters that actually fetched ``search_result_geojson`` (for a regular
    # search: what was sent to /catalog/meta; for a template: its stored searchParams). Used to
    # warn (the (!) indicator) when the current filter widgets are WIDER than what was fetched,
    # since local filtering cannot surface data the server never returned.
    search_baseline_filters: Optional[Dict] = None
    
    # === Preview State ===
    preview_dict: Dict[str, Any] = field(default_factory=dict)

    # === My Imagery State ===
    selected_mosaic: Optional["MosaicReturnSchema"] = None
    selected_image: Optional["ImageReturnSchema"] = None
    mosaics = Optional[Dict]
    images = Optional[List]

    # === Permissions ===
    allow_enable_processing = {'aoi_loaded': True, 
                               'my_mosaic_loaded': True, 
                               'my_image_loaded': True} # all true -> startProcessing button can be enabled

    def can_edit_template(self, template) -> bool:
        """Whether the current user may edit/control ``template`` — rename, update search
        params, manage its AOIs, exclude-from-search, and pause/resume/restart.

        Maintainers and owners may edit any template in the project (unchanged). A contributor
        may edit only their OWN templates (``template.userId`` == the logged-in ``user_id``),
        mirroring the backend, which lets contributors manage the planned processings they
        created. Readonly users may not edit any."""
        role = self.user_role
        # No shared-project role context (personal/default project, admin): full rights.
        if role is None:
            return True
        if role.can_delete_rename_review_processing:
            return True
        if role == UserRole.contributor and self.user_id is not None:
            return str(getattr(template, "userId", "")) == str(self.user_id)
        return False

    @property
    def workflow_defs(self):
        if self.current_project:
            return self.current_project.workflowDefs
        else:
            return None
        
    def get_workflow_def(self, wd_name):
        if not self.workflow_defs:
            return None
        else:
            workflow_def = None
            for wd in self.workflow_defs.values():
                if wd.name == wd_name:
                    workflow_def = wd
            return workflow_def
