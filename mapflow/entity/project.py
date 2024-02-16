from typing import List, Optional
from dataclasses import dataclass
from ..schema import SkipDataClass
from .workflow_def import WorkflowDef

@dataclass
class MapflowProject(SkipDataClass):
    id: str
    name: str
    workflowDefs: Optional[List[dict]] = None

    def __post_init__(self):
        if self.workflowDefs:
            self.workflowDefs = [WorkflowDef.from_dict(item) for item in self.workflowDefs]
        else:
            self.workflowDefs = []

