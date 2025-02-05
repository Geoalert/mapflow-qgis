from dataclasses import dataclass
from typing import Optional, List, Dict
from enum import Enum

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
    role: str
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
class MapflowProjectInfo(SkipDataClass):
    id: str
    name: str
    ownerEmail: str

@dataclass
class MapflowProject(SkipDataClass):
    id: str
    name: str
    isDefault: bool
    description: Optional[str]
    workflowDefs: Optional[List[dict]] = None
    shareProject: Optional[Dict[str, ShareProject]] = None

    def __post_init__(self):
        if self.workflowDefs:
            self.workflowDefs = [WorkflowDef.from_dict(item) for item in self.workflowDefs]
        else:
            self.workflowDefs = []

        if self.shareProject:
            self.shareProject = ShareProject.from_dict(self.shareProject)
        else:
            self.shareProject = []
    
class UserRole(str, Enum):
    readonly = "readonly"
    contributor = "contributor"
    maintainer = "maintainer"
    owner = "owner"

    @property
    def can_start_processing(self):
        return self.value != UserRole.readonly

    @property
    def can_delete_rename_review_processing(self):
        return self.value in (UserRole.maintainer, UserRole.owner)
    
    @property
    def can_delete_rename_project(self):
        return self.value == UserRole.owner
