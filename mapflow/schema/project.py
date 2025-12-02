from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict

from .base import Serializable, SkipDataClass
from .workflow_def import WorkflowDef
from ..config import Config


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

    def get_user_role(self, email):
        for owner in self.owners:
            if owner.email == email:
                 return UserRole.owner
        for user in self.users:
            if user.email == email:
                return UserRole(user.role)


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
    workflowDefs: Optional[dict] = None
    shareProject: Optional[ShareProject] = None
    updated: Optional[datetime] = None
    created: Optional[datetime] = None
    processingCounts: Optional[Dict[str, int]] = None
    total: Optional[int] = Config.PROJECTS_PAGE_LIMIT

    def __post_init__(self):
        if self.workflowDefs:
            self.workflowDefs = {item['id']: WorkflowDef.from_dict(item) for item in self.workflowDefs}
        else:
            self.workflowDefs = {}

        if self.shareProject:
            self.shareProject = ShareProject.from_dict(self.shareProject)
        else:
            self.shareProject = None
        if self.created and self.updated:
            self.created = datetime.fromisoformat(self.created.replace("Z", "+00:00"))
            self.updated = datetime.fromisoformat(self.updated.replace("Z", "+00:00"))
    
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
    
class ProjectSortBy(str, Enum):
    name = "NAME"
    created = "CREATED"
    updated = "UPDATED"

class ProjectSortOrder(str, Enum):
    ascending = "ASC"
    descending = "DESC"

@dataclass
class ProjectsRequest(Serializable):
    limit: int = Config.PROJECTS_PAGE_LIMIT
    offset: int = 0
    filter: Optional[str] = None
    sortBy: Optional[ProjectSortBy] = ProjectSortBy.updated
    sortOrder: Optional[ProjectSortOrder] = ProjectSortOrder.descending

@dataclass
class ProjectsResult(SkipDataClass):
    results: Optional[List[MapflowProject]] = None
    total: int = 0
    count: int = None

    def __post_init__(self):
        if self.results:
            self.results = [MapflowProject.from_dict(proj) for proj in self.results]
