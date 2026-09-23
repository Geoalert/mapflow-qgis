"""The Search button's two modes, and the Seen split-button.

The Search button is a split button: "Search" runs an immediate search, "Plan search" creates a
template that keeps searching. `SearchView` owns the mode and the label; what the mode *means* for
a template — that one needs a project — is `TemplateController`'s, reached by signal so the search
tab never has to know the template region exists.
"""
from unittest.mock import MagicMock

import pytest
from PyQt5.QtWidgets import QToolButton

from mapflow.functional.view.search_view import SearchView


@pytest.fixture
def view():
    """Real QToolButtons for the two split-buttons: `QMenu(parent)` rejects a MagicMock parent,
    and `setDefaultAction` is what the Seen assertions read back."""
    view = SearchView.__new__(SearchView)
    dlg = MagicMock()
    dlg.getMetadata = QToolButton()
    dlg.markSeenButton = QToolButton()
    SearchView.__init__(view, dlg=dlg, config=MagicMock())
    return view


def test_the_default_mode_is_an_immediate_search(view):
    assert view.search_mode == "search"


def test_switching_to_plan_relabels_the_button(view):
    view.set_search_mode("plan")

    assert view.search_mode == "plan"
    assert view.dlg.getMetadata.text() == "Plan search"


def test_switching_back_relabels_it_again(view):
    view.set_search_mode("plan")
    view.set_search_mode("search")

    assert view.dlg.getMetadata.text() == "Search"


def test_every_mode_change_is_announced(view):
    announced = []
    view.searchModeChanged.connect(announced.append)

    view.set_search_mode("plan")
    view.set_search_mode("search")

    assert announced == ["plan", "search"]


def test_building_the_dropdown_leaves_it_in_search_mode(view):
    """The menu is built once at startup and must not leave the button in whichever mode the
    last action happened to be."""
    announced = []
    view.searchModeChanged.connect(announced.append)

    view.setup_search_mode_dropdown()

    assert view.search_mode == "search"
    assert announced == ["search"]
    assert [action.text() for action in view.dlg.getMetadata.menu().actions()] == [
        "Search", "Plan search"]


def test_choosing_plan_search_from_the_menu_switches_mode(view):
    view.setup_search_mode_dropdown()

    plan_action = view.dlg.getMetadata.menu().actions()[1]
    plan_action.trigger()

    assert view.search_mode == "plan"


def test_the_seen_button_wires_the_handlers_it_is_given(view):
    """A view may not reach into a controller, so marking images seen arrives as callables."""
    on_seen, on_seen_all = MagicMock(), MagicMock()

    view.setup_seen_dropdown(on_seen=on_seen, on_seen_all=on_seen_all)

    assert [action.text() for action in view.dlg.markSeenButton.menu().actions()] == [
        "Seen", "Seen all"]
    # The default action is the plain "Seen", so clicking the button body rather than the arrow
    # marks the selection rather than everything.
    assert view.dlg.markSeenButton.defaultAction().text() == "Seen"

    view.dlg.markSeenButton.defaultAction().trigger()
    on_seen.assert_called_once()
    on_seen_all.assert_not_called()


def test_seen_all_is_a_separate_action(view):
    on_seen, on_seen_all = MagicMock(), MagicMock()
    view.setup_seen_dropdown(on_seen=on_seen, on_seen_all=on_seen_all)

    view.dlg.markSeenButton.menu().actions()[1].trigger()

    on_seen_all.assert_called_once()
    on_seen.assert_not_called()
