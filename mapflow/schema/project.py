from typing import Optional, List
from dataclasses import dataclass

from ..entity.workflow_def import WorkflowDef
from .base import Serializable, SkipDataClass

@dataclass
class PostProjectSchema(Serializable):
    name: str
    description: Optional[str] = None

@dataclass
class CreateProjectSchema(PostProjectSchema):
    pass

@dataclass
class UpdateProjectSchema(PostProjectSchema):
    pass

@dataclass
class MapflowProject(SkipDataClass):
    id: str
    name: str
    isDefault: bool
    description: Optional[str]
    workflowDefs: Optional[List[dict]] = None

    def __post_init__(self):
        if self.workflowDefs:
            self.workflowDefs = [WorkflowDef.from_dict(item) for item in self.workflowDefs]
        else:
            self.workflowDefs = []
