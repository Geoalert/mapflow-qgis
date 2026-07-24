"""QGIS-tier tests for the project table's combined "State" column.

The two former columns (Succeeded / Failed) plus the template count collapse into one column
rendered as a cell widget: an SVG icon + count for succeeded, failed and planned processings
(templates). See spec 002_A project table.
"""
from datetime import datetime, timezone
from types import SimpleNamespace

from PyQt5.QtWidgets import QTableWidget, QLabel

from mapflow.config import ConfigColumns
from mapflow.functional.view.project_view import ProjectView, build_project_state_widget


def _counts(widget):
    """The count strings shown in a state widget, in order (icon-only labels are skipped)."""
    return [lbl.text() for lbl in widget.findChildren(QLabel) if lbl.text()]


def test_state_widget_shows_counts_in_order():
    widget = build_project_state_widget(succeeded=5, failed=2, templates=3)
    assert _counts(widget) == ["5", "2", "3"]
    # Three icon labels (pixmap, no text) accompany the three counts.
    icon_labels = [lbl for lbl in widget.findChildren(QLabel) if not lbl.text()]
    assert len(icon_labels) == 3
    assert all(not lbl.pixmap().isNull() for lbl in icon_labels)


def _project(processing_counts, templates_count):
    ts = datetime(2026, 1, 2, 3, 4, tzinfo=timezone.utc)
    return SimpleNamespace(
        id="p-1", name="Demo",
        processingCounts=processing_counts, templatesCount=templates_count,
        shareProject=SimpleNamespace(owners=[SimpleNamespace(email="owner@example.com")]),
        updated=ts, created=ts,
    )


def _view():
    view = ProjectView.__new__(ProjectView)
    view.tr = lambda text: text
    view.columns_config = ConfigColumns()
    view.dlg = SimpleNamespace(projectsTable=QTableWidget())
    return view


def test_setup_projects_table_renders_single_state_column():
    view = _view()

    view.setup_projects_table([_project({"succeeded": 4, "failed": 1}, 2)])

    table = view.dlg.projectsTable
    # ID, Project, State, Author, Updated at, Created at -> 6 columns (was 7).
    assert table.columnCount() == 6
    assert table.horizontalHeaderItem(2).text() == "State"
    assert _counts(table.cellWidget(0, 2)) == ["4", "1", "2"]
    # Author shifted from column 4 to column 3.
    assert table.item(0, 3).text() == "owner@example.com"


def test_setup_projects_table_tolerates_missing_counts():
    view = _view()

    # processingCounts null and templatesCount null (as in a fresh project) must not crash.
    view.setup_projects_table([_project(None, None)])

    assert _counts(view.dlg.projectsTable.cellWidget(0, 2)) == ["0", "0", "0"]
