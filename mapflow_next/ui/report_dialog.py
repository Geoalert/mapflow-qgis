"""The report dialog behind "Send a report" (spec/006 § The report dialog): a one-line summary, the user's
comment, and the read-only technical text. "Send" opens the mail program, "Copy" fills the clipboard. The
plugin sends nothing itself."""
from __future__ import annotations

from qgis.PyQt.QtCore import QUrl
from qgis.PyQt.QtGui import QDesktopServices, QFontDatabase, QGuiApplication
from qgis.PyQt.QtWidgets import QDialog, QHBoxLayout, QPlainTextEdit, QVBoxLayout

from .theme import stylesheet
from .widgets import button, label
from ..core.guard import guarded
from ..core.report import compose, mailto


class ReportDialog(QDialog):
    def __init__(self, summary: str, technical: str, support_email: str, plugin_version: str, parent=None):
        super().__init__(parent)
        self.summary = summary
        self.technical = technical
        self.support_email = support_email
        self.plugin_version = plugin_version
        self.setObjectName("mfRoot")
        self.setWindowTitle("Send a report")
        self.setStyleSheet(stylesheet())
        self.setMinimumWidth(560)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 16)
        layout.setSpacing(8)
        layout.addWidget(label("Send a report", "h2"))
        layout.addWidget(label("The plugin sends nothing. “Send” opens your mail program with this text, addressed "
                               "to Mapflow support. “Copy” is for a mail program that cuts a long link short.",
                               "meta", wrap=True))
        self.summary_label = label(summary, "body", wrap=True)
        layout.addWidget(self.summary_label)
        layout.addWidget(label("What were you doing? (optional)", "label"))
        self.comment = QPlainTextEdit(self)
        self.comment.setPlaceholderText("For example: I pressed Run twice on a large area")
        self.comment.setFixedHeight(80)
        layout.addWidget(self.comment)
        layout.addWidget(label("Technical details", "label"))
        self.report_view = QPlainTextEdit(self)
        self.report_view.setReadOnly(True)
        self.report_view.setFont(QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont))
        self.report_view.setPlainText(technical)
        self.report_view.setMinimumHeight(200)
        layout.addWidget(self.report_view, 1)
        layout.addWidget(label("Your comment goes above this text.", "meta"))
        buttons = QHBoxLayout()
        buttons.addStretch(1)
        close = button("Close", "ghost")
        close.clicked.connect(guarded(lambda *_: self.reject()))
        copy = button("Copy", "outline")
        copy.clicked.connect(guarded(lambda *_: self.copy()))
        self.send_button = button("Send", "primary")
        self.send_button.clicked.connect(guarded(lambda *_: self.send()))
        self.send_button.setDefault(True)
        for item in (close, copy, self.send_button):
            buttons.addWidget(item)
        layout.addSpacing(6)
        layout.addLayout(buttons)
        self.comment.setFocus()

    def report_text(self) -> str:
        """What Send and Copy carry: the comment above the technical text."""
        return compose(self.comment.toPlainText(), self.technical)

    def send(self) -> None:
        """Open the mail program; the dialog stays, so the user can still Copy."""
        subject = f"Mapflow Next {self.plugin_version}: {self.summary}"
        QDesktopServices.openUrl(QUrl(mailto(self.support_email, subject, self.report_text())))

    def copy(self) -> None:
        QGuiApplication.clipboard().setText(self.report_text())
