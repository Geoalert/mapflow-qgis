"""Adding, editing and removing imagery providers, and the zoom that goes with one.

`spec/007_architecture.md` names this controller for "provider add/edit/remove dialogs and the
provider combos". What is deliberately NOT here is `on_provider_change`: switching source has
effects in the search, processing and catalog regions at once, and reaching into those from here
would be controller-to-controller. It stays in the composition root, driving views.
"""
from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import QMessageBox

from ...infra.alert_service import alert, alert_warning
from ..service.provider_service import ProviderService
from ..view.provider_view import ProviderView
from ...model.provider import create_provider


class ProviderController(QObject):
    """The provider dialog's lifecycle, and the zoom combo."""

    def __init__(self,
                 provider_service: ProviderService,
                 provider_view: ProviderView,
                 provider_dialog,
                 app_context,
                 processing_service=None,
                 add_button=None,
                 edit_button=None,
                 remove_button=None,
                 zoom_combo=None):
        super().__init__()
        self.provider_service = provider_service
        self.provider_view = provider_view
        self.provider_dialog = provider_dialog
        self.app_context = app_context
        #: Asked to re-price when the zoom changes; the cost is the service's to compute.
        self.processing_service = processing_service

        if add_button is not None:
            add_button.clicked.connect(self.add_provider)
        if edit_button is not None:
            edit_button.clicked.connect(self.edit_provider)
        if remove_button is not None:
            remove_button.clicked.connect(self.remove_provider)
        if zoom_combo is not None:
            zoom_combo.currentIndexChanged.connect(self.on_zoom_change)
        if provider_dialog is not None:
            provider_dialog.accepted.connect(self.commit_provider)

    # ---------- the zoom ----------

    def on_zoom_change(self, *args) -> None:
        """Remember the chosen zoom and re-price: for tiled sources the cost depends on it.

        The default entry stores None rather than its label — it means "the provider's own
        resolution", and writing the label would send a zoom the user never chose.
        """
        if self.provider_view.zoom_is_default():
            self.app_context.settings.setValue('zoom', None)
        else:
            self.app_context.settings.setValue('zoom', str(self.provider_view.zoom_text()))
        self.processing_service.update_processing_cost()

    # ---------- add / edit / remove ----------

    def add_provider(self, *args) -> None:
        self.provider_dialog.setup(None, self.tr("Add new provider"))

    def edit_provider(self, *args) -> None:
        provider = self.provider_service.providers[self.provider_view.provider_index()]
        if provider.is_default:
            alert_warning(self.tr("This is a default provider, it cannot be edited"))
            return
        self.provider_dialog.setup(provider)

    def remove_provider(self, *args) -> None:
        """The red minus beside the source combo. Built-in providers are protected; a user's own
        is removed only after confirmation, because there is no undo."""
        provider = self.provider_service.providers[self.provider_view.provider_index()]
        if provider.is_default:
            alert_warning(self.tr("This provider is default and cannot be removed"))
            return
        if alert(self.tr('Permanently remove {}?').format(provider.name),
                 icon=QMessageBox.Question):
            self.provider_service.user_providers.remove(provider)
            self.provider_service.update_providers()

    def commit_provider(self, *args) -> None:
        """The provider dialog was accepted: add the new provider, or replace the edited one.

        Names are the identity here — the combo and every saved setting key off them — so a
        collision is refused and the dialog reopened with the user's input intact, rather than
        silently overwriting whichever provider already had that name.
        """
        if not self.provider_dialog.result:
            return  # dialog closed without changes
        old_provider = self.provider_dialog.current_provider
        new_provider = create_provider(**self.provider_dialog.result)

        if not old_provider:
            if self._name_taken(new_provider.name):
                return
            self.provider_service.user_providers.append(new_provider)
            provider_index = len(self.provider_service.providers)
        else:
            provider_index = self.provider_service.providers.index(old_provider)
            # A rename onto another provider's name is the collision; keeping its own name is not.
            if new_provider.name != old_provider.name and self._name_taken(new_provider.name):
                return
            user_index = self.provider_service.user_providers.index(old_provider)
            self.provider_service.user_providers[user_index] = new_provider

        self.provider_service.update_providers()
        self.provider_view.set_provider_index(provider_index)

    def _name_taken(self, name: str) -> bool:
        if name not in self.provider_service.providers:
            return False
        alert_warning(self.tr("Provider name must be unique. {name} already exists, "
                              "select another or delete/edit existing").format(name=name))
        self.provider_dialog.show()
        return True
