"""QGIS-tier tests: the AOI area limit follows the OPEN project's owner (user.aoiAreaLimit).

For a shared project the owner's limit applies, not the logged-in user's default-project limit,
so the limit is set from the project's `user` section when a project is entered and reset to None
on exit.
"""
from types import SimpleNamespace

from mapflow.schema.project import MapflowProject, MapflowProjectUser
from mapflow.functional.service.project_service import ProjectService


def test_project_parses_user_section():
    project = MapflowProject.from_dict({
        "id": "p1", "name": "N", "isDefault": False, "description": None,
        "user": {"aoiAreaLimit": 25000000, "areaLimit": 25000000, "role": "USER",
                 "email": "owner@example.io", "isCustomer": True},
    })
    assert isinstance(project.user, MapflowProjectUser)
    assert project.user.aoiAreaLimit == 25000000
    assert project.user.email == "owner@example.io"


def test_project_without_user_section_is_none():
    project = MapflowProject.from_dict(
        {"id": "p1", "name": "N", "isDefault": False, "description": None})
    assert project.user is None


def _service(initial=None):
    service = ProjectService.__new__(ProjectService)
    service.app_context = SimpleNamespace(aoi_area_limit=initial)
    return service


def test_apply_limit_from_owner_converts_sqm_to_sqkm():
    service = _service()
    service.apply_project_aoi_area_limit(
        SimpleNamespace(user=SimpleNamespace(aoiAreaLimit=25_000_000)))  # 25 sq.km
    assert service.app_context.aoi_area_limit == 25.0


def test_apply_limit_resets_to_none_on_exit():
    service = _service(initial=25.0)
    service.apply_project_aoi_area_limit(None)
    assert service.app_context.aoi_area_limit is None


def test_apply_limit_none_when_user_or_limit_absent():
    service = _service(initial=25.0)
    service.apply_project_aoi_area_limit(SimpleNamespace(user=None))
    assert service.app_context.aoi_area_limit is None

    service.app_context.aoi_area_limit = 25.0
    service.apply_project_aoi_area_limit(SimpleNamespace(user=SimpleNamespace(aoiAreaLimit=None)))
    assert service.app_context.aoi_area_limit is None
