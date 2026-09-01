"""QGIS-tier tests for template search-results pagination (round-2 feedback 5). Template
results previously filled the table but never toggled the page navigation; now the shared
pager is driven from the response's total/limit/offset and next/prev re-fetch the template
page (preserving the AOI filter), rather than falling through to a regular search."""
from types import SimpleNamespace
from unittest.mock import MagicMock

from mapflow.config import Config, ConfigColumns
from mapflow.functional.service.search_service import SearchService
from mapflow.functional.service.template_service import TemplateService
from mapflow.functional.view.search_view import SearchView
from mapflow.mapflow import Mapflow


def _service(page_limit=5):
    service = SearchService(iface=MagicMock(),
                            app_context=MagicMock(),
                            http=MagicMock(),
                            plugin_dir="",
                            config=Config,
                            config_search_columns=ConfigColumns(),
                            result_loader=MagicMock(),
                            provider_service=MagicMock())
    service.page_offset = 0
    service.page_limit = page_limit
    return service


def _plugin(in_template_mode=True):
    plugin = Mapflow.__new__(Mapflow)
    plugin.dlg = MagicMock()
    plugin.search_view = SearchView(dlg=plugin.dlg, config=MagicMock())
    plugin.search_service = _service()
    plugin.template_service = SimpleNamespace(in_template_mode=in_template_mode,
                                              active_template=None)
    return plugin


# The pager computation is `SearchService.update_pager`; turning its answer into enabled buttons
# is `SearchView`. Wiring them here is what the plugin does, so the assertions stay on the dialog.

def _pager(view):
    """A service whose pager signals drive `view`, as mapflow.py wires them."""
    service = _service()
    service.pagerChanged.connect(view.show_pages)
    service.pagerHidden.connect(view.hide_pages)
    return service


def test_pager_shown_and_first_page_disables_left():
    plugin = _plugin()
    service = _pager(plugin.search_view)

    service.update_pager(total=12, limit=5, offset=0)

    plugin.dlg.enable_search_pages.assert_called_once_with(True, 1, 3)
    plugin.dlg.searchLeftButton.setEnabled.assert_called_once_with(False)  # first page
    plugin.dlg.searchRightButton.setEnabled.assert_called_once_with(True)


def test_pager_last_page_disables_right():
    plugin = _plugin()
    service = _pager(plugin.search_view)

    service.update_pager(total=12, limit=5, offset=10)  # page 3 of 3

    plugin.dlg.enable_search_pages.assert_called_once_with(True, 3, 3)
    plugin.dlg.searchRightButton.setEnabled.assert_called_once_with(False)
    plugin.dlg.searchLeftButton.setEnabled.assert_called_once_with(True)


def test_pager_hidden_when_single_page():
    plugin = _plugin()
    service = _pager(plugin.search_view)

    service.update_pager(total=4, limit=5, offset=0)

    plugin.dlg.enable_search_pages.assert_called_once_with(False)


def test_pager_hidden_when_results_exactly_fill_one_page():
    """The boundary: `total == limit` is still one page. A `>=` here would show a two-page pager
    whose second page is empty — and `total < limit` alone does not catch that."""
    plugin = _plugin()
    service = _pager(plugin.search_view)

    service.update_pager(total=5, limit=5, offset=0)

    plugin.dlg.enable_search_pages.assert_called_once_with(False)


# Which endpoint serves the page depends on where the results came from. That branch stays in
# `mapflow.py` until the regular search moves too, so it is still asserted on the plugin — but the
# template half now goes through `TemplateController`.

def test_next_page_in_template_mode_refetches_template_page():
    plugin = _plugin(in_template_mode=True)
    plugin.template_controller = MagicMock()
    plugin.get_metadata = MagicMock()
    plugin.search_service.page_offset = 0

    plugin.show_search_next_page()

    plugin.template_controller.load_search_page.assert_called_once_with(5)
    plugin.get_metadata.assert_not_called()


def test_prev_page_in_template_mode_refetches_template_page():
    plugin = _plugin(in_template_mode=True)
    plugin.template_controller = MagicMock()
    plugin.get_metadata = MagicMock()
    plugin.search_service.page_offset = 10

    plugin.show_search_previous_page()

    plugin.template_controller.load_search_page.assert_called_once_with(5)


def test_next_page_outside_template_mode_uses_regular_search():
    plugin = _plugin(in_template_mode=False)
    plugin.template_controller = MagicMock()
    plugin.get_metadata = MagicMock()
    plugin.search_service.page_offset = 5

    plugin.show_search_next_page()

    plugin.get_metadata.assert_called_once_with(offset=10)
    plugin.template_controller.load_search_page.assert_not_called()


def _template_service(active_template=None, aoi_filter=None):
    service = TemplateService(app_context=MagicMock(), processing_service=MagicMock())
    service.active_template = active_template
    service.search_aoi_filter = aoi_filter
    service.load_search = MagicMock()
    return service


def test_load_search_page_preserves_aoi_filter_and_offset():
    service = _template_service(active_template=SimpleNamespace(id="tpl-1"),
                                aoi_filter=frozenset({"a1", "a2"}))

    service.load_search_page(offset=10)

    service.load_search.assert_called_once()
    _, kwargs = service.load_search.call_args
    assert set(kwargs["aoi_ids"]) == {"a1", "a2"}
    assert kwargs["offset"] == 10


def test_load_search_page_noop_without_active_template():
    service = _template_service(active_template=None)

    service.load_search_page(offset=5)

    service.load_search.assert_not_called()
