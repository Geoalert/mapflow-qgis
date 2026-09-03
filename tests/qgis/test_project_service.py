"""QGIS-tier tests for the projects panel: what the service announces, and what the controller
renders from it.

`ProjectService` held the dialog and built its own view, so none of this was reachable without a
plugin — the behavioural journey in `tests/qgis/behavioral/test_projects_and_processings.py` was
the only cover. These pin the contract between the two halves: the service decides *what* the
panel shows and emits it; the controller reads the widgets and renders.
"""
import json
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from PyQt5.QtCore import QObject

from mapflow.functional.controller.project_processing_controller import ProjectProcessingController
from mapflow.functional.service.project_service import ProjectService
from mapflow.schema.project import ProjectSortBy, ProjectSortOrder


def _service(total=1, page_limit=5):
    service = ProjectService.__new__(ProjectService)
    QObject.__init__(service)  # the panel updates are signals
    service.tr = lambda text: text
    service.api = MagicMock()
    service.config = SimpleNamespace(MAPFLOW_ENV="production", DEFAULT_MODEL="Buildings")
    service.app_context = SimpleNamespace(settings=MagicMock(), project_id=None,
                                          current_project=None, workflow_defs={},
                                          plugin_name="Mapflow", username="me@example.com",
                                          user_role=None, aoi_area_limit=None)
    service.projects = {}
    service.projects_data = SimpleNamespace(total=total)
    service.projects_page_limit = page_limit
    service.projects_page_offset = 0
    service._last_filter = ""
    service.area_calculator_service = MagicMock()
    return service


def _response(payload):
    reply = MagicMock()
    reply.readAll.return_value.data.return_value = json.dumps(payload).encode()
    return reply


def _projects_payload(count, total=None):
    """A full project dict: `MapflowProject.from_dict` rejects partial ones, and a thin fixture
    fails as a TypeError deep in the parse rather than as the thing under test."""
    return {"results": [{"id": f"p-{i}",
                         "name": f"Project {i}",
                         "isDefault": False,
                         "description": "",
                         "workflowDefs": [],
                         "created": "2026-01-01T00:00:00.000Z",
                         "updated": "2026-01-01T00:00:00.000Z"}
                        for i in range(count)],
            "total": count if total is None else total}


# ---------- requesting a page ----------

def test_the_request_carries_the_sort_and_filter_it_was_given():
    """The panel's widgets are read by the caller; nothing here reaches for them."""
    service = _service()

    service.get_projects(ProjectSortBy.name, ProjectSortOrder.ascending, "roads")

    request = service.api.get_projects.call_args.args[0]
    assert request.filter == "roads"
    assert request.sortBy == ProjectSortBy.name
    assert request.sortOrder == ProjectSortOrder.ascending


def test_a_request_disables_the_pager_and_locks_the_selection():
    """Both prevent acting on a list that is about to be replaced."""
    service = _service()
    pager, locks = [], []
    service.pagerChanged.connect(lambda *a: pager.append(a))
    service.selectionLocked.connect(locks.append)

    service.get_projects()

    assert pager == [(False, 1, 1)]
    assert locks == [True]


def test_an_offset_past_the_end_falls_back_to_the_first_page():
    service = _service(total=3)
    service.projects_page_offset = 99

    service.get_projects()

    assert service.projects_page_offset == 0


def test_paging_moves_the_cursor_without_requesting():
    """Re-requesting needs the panel's sort and filter, so the caller asks — this only moves."""
    service = _service(page_limit=5)

    service.to_next_page()
    assert service.projects_page_offset == 5

    service.to_previous_page()
    assert service.projects_page_offset == 0


def test_filtering_returns_to_the_first_page_and_forgets_the_open_project():
    service = _service()
    service.projects_page_offset = 10
    service.app_context.project_id = "p-1"

    service.to_first_page()

    assert service.projects_page_offset == 0
    assert service.app_context.project_id is None


# ---------- the response ----------

def test_the_results_are_announced_for_the_table():
    service = _service()
    shown = []
    service.projectsLoaded.connect(shown.append)

    service.get_projects_callback(_response(_projects_payload(2)))

    assert len(shown[0]) == 2
    assert set(service.projects) == {"p-0", "p-1"}


def test_the_pager_reports_the_page_count():
    service = _service(page_limit=5)
    pages = []
    service.pagerChanged.connect(lambda *a: pages.append(a))
    service.projects_page_offset = 5

    service.get_projects_callback(_response(_projects_payload(5, total=12)))

    # 12 over 5 per page = 3 pages; offset 5 is the second.
    assert pages[-1] == (True, 2, 3)


def test_a_short_page_hides_the_pager():
    service = _service(page_limit=5)
    pages = []
    service.pagerChanged.connect(lambda *a: pages.append(a))

    service.get_projects_callback(_response(_projects_payload(2, total=2)))

    assert pages[-1] == (False, 1, 1)


def test_an_empty_unfiltered_result_asks_again_without_parameters():
    """Every account has at least a Default project, so nothing-at-all means the request carried
    a stale page rather than the account being empty."""
    service = _service()
    service._last_filter = ""

    service.get_projects_callback(_response(_projects_payload(0, total=0)))

    assert service.api.get_projects.call_count == 1


def test_an_empty_filtered_result_is_left_alone():
    """A filter that matches nothing is a real answer — re-requesting would discard it."""
    service = _service()
    service._last_filter = "no-such-project"

    service.get_projects_callback(_response(_projects_payload(0, total=0)))

    service.api.get_projects.assert_not_called()


def test_the_selection_unlocks_once_the_list_has_arrived():
    service = _service()
    locks = []
    service.selectionLocked.connect(locks.append)

    service.get_projects_callback(_response(_projects_payload(1, total=1)))

    assert locks[-1] is False


# ---------- which project is open ----------

def test_selecting_a_project_announces_it():
    service = _service()
    service.projects = {"p-1": SimpleNamespace(id="p-1", name="Roads", shareProject=None,
                                               isDefault=False, workflowDefs={}, user=None)}
    announced = []
    service.currentProjectChanged.connect(announced.append)

    service.on_project_change("p-1")

    assert announced[0].name == "Roads"
    assert service.app_context.project_id == "p-1"


def test_clearing_the_selection_announces_no_project():
    service = _service()
    announced, titles = [], []
    service.currentProjectChanged.connect(announced.append)
    service.windowTitleChanged.connect(titles.append)

    service.on_project_change(None)

    assert announced == [None]
    assert titles  # the header drops the project name
    assert service.app_context.project_id is None


def test_reselecting_the_open_project_does_nothing():
    """Its workflow defs are already set up; redoing it re-requests for no reason."""
    service = _service()
    service.app_context.project_id = "p-1"
    service.app_context.workflow_defs = {"wd": object()}
    announced = []
    service.currentProjectChanged.connect(announced.append)

    service.on_project_change("p-1")

    assert announced == []


def test_reselecting_at_startup_is_not_skipped():
    """Same id, but no workflow defs yet — the project is not set up, so it must proceed."""
    service = _service()
    service.app_context.project_id = "p-1"
    service.app_context.workflow_defs = {}
    service.projects = {"p-1": SimpleNamespace(id="p-1", name="Roads", shareProject=None,
                                               isDefault=False, workflowDefs={}, user=None)}
    announced = []
    service.currentProjectChanged.connect(announced.append)

    service.on_project_change("p-1")

    assert announced and announced[0].name == "Roads"


# ---------- what may be done with it ----------

@pytest.mark.parametrize("project, role, expect_editable, expect_reason", [
    (None, None, False, "No project selected"),
    (SimpleNamespace(isDefault=True), SimpleNamespace(can_delete_rename_project=True, value="owner"),
     False, "default project"),
    (SimpleNamespace(isDefault=False), SimpleNamespace(can_delete_rename_project=False, value="viewer"),
     False, "Not enough rights"),
    (SimpleNamespace(isDefault=False), SimpleNamespace(can_delete_rename_project=True, value="owner"),
     True, ""),
])
def test_the_rename_delete_controls_follow_the_project_and_the_role(
        project, role, expect_editable, expect_reason):
    service = _service()
    service.app_context.current_project = project
    service.app_context.user_role = role
    announced = []
    service.projectChangeRightsChanged.connect(lambda *a: announced.append(a))

    service.setup_project_change_rights()

    reason, editable = announced[0]
    assert editable is expect_editable
    assert expect_reason in reason


def test_deleting_locks_the_selection_before_the_request():
    """The list renumbers when this returns; a click in that window selects whatever lands on the
    row the user aimed at."""
    service = _service()
    locks = []
    service.selectionLocked.connect(locks.append)

    service.delete_project("p-1")

    assert locks == [True]
    service.api.delete_project.assert_called_once()


# ---------- the controller's half ----------

def _controller():
    controller = ProjectProcessingController.__new__(ProjectProcessingController)
    QObject.__init__(controller)
    controller.tr = lambda text: text
    controller.project_service = MagicMock()
    controller.project_view = MagicMock()
    controller.app_context = SimpleNamespace(project_id=None)
    controller.config = SimpleNamespace(DEFAULT_MODEL="Buildings")
    return controller


def test_the_switch_arrow_follows_whether_a_project_is_open():
    controller = _controller()

    controller._render_current_project(None)
    assert controller.project_view.enable_switch_to_processings.call_args.args[0] is False

    controller._render_current_project(SimpleNamespace(name="Roads", workflowDefs={}))
    assert controller.project_view.enable_switch_to_processings.call_args.args[0] is True


def test_the_open_projects_name_is_elided_by_the_view():
    """The label's width is only knowable from the widget, so the view does the eliding — the
    controller hands it the raw name."""
    controller = _controller()

    controller._render_current_project(SimpleNamespace(name="A very long project name",
                                                       workflowDefs={}))

    controller.project_view.show_current_project.assert_called_once_with("A very long project name")


def test_the_models_are_repopulated_only_when_the_project_has_them():
    controller = _controller()

    controller._render_current_project(SimpleNamespace(name="Roads", workflowDefs={}))
    controller.project_view.setup_workflow_defs.assert_not_called()

    controller._render_current_project(SimpleNamespace(name="Roads", workflowDefs={"wd": object()}))
    controller.project_view.setup_workflow_defs.assert_called_once()


def test_refreshing_reads_the_sort_and_filter_off_the_panel():
    controller = _controller()
    controller.project_view.sort_projects.return_value = ("NAME", "ASC")
    controller.project_view.projects_filter = "roads"

    controller.refresh_projects()

    controller.project_service.get_projects.assert_called_once_with("NAME", "ASC", "roads")


def test_paging_moves_the_cursor_then_re_requests():
    controller = _controller()
    controller.project_view.sort_projects.return_value = ("UPDATED", "DESC")
    controller.project_view.projects_filter = ""

    controller.show_projects_next_page()

    controller.project_service.to_next_page.assert_called_once()
    controller.project_service.get_projects.assert_called_once()


def test_leaving_a_project_sends_a_real_sort_not_a_flag():
    """`show_projects` takes a bool for "restore the saved page". Passing it straight into
    `get_projects` puts it where `sort_by` goes, and the backend rejects the body with
    `Invalid value for: body (String at 'sortBy')` — a 400 the user sees on every exit."""
    controller = _controller()
    controller.processing_service = MagicMock()
    controller.project_view.sort_projects.return_value = ("UPDATED", "DESC")
    controller.project_view.projects_filter = ""

    controller.show_projects(open_saved_page=False)

    sort_by = controller.project_service.get_projects.call_args.args[0]
    assert not isinstance(sort_by, bool)
    assert sort_by == "UPDATED"


def test_returning_to_projects_restores_the_page_the_user_left():
    controller = _controller()
    controller.processing_service = MagicMock()
    controller.project_service.saved_projects_page.return_value = {
        'offset': 20, 'sort_by': ProjectSortBy.name,
        'sort_order': ProjectSortOrder.ascending, 'filter': "roads"}
    controller.project_service.sort_combo_index.return_value = 0

    controller.show_projects(open_saved_page=True)

    # The widgets are set to match the query the request will carry...
    controller.project_view.set_projects_filter.assert_called_once_with("roads")
    controller.project_view.set_sort_index.assert_called_once_with(0)
    # ...and the request asks for the remembered page, not the first one.
    kwargs = controller.project_service.get_projects.call_args.kwargs
    assert kwargs["offset"] == 20


def test_a_restored_page_with_no_filter_leaves_the_filter_box_alone():
    controller = _controller()
    controller.processing_service = MagicMock()
    controller.project_service.saved_projects_page.return_value = {
        'offset': 0, 'sort_by': ProjectSortBy.updated,
        'sort_order': ProjectSortOrder.descending, 'filter': ""}
    controller.project_service.sort_combo_index.return_value = 4

    controller.show_projects(open_saved_page=True)

    controller.project_view.set_projects_filter.assert_not_called()


def test_an_explicit_offset_overrides_the_current_page():
    service = _service(total=50)
    service.projects_page_offset = 5

    service.get_projects(ProjectSortBy.name, ProjectSortOrder.ascending, "", offset=20)

    assert service.api.get_projects.call_args.args[0].offset == 20


def test_a_saved_page_past_the_end_falls_back_to_the_first():
    """A remembered page outlives the projects it referred to: deleting enough of them leaves the
    saved offset pointing past the end, and asking for it returns nothing at all."""
    service = _service(total=3)

    service.get_projects(ProjectSortBy.name, ProjectSortOrder.ascending, "", offset=20)

    assert service.api.get_projects.call_args.args[0].offset == 0


def test_the_sort_combo_index_round_trips_every_pair():
    """`sort_combo_index` is the inverse of `ProjectView.sort_projects`; each (field, direction)
    pair must land on exactly one row, or restoring a saved page selects the wrong sort."""
    seen = set()
    for sort_by in (ProjectSortBy.name, ProjectSortBy.created, ProjectSortBy.updated):
        for sort_order in (ProjectSortOrder.ascending, ProjectSortOrder.descending):
            seen.add(ProjectService.sort_combo_index(sort_by, sort_order))
    assert seen == {0, 1, 2, 3, 4, 5}


def test_unlocking_the_selection_restores_the_open_project():
    controller = _controller()
    controller.app_context.project_id = "p-1"

    controller._lock_projects_selection(False)

    controller.project_view.unlock_projects_selection.assert_called_once()
    controller.project_view.select_project.assert_called_once_with("p-1")
