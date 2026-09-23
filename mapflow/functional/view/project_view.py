from typing import List

from PyQt5.QtCore import QObject, Qt
from PyQt5.QtWidgets import (QWidget, QTableWidget, QTableWidgetItem, QAbstractItemView,
                             QHeaderView, QHBoxLayout, QLabel)

from ...dialogs.main_dialog import MainDialog
from ...dialogs import icons
from ...config import ConfigColumns
from ...schema import WorkflowDef
from ...schema.project import MapflowProject, ProjectSortBy, ProjectSortOrder


# Icon size (px) for the project "State" column markers.
STATE_ICON_SIZE = 14


def build_project_state_widget(succeeded: int, failed: int, templates: int) -> QWidget:
    """A one-line cell for the project "State" column: succeeded / failed processings and
    planned processings (templates), each as an SVG icon followed by its count.

    Rendered as a cell widget (not a plain item) because a QTableWidgetItem holds only one icon.
    Made transparent to mouse events so a click still selects the row for opening the project."""
    widget = QWidget()
    layout = QHBoxLayout(widget)
    layout.setContentsMargins(6, 0, 6, 0)
    layout.setSpacing(4)
    pairs = ((icons.ok_circle_icon, succeeded),
             (icons.close_circle_icon, failed),
             (icons.clock_play_icon, templates))
    for index, (icon, count) in enumerate(pairs):
        if index:
            layout.addSpacing(10)
        icon_label = QLabel()
        icon_label.setPixmap(icon.pixmap(STATE_ICON_SIZE, STATE_ICON_SIZE))
        icon_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        layout.addWidget(icon_label)
        count_label = QLabel(str(count))
        count_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        layout.addWidget(count_label)
    layout.addStretch()
    widget.setAttribute(Qt.WA_TransparentForMouseEvents)
    return widget


class ProjectView(QObject):
    def __init__(self, dlg: MainDialog):
        super().__init__()
        self.dlg = dlg
        self.dlg.projectsPreviousPageButton.setIcon(icons.arrow_left_icon)
        self.dlg.projectsNextPageButton.setIcon(icons.arrow_right_icon)
        # Buttons < and > in projects and processings are different because of stacked widget
        # So we specify to always disabled buttons just for looks
        self.dlg.switchProjectsButton.setIcon(icons.arrow_left_icon)
        self.dlg.switchProcessingsButton.setIcon(icons.arrow_right_icon)
        self.dlg.switchProjectsFakeButton.setIcon(icons.arrow_left_icon)
        self.dlg.switchProcessingsFakeButton.setIcon(icons.arrow_right_icon)
        self.dlg.switchProjectsButton.setToolTip(self.tr("See projects"))
        self.dlg.switchProjectsFakeButton.setToolTip(self.tr("See projects"))
        self.dlg.switchProcessingsButton.setToolTip(self.tr("See processings"))
        self.dlg.switchProcessingsFakeButton.setToolTip(self.tr("See processings"))
        self.dlg.switchProcessingsButton.setEnabled(False)
        self.dlg.filterProjects.setPlaceholderText(self.tr("Filter projects by name"))
        self.dlg.createProject.setToolTip(self.tr("Create project"))
        # Add sorting options for projects and set updated recently as default
        self.dlg.sortProjectsCombo.addItems([self.tr("A-Z"), self.tr("Z-A"),
                                             self.tr("Newest first"), self.tr("Oldest first"),
                                             self.tr("Updated recently"), self.tr("Updated long ago")])
        self.dlg.sortProjectsCombo.setCurrentIndex(4)
        self.columns_config = ConfigColumns()

    def show_projects_pages(self, enable: bool = False, page_number: int = 1, total_pages: int = 1):
        self.dlg.projectsPreviousPageButton.setVisible(enable)
        self.dlg.projectsNextPageButton.setVisible(enable)
        self.dlg.projectsPageLabel.setVisible(enable)
        if enable is True:
            self.dlg.projectsPageLabel.setText(f"{page_number}/{total_pages}")
        # Disable next arrow for the last page
        if page_number == total_pages:
            self.dlg.projectsNextPageButton.setEnabled(False)
        else:
            self.dlg.projectsNextPageButton.setEnabled(True)
        # Disable previous arrow for the first page
        if page_number == 1:
            self.dlg.projectsPreviousPageButton.setEnabled(False)
        else:
            self.dlg.projectsPreviousPageButton.setEnabled(True)

    def enable_projects_pages(self, enable: bool = False):
        self.dlg.projectsNextPageButton.setEnabled(enable)
        self.dlg.projectsPreviousPageButton.setEnabled(enable) 
        
    def setup_projects_table(self, projects: List[MapflowProject]):
        if not projects:
            return
        # First column is ID, hidden; second is name
        self.dlg.projectsTable.setColumnCount(len(self.columns_config.PROJECTS_TABLE_COLUMNS))
        self.dlg.projectsTable.setColumnHidden(0, True)
        self.dlg.projectsTable.setRowCount(len(projects))
        self.dlg.projectsTable.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.dlg.projectsTable.setSelectionBehavior(QAbstractItemView.SelectRows)
        for row, project in enumerate(projects):
            id_item = QTableWidgetItem()
            id_item.setData(Qt.DisplayRole, project.id)
            self.dlg.projectsTable.setItem(row, 0, id_item)
            name_item = QTableWidgetItem()
            name_item.setData(Qt.DisplayRole, project.name)
            self.dlg.projectsTable.setItem(row, 1, name_item)
            # Combined state: succeeded / failed processings + planned processings (templates).
            counts = project.processingCounts or {}
            succeeded = counts.get('succeeded', 0)
            failed = counts.get('failed', 0)
            templates = project.templatesCount or 0
            state_widget = build_project_state_widget(succeeded, failed, templates)
            state_item = QTableWidgetItem()
            # Let resizeColumnsToContents account for the widget, and keep an item for selection.
            state_item.setSizeHint(state_widget.sizeHint())
            state_item.setToolTip(self.tr("Succeeded: {ok} · Failed: {failed} · Planned: {templates}").format(
                ok=succeeded, failed=failed, templates=templates))
            self.dlg.projectsTable.setItem(row, 2, state_item)
            self.dlg.projectsTable.setCellWidget(row, 2, state_widget)
            owner_item = QTableWidgetItem()
            owner_item.setData(Qt.DisplayRole, project.shareProject.owners[0].email)
            self.dlg.projectsTable.setItem(row, 3, owner_item)
            updated_item = QTableWidgetItem()
            updated_item.setData(Qt.DisplayRole, project.updated.astimezone().strftime('%Y-%m-%d %H:%M'))
            self.dlg.projectsTable.setItem(row, 4, updated_item)
            created_item = QTableWidgetItem()
            created_item.setData(Qt.DisplayRole, project.created.astimezone().strftime('%Y-%m-%d %H:%M'))
            self.dlg.projectsTable.setItem(row, 5, created_item)
            self.dlg.projectsTable.setHorizontalHeaderLabels(self.columns_config.PROJECTS_TABLE_COLUMNS)
        self.dlg.projectsTable.resizeColumnsToContents()
        for column_idx in (1, 3):
            # these columns are user-defined and can expand too wide, so we bound them
            if self.dlg.projectsTable.columnWidth(column_idx) > self.columns_config.MAX_WIDTH:
                self.dlg.projectsTable.setColumnWidth(column_idx, self.columns_config.MAX_WIDTH)
        self.dlg.projectsTable.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        self.dlg.projectsTable.horizontalHeader().setStretchLastSection(True)
        self.dlg.projectsTable.setSelectionMode(QAbstractItemView.SingleSelection)
        self.dlg.projectsTable.setSortingEnabled(True) # enable sorting by header click

    def clear_projects_table(self):
        self.dlg.projectsTable.clear()
        # Add a row with an error message to projects table
        table_item = QTableWidgetItem(self.tr("No project that meets specified criteria was found"))
        self.dlg.projectsTable.setRowCount(1)
        self.dlg.projectsTable.setColumnCount(2)
        self.dlg.projectsTable.setItem(0, 1, table_item)
        self.dlg.projectsTable.setHorizontalHeaderLabels(["ID", self.tr("Project")])
        return

    def select_project(self, project_id):
        try:
            item = self.dlg.projectsTable.findItems(project_id, Qt.MatchExactly)[0]
            self.dlg.projectsTable.setCurrentItem(item)
        except IndexError:
            self.switch_to_projects()
            pass

    def switch_to_projects(self):
        self.dlg.stackedProjectsWidget.setCurrentIndex(0)
        processings_tab = self.dlg.tabWidget.findChild(QWidget, "processingsTab")
        tab_index = self.dlg.tabWidget.indexOf(processings_tab)
        self.dlg.tabWidget.setTabText(tab_index, self.tr("Project"))

    def switch_to_processings(self):
        self.dlg.stackedProjectsWidget.setCurrentIndex(1)
        processings_tab = self.dlg.tabWidget.findChild(QWidget, "processingsTab")
        tab_index = self.dlg.tabWidget.indexOf(processings_tab)
        self.dlg.tabWidget.setTabText(tab_index, self.tr("Processing"))

    def sort_projects(self):
        index = self.dlg.sortProjectsCombo.currentIndex()
        # Define sorting field
        if index in (0, 1): # sort by name
                sort_by = ProjectSortBy.name
        elif index in (2, 3): # sort by date of creation
                sort_by = ProjectSortBy.created
        else: # sort by date of updating
                sort_by = ProjectSortBy.updated
        # Define sorting order
        if index in (0, 3, 5): # A-Z, Oldest first, Updated long ago
            sort_order = ProjectSortOrder.ascending
        else: # Z-A, Newest first, Updated recently
            sort_order = ProjectSortOrder.descending
        return sort_by.value, sort_order.value

    def setup_workflow_defs(self,
                            workflow_defs: dict[str, WorkflowDef],
                            default_model_name,
                            ):
        self.dlg.modelCombo.clear()
        self.dlg.modelCombo.addItems(wd.name for wd in workflow_defs.values())
        self.dlg.modelCombo.setCurrentText(default_model_name)
        self.dlg.modelCombo.activated.emit(self.dlg.modelCombo.currentIndex())

    @property
    def projects_filter(self):
        return self.dlg.filterProjects.text()

    def set_projects_filter(self, text: str) -> None:
        self.dlg.filterProjects.setText(text)

    def set_sort_index(self, index: int) -> None:
        self.dlg.sortProjectsCombo.setCurrentIndex(index)

    def selected_project_id(self):
        return self.dlg.selected_project_id()

    # ---------- the table's selection, while a request is in flight ----------

    def lock_projects_selection(self) -> None:
        """Forbid selecting a project until the pending request answers.

        Deleting a project renumbers the table under the user; letting them click during that
        window selects whichever project happens to land on the row they aimed at.
        """
        self.dlg.projectsTable.setSelectionMode(QAbstractItemView.NoSelection)
        self.dlg.projectsTable.clearSelection()

    def unlock_projects_selection(self) -> None:
        self.dlg.projectsTable.clearSelection()
        self.dlg.projectsTable.setSelectionMode(QAbstractItemView.SingleSelection)

    def clear_projects_selection(self) -> None:
        self.dlg.projectsTable.clearSelection()

    def freeze_projects_sorting(self) -> None:
        """Header-click sorting is re-enabled by `setup_projects_table`; turning it off first stops
        the rows re-ordering while they are being written."""
        self.dlg.projectsTable.setSortingEnabled(False)

    # ---------- which project is open ----------

    def show_current_project(self, name: str) -> None:
        """Name the open project in the header label, elided to the width it actually has.

        `fontMetrics().elidedText` needs the live widget width, so this cannot be precomputed by a
        caller — which is why the elision lives here rather than being passed in ready-made.
        """
        label = self.dlg.currentProjectLabel
        elided = label.fontMetrics().elidedText(name, Qt.ElideRight, label.width() - 50)
        label.setText(self.tr("Project: <b>{}").format(elided))
        label.adjustSize()

    def set_window_title(self, title: str) -> None:
        self.dlg.setWindowTitle(title)

    def enable_switch_to_processings(self, enabled: bool) -> None:
        self.dlg.switchProcessingsButton.setEnabled(enabled)

    def enable_project_change(self, reason: str, enabled: bool) -> None:
        self.dlg.enable_project_change(reason, enabled)

    def enable_shared_project(self, user_role) -> None:
        self.dlg.enable_shared_project(user_role)