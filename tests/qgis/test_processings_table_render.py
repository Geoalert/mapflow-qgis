"""QGIS-tier tests for the split between what fills the processings table and what draws it.

`ProcessingService` held the table: it read the sort combo, the filter box and the selected
rows, and called a view to render. A service may not do any of that (`spec/007_architecture.md`
§ Services), and the cost was concrete — `TemplateService` had to reach through
`ProcessingService.view` to learn what was selected, because that was the only place the
answer existed.

Now the service announces (`rowsChanged`, `pagerChanged`, …) and is *told* the three things it
used to read (`set_sort`, `set_filter`, `set_selected_ids`). These pin both halves: that the
service emits rather than draws, and that `ProjectProcessingController` draws what it hears.
"""
import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from PyQt5.QtCore import QObject, pyqtSignal

from mapflow.functional.controller.project_processing_controller import ProjectProcessingController
from mapflow.functional.service import processing_service as processing_service_module
from mapflow.functional.service.processing_service import ProcessingService
from mapflow.functional.service.template_service import TemplateService


def _service():
    service = ProcessingService.__new__(ProcessingService)
    QObject.__init__(service)  # everything the table shows leaves as a signal
    service.tr = lambda text: text
    service.api = MagicMock()
    service.view = MagicMock()
    service.iface = MagicMock()
    service.app_context = SimpleNamespace(current_project=SimpleNamespace(id="proj-1"),
                                          settings=MagicMock())
    service.processings = {}
    service.templates = {}
    service.processings_data = None
    service.processings_page_limit = 10
    service.processings_page_offset = 0
    service.processings_history = None
    service.processing_fetch_timer = MagicMock()
    service._delete_state = {}
    return service


def _response(payload):
    reply = MagicMock()
    reply.readAll.return_value.data.return_value = json.dumps(payload).encode()
    return reply


def _controller():
    controller = ProjectProcessingController.__new__(ProjectProcessingController)
    QObject.__init__(controller)
    controller.tr = lambda text: text
    controller.dlg = MagicMock()
    controller.processing_service = MagicMock()
    controller.template_service = MagicMock()
    controller.template_service.in_template_mode = False
    controller.processing_view = MagicMock()
    controller.processing_view.sort_processings.return_value = ("CREATED", "DESC")
    controller.processing_view.processings_filter = ""
    controller.processing_view.selected_processing_ids.return_value = []
    return controller


# ---------- the service announces the table, it does not draw it ----------

def test_opening_the_table_asks_for_a_loading_placeholder():
    service = _service()
    loading = []
    service.tableLoading.connect(lambda: loading.append(True))

    service.setup_processings_table()

    assert loading == [True]
    assert service.processings_page_offset == 0


def test_a_request_carries_the_pushed_sort_and_filter():
    """The widgets are read by the controller and handed over; nothing here reaches for them."""
    service = _service()
    service.set_sort("NAME", "ASC")
    service.set_filter("roads")

    service.get_processings()

    request = service.api.get_processings.call_args.kwargs["request_body"]
    assert (request.sortBy, request.sortOrder) == ("NAME", "ASC")
    assert request.terms == "roads"


def test_an_empty_filter_is_sent_as_no_filter():
    """`terms=""` would ask the server to match the empty string; the field must be omitted."""
    service = _service()
    service.set_filter("")

    service.get_processings()

    assert service.api.get_processings.call_args.kwargs["request_body"].terms is None


def test_a_request_in_flight_disables_the_pager():
    """Paging a list that is about to be replaced pages the wrong list."""
    service = _service()
    enabled = []
    service.pagerEnabled.connect(enabled.append)

    service.get_processings()

    assert enabled == [False]


def test_the_pager_is_announced_when_the_results_span_pages():
    service = _service()
    service.processings_page_offset = 20  # third page of ten
    pager = []
    service.pagerChanged.connect(lambda *a: pager.append(a))

    service.get_processings_callback(_response({"results": [], "total": 95, "count": 0}))

    assert pager == [(True, 3, 10)]


def test_the_pager_is_hidden_for_a_single_page():
    service = _service()
    pager = []
    service.pagerChanged.connect(lambda *a: pager.append(a))

    service.get_processings_callback(_response({"results": [], "total": 4, "count": 0}))

    assert pager == [(False, 1, 1)]


def test_the_rows_are_announced_once_the_templates_resolve():
    service = _service()
    service.app_context.current_project = None  # no template fetch: render immediately
    rendered = []
    service.rowsChanged.connect(rendered.append)

    service.get_processings_callback(_response({"results": [], "total": 0, "count": 0}))

    assert rendered == [[]]


def test_a_rename_is_announced_with_the_id_and_the_new_name():
    service = _service()
    service.save_processing = MagicMock()
    renamed = []
    service.processingRenamed.connect(lambda *a: renamed.append(a))
    renamed_dto = SimpleNamespace(id="p-1", name="Renamed")

    with patch.object(processing_service_module.ProcessingDTO, "from_dict",
                      return_value=renamed_dto):
        service.update_processing_callback(_response({"id": "p-1", "name": "Renamed"}))

    assert renamed == [("p-1", "Renamed")]
    assert service.processings["p-1"] is renamed_dto


def test_the_ids_that_were_deleted_are_announced_when_the_run_finishes():
    service = _service()
    deleted = []
    service.processingsDeleted.connect(deleted.append)

    service.delete_processings(response=None, items=[], deleted=["p-1", "p-2"], failed=[])

    assert deleted == [["p-1", "p-2"]]


# ---------- the sort is remembered, not re-read ----------

def test_the_rows_are_sorted_by_the_sort_the_request_used():
    """The reason sort is pushed rather than passed: `combined_processing_rows` runs in a
    callback, long after the controller read the combo. Re-reading the widget there would sort
    a reply by a sort the user picked while it was in flight."""
    service = _service()
    service.set_sort("NAME", "ASC")
    service.processings = {
        "p-1": SimpleNamespace(id="p-1", name="Beta", created=2),
        "p-2": SimpleNamespace(id="p-2", name="Alpha", created=1),
    }

    assert [p.name for p in service.combined_processing_rows()] == ["Alpha", "Beta"]

    service.set_sort("NAME", "DESC")
    assert [p.name for p in service.combined_processing_rows()] == ["Beta", "Alpha"]


def test_templates_are_listed_above_processings_whatever_the_sort():
    """A planned processing is the parent of the runs under it, so it heads the list."""
    service = _service()
    service.set_sort("NAME", "ASC")
    service.processings = {"p-1": SimpleNamespace(id="p-1", name="Alpha", created=1)}
    service.templates = {"t-1": SimpleNamespace(id="t-1", name="Zulu", createdAt=2)}

    assert [row.name for row in service.combined_processing_rows()] == ["Zulu", "Alpha"]


# ---------- the selection is pushed, and two services read it ----------

def test_the_selection_is_held_and_sliced_in_table_order():
    service = _service()
    service.set_selected_ids(["p-1", "p-2", "p-3"])

    assert service.selected_ids() == ["p-1", "p-2", "p-3"]
    assert service.selected_ids(limit=1) == ["p-1"]


def test_no_selection_reads_as_empty_before_anything_is_pushed():
    """Every `selected_*` call runs through this, including on a service the plugin has only
    just built."""
    assert ProcessingService.__new__(ProcessingService).selected_ids() == []


def test_the_template_service_resolves_the_same_selection():
    """It used to reach through `ProcessingService.view` for this — a service holding another
    service's view. The ids live on the service now, so it asks the service."""
    processing_service = _service()
    processing_service.set_selected_ids(["aoi-1"])
    template_service = TemplateService(app_context=MagicMock(),
                                       processing_service=processing_service)
    template_service.template_aois = {"aoi-1": "the AOI", "aoi-2": "another"}

    assert template_service.selected_aois() == ["the AOI"]


# ---------- the controller draws what it hears ----------

def test_the_controller_renders_the_rows_it_is_given():
    controller = _controller()
    rows = ["row"]

    controller.render_rows(rows)

    controller.processing_view.update_processing_table.assert_called_once_with(rows)


def test_every_render_re_syncs_the_selection():
    """A rebuild restores the selection with the table's signals blocked, so no selection
    signal fires — nothing else would notice that a selected row is gone."""
    controller = _controller()
    controller.processing_view.selected_processing_ids.return_value = ["p-1"]

    controller.render_rows([])

    controller.processing_service.set_selected_ids.assert_called_with(["p-1"])


def test_the_loading_placeholder_also_re_syncs_the_selection():
    controller = _controller()

    controller.render_loading()

    controller.processing_view.set_table_loading.assert_called_once()
    controller.processing_service.set_selected_ids.assert_called_with([])


def test_the_pager_is_shown_or_hidden_as_announced():
    controller = _controller()

    controller._render_processings_pager(True, 3, 10)
    controller.processing_view.show_processings_pages.assert_called_once_with(True, 3, 10)

    controller.processing_view.reset_mock()
    controller._render_processings_pager(False, 1, 1)
    controller.processing_view.show_processings_pages.assert_called_once_with(False)


def test_a_fetch_hands_over_the_sort_and_filter_first():
    controller = _controller()
    controller.processing_view.sort_processings.return_value = ("STATUS", "ASC")
    controller.processing_view.processings_filter = "roads"

    controller.refresh_table()

    controller.processing_service.set_sort.assert_called_once_with("STATUS", "ASC")
    controller.processing_service.set_filter.assert_called_once_with("roads")
    controller.processing_service.get_processings.assert_called_once()


def test_choosing_from_the_sort_combo_drops_the_column_override_and_refetches():
    """A column click overrides the combo; picking from the combo has to take the wheel back,
    or the list keeps arriving in the column's order."""
    controller = _controller()

    controller.on_combo_sort_changed(2)

    controller.processing_view.clear_header_sort.assert_called_once()
    controller.processing_service.get_processings.assert_called_once()


def test_a_column_sort_re_renders_without_a_request():
    """The rows are already held; asking the server again would only cost a round trip."""
    controller = _controller()
    controller.processing_service.combined_processing_rows.return_value = ["row"]

    controller.rerender_rows()

    controller.processing_service.get_processings.assert_not_called()
    controller.processing_view.update_processing_table.assert_called_once_with(["row"])


class _TemplateStub(QObject):
    """`TemplateService`, reduced to the signals the controller subscribes to."""
    refreshRequested = pyqtSignal()
    templateRowsChanged = pyqtSignal(object)
    pollIntervalChanged = pyqtSignal(int)
    templateOpened = pyqtSignal(object)
    templateClosed = pyqtSignal(object)
    visibleProcessingsChanged = pyqtSignal(object)

    in_template_mode = False


def test_setting_up_the_bindings_subscribes_to_all_of_them():
    """Asserted against a controller that really ran its wiring, not one whose connections the
    test made for it. A connection that silently stopped being made is invisible otherwise: the
    services still work in isolation, and every test that wires its own passes."""
    controller = _controller()
    template_service = _TemplateStub()
    controller.template_service = template_service

    controller._setup_processing_bindings()

    template = SimpleNamespace(id="t-1")
    template_service.templateOpened.emit(template)
    controller.processing_service.set_open_template.assert_called_once_with(template)

    template_service.visibleProcessingsChanged.emit({"p-1": "one"})
    controller.processing_service.set_visible_processings.assert_called_once_with({"p-1": "one"})

    template_service.templateClosed.emit(template)
    assert controller.processing_service.set_open_template.call_args.args == (None,)

    template_service.templateRowsChanged.emit(["row"])
    controller.processing_view.update_processing_table.assert_called_once_with(["row"])


def test_opening_the_table_hands_over_the_query_before_the_first_page():
    """`setup_processings_table` fetches immediately, so a push afterwards would arrive too
    late and the first page would come back under the previous project's sort."""
    controller = _controller()
    controller.processing_view.sort_processings.return_value = ("NAME", "ASC")

    controller.open_processings_table()

    called = [call[0] for call in controller.processing_service.mock_calls]
    assert called.index("set_sort") < called.index("setup_processings_table")
    controller.processing_service.set_sort.assert_called_once_with("NAME", "ASC")
