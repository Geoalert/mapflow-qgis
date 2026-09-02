"""What the account may do and how much of it is left: the `/user/status` conversation.

One endpoint, two callers with different needs. A periodic refresh keeps the remaining limit and
the balance current while the plugin is open. A separate poll runs right after login until the
first response lands, because several things — the billing mode, the review workflow, the provider
lists, the area caps — cannot be configured until it does, and the request can fail on a slow or
offline start.

Holds no widget (`spec/007_architecture.md` § Layer rules). It parses the response into
`AppContext` and announces it; who repaints what is the listener's business. Its timers are
parented to the service rather than to the dialog, so nothing here needs a dialog to exist.
"""
import json
import logging
from typing import Optional

from PyQt5.QtCore import QObject, QTimer, pyqtSignal
from PyQt5.QtNetwork import QNetworkReply

from ..app_context import AppContext
from ...http import Http
from ...schema import BillingType

logger = logging.getLogger(__name__)


class AccountService(QObject):
    """The account's status: limits, balance, billing mode, and the caps a processing is checked
    against."""

    #: A status response was parsed into `AppContext`. Carries the raw payload (the provider lists
    #: live in it and are nobody else's to interpret) and whether this is the first response after
    #: login — the one the startup configuration is waiting for.
    statusApplied = pyqtSignal(dict, bool)
    #: The balance line: credits, remaining area, or empty when neither applies.
    balanceChanged = pyqtSignal(str)
    #: The startup retries ran out. Carries the message for the user; emitted once, ever, because
    #: giving up is latched.
    startupGaveUp = pyqtSignal(str)

    def __init__(self,
                 http: Http,
                 app_context: AppContext,
                 config,
                 server: str,
                 plugin_name: str):
        super().__init__()
        self.http = http
        self.app_context = app_context
        self.config = config
        self.server = server
        self.plugin_name = plugin_name

        #: The steady-state refresh while the plugin is open.
        self.refresh_timer = QTimer(self)
        self.refresh_timer.setInterval(config.USER_STATUS_UPDATE_INTERVAL * 1000)
        self.refresh_timer.timeout.connect(self.refresh_status)
        #: The post-login retry, on a much shorter interval, until the first response arrives.
        self.startup_timer = QTimer(self)
        self.startup_timer.setInterval(config.STARTUP_STATUS_RETRY_INTERVAL)
        self.startup_timer.timeout.connect(self.request_startup_status)
        self._startup_attempts = 0
        self._startup_pending = False
        self._startup_given_up = False

    # ---------- the steady-state refresh ----------

    def start_refreshing(self) -> None:
        self.refresh_timer.start()

    def stop_refreshing(self) -> None:
        self.refresh_timer.stop()

    def refresh_status(self) -> None:
        self.http.get(
            url=f'{self.server}/user/status',
            callback=self.apply_status,
            use_default_error_handler=False  # driven by a timer, so errors would stack up alerts
        )

    def request_status(self) -> None:
        """A one-off refresh, for the moments the timer's cadence is too slow to wait for —
        right after login, and after an action that spends limit."""
        self.refresh_status()

    # ---------- the post-login retry ----------

    def begin_startup_polling(self) -> None:
        """Start (or restart) the wait for the first status. Logging in again after a failed
        start must get a full budget of retries, so the counters reset here."""
        self._startup_attempts = 0
        self._startup_pending = False
        self._startup_given_up = False
        self.startup_timer.start()

    def stop_startup_polling(self) -> None:
        self.startup_timer.stop()
        self._startup_pending = False

    def request_startup_status(self) -> None:
        if self._startup_given_up or self._startup_pending:
            return
        if self._startup_attempts >= self.config.STARTUP_STATUS_MAX_ATTEMPTS:
            # Latched rather than left to the stopped timer: giving up must be a terminal
            # state, so a stray call cannot turn one warning into a modal per invocation.
            self._startup_given_up = True
            self.stop_startup_polling()
            self.startupGaveUp.emit(
                self.tr('Could not load your account status from Mapflow.\n\n'
                        'Some features stay unavailable until you reconnect and '
                        'reopen the plugin.'))
            return
        self._startup_attempts += 1
        self._startup_pending = True
        self.http.get(
            url=f'{self.server}/user/status',
            callback=self.startup_status_callback,
            error_handler=self.startup_status_error_handler,
            use_default_error_handler=False
        )

    def startup_status_callback(self, response: QNetworkReply) -> None:
        """Apply the startup configuration carried by the first `/user/status` response.

        The timer is stopped *before* the configuration runs, not after it. `apply_status` is
        invoked through the error guard, which swallows an exception and skips the rest of the
        callback — so a stop placed after the configuration would never run on a bad response, and
        the plugin would re-attempt the whole setup twice a second for the rest of the session.
        See spec/006_error_reporting.md § Consequences for new code.
        """
        self.stop_startup_polling()
        self.apply_status(response, app_startup_request=True)

    def startup_status_error_handler(self, response: QNetworkReply) -> None:
        """Let the next tick retry, and surface the failure once the attempts run out."""
        self._startup_pending = False
        logger.warning("Startup /user/status attempt %s failed with Qt error %s",
                       self._startup_attempts, response.error())

    # ---------- the response ----------

    def apply_status(self,
                     response: QNetworkReply,
                     app_startup_request: Optional[bool] = False) -> None:
        """Read the account's limits and modes out of a status response and into `AppContext`."""
        response_data = json.loads(response.readAll().data())
        if self.plugin_name != 'Mapflow':
            # In custom plugins we neither show the remaining limit nor check it before a start.
            self.app_context.billing_type = BillingType.none
        else:
            self.app_context.billing_type = BillingType(
                response_data.get('billingType', 'AREA').upper())
        self.app_context.remaining_limit = int(response_data.get('remainingArea', 0)) / 1e6  # sq.km
        self.app_context.remaining_credits = int(response_data.get('remainingCredits', 0))
        # Planned-processing (template) area cap; absent/zero means "unknown" and disables the
        # client-side check.
        self.app_context.template_area_limit = int(
            response_data.get('templateAreaLimit', 0)) / 1e6  # sq.km
        # Immediate-search area cap; above it the user is offered a Planned Search (T8).
        # Zero = unknown/disabled.
        self.app_context.search_area_limit = int(
            response_data.get('searchAreaLimit', 0)) / 1e6  # sq.km
        self.app_context.max_aois_per_processing = int(
            response_data.get("maxAoisPerProcessing", self.config.MAX_AOIS_PER_PROCESSING))
        self.app_context.review_workflow_enabled = response_data.get('reviewWorkflowEnabled', False)

        self.balanceChanged.emit(self.balance_message())
        self.statusApplied.emit(response_data, bool(app_startup_request))

    def balance_message(self) -> str:
        """What the account has left, in the unit it is billed in. Empty for an account that is
        not billed at all — there is no number to show, and '0' would read as 'nothing left'."""
        if self.app_context.billing_type == BillingType.credits:
            return self.tr("Your balance: {} credits").format(self.app_context.remaining_credits)
        if self.app_context.billing_type == BillingType.area:
            return self.tr('Remaining limit: {:.2f} sq.km').format(self.app_context.remaining_limit)
        return ''
