"""Routes the plugin's stdlib logging into the QGIS message log.

Modules log through the standard library — ``logging.getLogger(__name__)`` — and never
touch QGIS directly. That matters for three reasons specific to this codebase:

* **No import cycles.** ``logging`` is stdlib, so a logging call can never drag another
  plugin package into a module. Do not move this behind a helper in
  ``functional/service/`` — that package sits on the circular import chain documented in
  tests/functional/conftest.py, which would make logging unreachable from leaf modules
  like ``schema/catalog.py`` and force lazy-import shims at every call site.
* **Tracebacks.** ``logger.exception(...)`` records ``exc_info`` automatically. Formatting
  only ``str(e)`` loses the location, which is the entire diagnostic value of an
  *unexpected* exception.
* **One binding point for QGIS.** The Qt6/QGIS4 port has a single place to change.

Deliberately NOT a user-facing channel. QGIS's log panel is closed by default, so anything
recorded here is effectively invisible to users — it is for developers and testers reading
logs after the fact. Anything a user must actually notice belongs on the message bar or in
the error-report dialog.

The module is importable without QGIS: the handler imports ``qgis.core`` lazily, so
functional-tier tests can configure logging without a runtime.
"""
import logging

LOGGER_NAME = "mapflow"
MESSAGE_LOG_TAG = "Mapflow"


class QgisMessageLogHandler(logging.Handler):
    """Forward log records to the QGIS message log under the "Mapflow" tag."""

    #: stdlib level -> Qgis.MessageLevel attribute name, resolved lazily so this module
    #: stays importable without the QGIS runtime.
    _LEVEL_NAMES = (
        (logging.ERROR, "Critical"),
        (logging.WARNING, "Warning"),
        (logging.NOTSET, "Info"),
    )

    def emit(self, record: logging.LogRecord) -> None:
        try:
            from qgis.core import Qgis, QgsMessageLog
        except ImportError:
            # No QGIS runtime (a bare unit-test process). Nothing to forward to; the
            # record still reaches any other handler that is installed.
            return
        try:
            message = self.format(record)
            level_name = next(name for threshold, name in self._LEVEL_NAMES
                              if record.levelno >= threshold)
            QgsMessageLog.logMessage(message, MESSAGE_LOG_TAG, level=getattr(Qgis, level_name))
        except Exception:  # noqa: BLE001 - see below
            # A logging handler must never raise into the code that logged: that would
            # turn a diagnostic into a second failure, at the exact moment the first one
            # is being reported. handleError() honours logging.raiseExceptions.
            self.handleError(record)


def configure_logging(level: int = logging.INFO) -> logging.Logger:
    """Attach the QGIS handler to the plugin's root logger. Safe to call more than once.

    Called from plugin start-up. Tests do not need it — without a handler, records simply
    go nowhere, and ``caplog`` captures them regardless.
    """
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(level)
    # Plugins share the host process, so propagating to the root logger would push this
    # plugin's output into whatever handler QGIS (or another plugin) installed there.
    #
    # Note for tests: this is why the suite does NOT call configure_logging(). pytest's
    # caplog attaches at the root, so propagate=False would hide records from it. Leaving
    # the plugin logger unconfigured in tests keeps propagation on and caplog working.
    logger.propagate = False
    if not any(isinstance(h, QgisMessageLogHandler) for h in logger.handlers):
        handler = QgisMessageLogHandler()
        # The logger name identifies the module; the QGIS panel shows tag + message only.
        handler.setFormatter(logging.Formatter("%(name)s: %(message)s"))
        logger.addHandler(handler)
    return logger
