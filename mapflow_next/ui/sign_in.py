"""Sign-in: browser sign-in first, a free account second, the API token folded away."""
from __future__ import annotations

from qgis.PyQt.QtCore import Qt, pyqtSignal
from qgis.PyQt.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QScrollArea, QVBoxLayout, QWidget

from .. import config
from . import icons
from .theme import is_dark, tokens
from .widgets import Callout, button, label, link, rule, vbox


class SignInPage(QWidget):
    HINT = "Opens your browser to sign in, then Mapflow Web"
    WAITING = "Finish signing in in your browser, then come back to QGIS."

    browserRequested = pyqtSignal()
    cancelRequested = pyqtSignal()
    tokenSubmitted = pyqtSignal(str)
    networkSettingsRequested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("mfPage")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        body = QWidget()
        body.setObjectName("mfScrollBody")
        scroll.setWidget(body)
        outer.addWidget(scroll)
        layout = QVBoxLayout(body)
        layout.setContentsMargins(24, 28, 24, 20)
        layout.setSpacing(20)

        layout.addWidget(icons.logo_widget(is_dark(), 34, body), 0, Qt.AlignmentFlag.AlignLeft)
        layout.addLayout(vbox(label("AI mapping, right inside QGIS", "h1", wrap=True),
                              label("Get buildings, roads and forest from imagery as editable layers "
                                    "in your project.", "lead", wrap=True), spacing=6))

        for icon_name, title, text in (
                ("buildings", "Ready-made scenarios", "Built on Mapflow models for buildings, trees, roads and more"),
                ("image", "Your imagery or ours", "Mapbox, satellite catalogs or your own GeoTIFF"),
                ("layers", "Results as QGIS layers", "Styled GeoPackage layers, ready to edit")):
            row = QHBoxLayout()
            row.setSpacing(12)
            badge = QLabel(body)
            badge.setFixedSize(40, 40)
            badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            badge.setStyleSheet(f"background: {tokens()['primary_soft']}; border-radius: 10px;")
            badge.setPixmap(icons.pixmap(icon_name, tokens()["primary_hover"], 20))
            row.addWidget(badge, 0, Qt.AlignmentFlag.AlignTop)
            row.addLayout(vbox(label(title, "title"), label(text, "meta", wrap=True), spacing=2), 1)
            layout.addLayout(row)

        self.error = Callout("error", "", body)
        layout.addWidget(self.error)

        self.browser = button("Sign in with Mapflow", "primary", "login", size="lg")
        self.browser.clicked.connect(self.browserRequested.emit)
        self.hint = label(self.HINT, "meta", wrap=True)
        self.hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cancel = button("Cancel", "ghost", size="sm")
        self.cancel.clicked.connect(self.cancelRequested.emit)
        self.cancel.setVisible(False)
        layout.addLayout(vbox(self.browser, self.hint, spacing=6))
        layout.addWidget(self.cancel, 0, Qt.AlignmentFlag.AlignHCenter)

        create = button("Create a free account", "outline", external=True, size="lg")
        create.setToolTip(config.SIGN_UP_URL)
        create.clicked.connect(lambda: _open(config.SIGN_UP_URL))
        credits = label("250 free credits to start", "meta")
        credits.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addLayout(vbox(create, credits, spacing=6))

        self.more = button("Other ways to sign in", "ghost", size="sm")
        self.more.setIcon(icons.icon("chevron-down", tokens()["link"], 14))
        self.more.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.more.clicked.connect(lambda: self._toggle_more())   # not the slot itself: clicked passes checked=False
        layout.addWidget(self.more, 0, Qt.AlignmentFlag.AlignHCenter)

        self.token_box = QWidget(body)
        self.token_box.setObjectName("mfScrollBody")
        token_layout = QVBoxLayout(self.token_box)
        token_layout.setContentsMargins(0, 0, 0, 0)
        token_layout.setSpacing(8)
        token_layout.addWidget(label("Use an API token if browser sign-in doesn't work, for example behind a "
                                     "proxy or on a remote desktop.", "meta", wrap=True))
        token_layout.addWidget(label("API token", "label"))
        row = QHBoxLayout()
        row.setSpacing(8)
        self.token = QLineEdit(self.token_box)
        self.token.setEchoMode(QLineEdit.EchoMode.Password)
        self.token.setPlaceholderText("Paste your token")
        self.token.returnPressed.connect(self._submit_token)
        self.token_button = button("Sign in", "outline")
        self.token_button.clicked.connect(self._submit_token)
        row.addWidget(self.token, 1)
        row.addWidget(self.token_button)
        token_layout.addLayout(row)
        token_layout.addWidget(link("Get your token in Mapflow Web", config.API_TOKEN_URL))
        self.token_box.setVisible(False)
        layout.addWidget(self.token_box)

        layout.addStretch(1)
        layout.addWidget(rule())
        network = link("Network and proxy settings", external=False)
        network.clicked.connect(self.networkSettingsRequested.emit)
        footer = QHBoxLayout()
        footer.setSpacing(16)
        footer.addWidget(network)
        footer.addWidget(link("Plugin guide", config.DOCS_URL))
        footer.addStretch(1)
        layout.addLayout(footer)

    def _toggle_more(self, show=None) -> None:
        visible = (not self.token_box.isVisible()) if show is None else bool(show)
        self.token_box.setVisible(visible)
        self.more.setIcon(icons.icon("chevron-up" if visible else "chevron-down", tokens()["link"], 14))
        if visible:
            self.token.setFocus()

    def _submit_token(self) -> None:
        token = self.token.text().strip()
        if token:
            self.tokenSubmitted.emit(token)

    def set_busy(self, busy: bool, waiting_browser: bool = False) -> None:
        self.browser.setEnabled(not busy)
        self.token_button.setEnabled(not busy)
        waiting = busy and waiting_browser
        self.browser.setText("Waiting for your browser…" if waiting else "Signing in…" if busy
                             else "Sign in with Mapflow")
        self.hint.setText(self.WAITING if waiting else self.HINT)
        self.cancel.setVisible(waiting)

    def show_error(self, text: str, open_token: bool = False) -> None:
        self.error.set("error", text)
        if open_token:
            self._toggle_more(True)

    def clear(self) -> None:
        self.error.set("error", "")
        self.token.clear()


def _open(url: str) -> None:
    from qgis.PyQt.QtCore import QUrl
    from qgis.PyQt.QtGui import QDesktopServices
    QDesktopServices.openUrl(QUrl(url))
