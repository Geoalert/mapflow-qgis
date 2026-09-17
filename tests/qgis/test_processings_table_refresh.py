"""QGIS-tier tests for who decides what the processings table shows.

One table, two views: the project's processings+templates, or an open template's AOIs+processings.
Deciding between them is navigation, so it belongs to `ProjectProcessingController` rather than to
either service — otherwise `ProcessingService` has to ask `TemplateService` which view is up while
`TemplateService` is already asking `ProcessingService` for everything else, and the two end up
mutually dependent (`spec/007_architecture.md` § Services, § Controllers).

Services therefore *ask* for a refresh and the controller performs it. These tests pin the choice,
and that one request produces exactly one fetch — the failure mode of routing every caller through
a signal is that the table quietly refetches twice per action.

Each ask also says what triggered it, as a request mode (`spec/005` § Request modes), and the fetch
must go out with that mode: the refresh timer, a page change and a refresh after a reply all end
here, and they tolerate a failure differently.
"""
from unittest.mock import MagicMock

import pytest
from PyQt5.QtCore import QObject, pyqtSignal

from mapflow.functional.controller.project_processing_controller import ProjectProcessingController
from mapflow.http import RequestMode


class _Asker(QObject):
    """Stands in for a service that asks for the table to be refreshed."""
    refreshRequested = pyqtSignal(object)
    rerenderRequested = pyqtSignal()
    templateRehydrateRequested = pyqtSignal()


@pytest.fixture
def controller():
    controller = ProjectProcessingController.__new__(ProjectProcessingController)
    # Needed for the connect tests below: a slot on an uninitialised QObject never fires.
    QObject.__init__(controller)
    controller.processing_service = MagicMock()
    controller.template_service = MagicMock()
    controller.template_service.in_template_mode = False
    controller.processing_view = MagicMock()
    controller.processing_view.sort_processings.return_value = ("CREATED", "DESC")
    return controller


def test_outside_a_template_the_project_list_is_fetched(controller):
    controller.refresh_table(RequestMode.INTERACTIVE)

    controller.processing_service.get_processings.assert_called_once_with(mode=RequestMode.INTERACTIVE)
    controller.template_service.refresh_template_view.assert_not_called()


def test_inside_a_template_the_template_view_is_refreshed(controller):
    controller.template_service.in_template_mode = True

    controller.refresh_table(RequestMode.BACKGROUND)

    controller.template_service.refresh_template_view.assert_called_once_with(mode=RequestMode.BACKGROUND)
    controller.processing_service.get_processings.assert_not_called()


@pytest.mark.parametrize("in_template_mode", [False, True])
def test_the_timer_tick_refreshes_as_a_poll(controller, in_template_mode):
    """The tick is the one trigger a single failure should not be reported for."""
    controller.template_service.in_template_mode = in_template_mode

    controller.poll_table()

    fetch = controller.template_service.refresh_template_view if in_template_mode \
        else controller.processing_service.get_processings
    fetch.assert_called_once_with(mode=RequestMode.POLL)


def test_the_sort_combo_refreshes_interactively(controller):
    controller.on_combo_sort_changed()

    controller.processing_service.get_processings.assert_called_once_with(mode=RequestMode.INTERACTIVE)


def test_a_sort_re_renders_the_rows_of_whichever_view_is_up(controller):
    controller.rerender_rows()
    assert controller.processing_service.combined_processing_rows.called
    assert not controller.template_service.combined_template_rows.called

    controller.processing_service.reset_mock()
    controller.template_service.in_template_mode = True

    controller.rerender_rows()
    assert controller.template_service.combined_template_rows.called
    assert not controller.processing_service.combined_processing_rows.called


def test_a_rehydrate_request_rebinds_the_template(controller):
    controller.rehydrate_template()

    controller.template_service.refresh_active_template.assert_called_once()


def test_one_request_produces_exactly_one_fetch_with_the_askers_mode(controller):
    """The point of routing everything through a signal is a single owner, not a second fetch."""
    asker = _Asker()
    asker.refreshRequested.connect(controller.refresh_table)

    asker.refreshRequested.emit(RequestMode.BACKGROUND)

    controller.processing_service.get_processings.assert_called_once_with(mode=RequestMode.BACKGROUND)


def test_both_services_asking_are_served_by_the_same_owner(controller):
    """A template action and a processing action must not take different refresh paths."""
    from_processings = _Asker()
    from_templates = _Asker()
    from_processings.refreshRequested.connect(controller.refresh_table)
    from_templates.refreshRequested.connect(controller.refresh_table)

    from_processings.refreshRequested.emit(RequestMode.INTERACTIVE)
    from_templates.refreshRequested.emit(RequestMode.BACKGROUND)

    assert controller.processing_service.get_processings.call_count == 2
