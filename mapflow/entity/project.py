from typing import List, Optional
from dataclasses import dataclass
from ..schema import SkipDataClass
from .workflow_def import WorkflowDef

@dataclass
class MapflowProject(SkipDataClass):
    id: str
    name: str
    workflow_defs: Optional[List[dict]] = None

    def __post_init__(self):
        if self.workflow_defs:
            self.workflow_defs = [WorkflowDef.from_dict(item) for item in self.workflow_defs]
        else:
            self.workflow_defs = []

