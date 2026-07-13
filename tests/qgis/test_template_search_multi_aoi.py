"""QGIS-tier tests for filtering template search results by multiple selected AOIs
(round-2 feedback 11; spec 002_F: selecting one or more AOI rows sends all their ids as
``aoiIds`` on the template images request; deselecting all restores the full results)."""
from types import SimpleNamespace
from unittest.mock import MagicMock

from mapflow.mapflow import Mapflow


def _plugin(selected_aois):
    plugin = Mapflow.__new__(Mapflow)
    plugin._template_search_aoi_filter = None
    template = SimpleNamespace(id="tpl-1", name="T1")
    plugin.processing_service = SimpleNamespace(
        in_template_mode=True,
        active_template=template,
        selected_aois=lambda: selected_aois,
    )
    plugin._load_template_search = MagicMock()
    return plugin, template


def _aoi(aoi_id):
    return SimpleNamespace(id=aoi_id)


def test_multiple_selected_aois_are_all_sent():
    plugin, template = _plugin([_aoi("a1"), _aoi("a2")])

    plugin.filter_search_by_selected_aoi()

    plugin._load_template_search.assert_called_once()
    _, kwargs = plugin._load_template_search.call_args
    assert set(kwargs["aoi_ids"]) == {"a1", "a2"}
    assert plugin._template_search_aoi_filter == frozenset({"a1", "a2"})


def test_no_selection_restores_full_results():
    plugin, template = _plugin([])
    plugin._template_search_aoi_filter = frozenset({"a1"})

    plugin.filter_search_by_selected_aoi()

    plugin._load_template_search.assert_called_once_with(template, aoi_ids=None)
    assert plugin._template_search_aoi_filter is None


def test_unchanged_selection_does_not_reload():
    plugin, _ = _plugin([_aoi("a1"), _aoi("a2")])
    plugin._template_search_aoi_filter = frozenset({"a1", "a2"})

    plugin.filter_search_by_selected_aoi()

    plugin._load_template_search.assert_not_called()


def test_reselection_order_independent():
    """Selecting the same AOIs in a different order must not trigger a reload."""
    plugin, _ = _plugin([_aoi("a2"), _aoi("a1")])
    plugin._template_search_aoi_filter = frozenset({"a1", "a2"})

    plugin.filter_search_by_selected_aoi()

    plugin._load_template_search.assert_not_called()


def test_not_in_template_mode_is_noop():
    plugin, _ = _plugin([_aoi("a1")])
    plugin.processing_service.in_template_mode = False

    plugin.filter_search_by_selected_aoi()

    plugin._load_template_search.assert_not_called()
