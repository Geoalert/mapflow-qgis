from PyQt5.QtCore import QObject, Qt
from PyQt5.QtWidgets import QWidget, QTableWidget, QTableWidgetItem, QAbstractItemView, QHeaderView

from ...dialogs.main_dialog import MainDialog
from ...dialogs import icons
from ...config import ConfigColumns
from ...schema.project import MapflowProject, ProjectSortBy, ProjectSortOrder


class ProjectView(QObject):
    def tr(self, message: str) -> str:
        """Translate string for i18n support."""
        from PyQt5.QtCore import QCoreApplication
        return QCoreApplication.translate('ProjectView', message)
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
        
    def setup_projects_table(self, projects: dict[str, MapflowProject]):
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
            ok_item = QTableWidgetItem()
            ok_item.setData(Qt.DisplayRole, project.processingCounts['succeeded'])
            self.dlg.projectsTable.setItem(row, 2, ok_item)
            failed_item = QTableWidgetItem()
            failed_item.setData(Qt.DisplayRole, project.processingCounts['failed'])
            self.dlg.projectsTable.setItem(row, 3, failed_item)
            owner_item = QTableWidgetItem()
            owner_item.setData(Qt.DisplayRole, project.shareProject.owners[0].email)
            self.dlg.projectsTable.setItem(row, 4, owner_item)
            updated_item = QTableWidgetItem()
            updated_item.setData(Qt.DisplayRole, project.updated.astimezone().strftime('%Y-%m-%d %H:%M'))
            self.dlg.projectsTable.setItem(row, 5, updated_item)
            created_item = QTableWidgetItem()
            created_item.setData(Qt.DisplayRole, project.created.astimezone().strftime('%Y-%m-%d %H:%M'))
            self.dlg.projectsTable.setItem(row, 6, created_item)
            self.dlg.projectsTable.setHorizontalHeaderLabels(self.columns_config.PROJECTS_TABLE_COLUMNS)
        self.dlg.projectsTable.resizeColumnsToContents()
        for column_idx in (1, 4):
            # these columns are user-defined and can expand too wide, so we bound them
            if self.dlg.projectsTable.columnWidth(column_idx) > self.columns_config.MAX_WIDTH:
                self.dlg.projectsTable.setColumnWidth(column_idx, self.columns_config.MAX_WIDTH)
        self.dlg.projectsTable.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        self.dlg.projectsTable.horizontalHeader().setStretchLastSection(True)
        self.dlg.projectsTable.setSelectionMode(QAbstractItemView.SingleSelection)
        self.dlg.projectsTable.setSortingEnabled(True) # enable sorting by header click

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
