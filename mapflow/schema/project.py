from dataclasses import dataclass
from typing import Optional, List

from .base import Serializable, SkipDataClass
from ..entity.workflow_def import WorkflowDef


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
class ShareProjectUser(SkipDataClass):
    projectId: str
    role: str
    userId: str
    email: str

@dataclass
class ShareProject(SkipDataClass):
    owners: Optional[List[ShareProjectUser]]
    users: Optional[List[ShareProjectUser]]

    def __post_init__(self):
        if self.owners:
            self.owners = [ShareProjectUser.from_dict(item) for item in self.owners]
        if self.users:
            self.users = [ShareProjectUser.from_dict(item) for item in self.users]

@dataclass
class MapflowProject(SkipDataClass):
    id: str
    name: str
    isDefault: bool
    description: Optional[str]
    workflowDefs: Optional[List[dict]] = None
    shareProject: Optional[dict[ShareProject]] = None

    def __post_init__(self):
        if self.workflowDefs:
            self.workflowDefs = [WorkflowDef.from_dict(item) for item in self.workflowDefs]
        else:
            self.workflowDefs = []

        if self.shareProject:
            self.shareProject = ShareProject.from_dict(self.shareProject)
        else:
            self.shareProject = []
