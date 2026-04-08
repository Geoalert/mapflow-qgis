from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Dict, List, Optional, Any

from qgis.core import QgsGeometry, QgsVectorLayer, QgsProject, QgsSettings
from ..schema.project import UserRole
from ..config import Config

if TYPE_CHECKING:
    from ..schema.project import MapflowProject
    from ..schema.workflow_def import WorkflowDef
    from ..entity.billing import BillingType
    from ..entity.provider import ProviderInterface


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
    aoi: Optional[QgsGeometry] = None
    aoi_size: Optional[float] = None
    aoi_layers: List[QgsVectorLayer] = field(default_factory=list)
    
    # === User/Account State ===
    is_admin: bool = False
    logged_in: bool = False
    username: str = ""
    password: str = ""
    
    # === Billing & Limits ===
    billing_type: Optional["BillingType"] = None
    remaining_limit: float = 0.0
    remaining_credits: float = 0.0
    aoi_area_limit: float = 0.0
    max_aois_per_processing: int = 1
    review_workflow_enabled: bool = False

    # === Provider State ===
    data_provider: Optional["ProviderInterface"] = None
    
    # === Imagery Search State ===
    search_provider: Optional["ProviderInterface"] = None
    metadata_aoi: Optional[QgsGeometry] = None
    metadata_layer: Optional[QgsVectorLayer] = None
    meta_layer_table_connection = None
    search_footprints: Dict[str, Any] = field(default_factory=dict)
    search_page_offset: int = 0
    
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

    @property
    def workflow_defs(self):
        if self.current_project:
            return self.current_project.workflowDefs
        else:
            return None
        
    @property
    def zoom_selector(self):
        return self.config.ZOOM_SELECTOR.lower() == "true" if self.config else None

    def get_workflow_def(self, wd_name):
        if not self.workflow_defs:
            return None
        else:
            workflow_def = None
            for wd in self.workflow_defs.values():
                if wd.name == wd_name:
                    workflow_def = wd
            return workflow_def
