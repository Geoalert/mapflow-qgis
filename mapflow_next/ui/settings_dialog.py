"""Settings: how results arrive, where files go, and the account."""
from __future__ import annotations

from qgis.PyQt.QtWidgets import (QButtonGroup, QCheckBox, QDialog, QFileDialog, QHBoxLayout, QLineEdit, QRadioButton,
                                 QVBoxLayout)

from .. import config
from ..services.results import FILES, TILES, default_output_dir
from .theme import stylesheet
from .widgets import Card, button, label, link


class SettingsDialog(QDialog):
    def __init__(self, settings, email: str, server: str, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.signed_out = False
        self.setObjectName("mfRoot")
        self.setWindowTitle("Mapflow settings")
        self.setStyleSheet(stylesheet())
        self.setMinimumWidth(440)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        results = Card(spacing=8)
        results.add(label("Results", "h2"))
        self.files = QRadioButton("Save as GeoPackage files and add to the map")
        self.tiles = QRadioButton("Stream as vector tiles (fast preview, nothing saved)")
        group = QButtonGroup(self)
        group.addButton(self.files)
        group.addButton(self.tiles)
        (self.tiles if settings.value("results_mode", FILES) == TILES else self.files).setChecked(True)
        results.add(self.files)
        results.add(self.tiles)
        results.add(label("Folder for result files", "label"))
        row = QHBoxLayout()
        self.folder = QLineEdit(str(settings.value("output_dir", "") or default_output_dir()))
        self.folder.setReadOnly(True)
        choose = button("Choose…", "outline", size="sm")
        choose.clicked.connect(self._choose_folder)
        row.addWidget(self.folder, 1)
        row.addWidget(choose)
        results.add(row)
        self.auto = QCheckBox("Add results to the map when a processing I started finishes")
        self.auto.setChecked(settings.flag("auto_load", True))
        results.add(self.auto)
        layout.addWidget(results)

        account = Card(spacing=6)
        account.add(label("Account", "h2"))
        account.add(label(email or "Signed in", "body"))
        account.add(label(f"Server: {server}", "meta", wrap=True))
        links = QHBoxLayout()
        links.setSpacing(14)
        links.addWidget(link("Balance and billing", config.TOP_UP_URL))
        links.addWidget(link("API token", config.API_TOKEN_URL))
        links.addStretch(1)
        account.add(links)
        sign_out = button("Sign out", "ghost", "logout", size="sm")
        sign_out.clicked.connect(self._sign_out)
        account.add(sign_out)
        layout.addWidget(account)

        buttons = QHBoxLayout()
        buttons.addWidget(link("Plugin guide", config.DOCS_URL))
        buttons.addStretch(1)
        cancel = button("Cancel", "ghost")
        cancel.clicked.connect(self.reject)
        save = button("Save", "primary")
        save.clicked.connect(self._save)
        buttons.addWidget(cancel)
        buttons.addWidget(save)
        layout.addLayout(buttons)

    def _choose_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Folder for Mapflow results", self.folder.text())
        if folder:
            self.folder.setText(folder)

    def _save(self) -> None:
        self.settings.setValue("results_mode", TILES if self.tiles.isChecked() else FILES)
        self.settings.setValue("output_dir", self.folder.text())
        self.settings.setValue("auto_load", self.auto.isChecked())
        self.accept()

    def _sign_out(self) -> None:
        self.signed_out = True
        self.accept()
