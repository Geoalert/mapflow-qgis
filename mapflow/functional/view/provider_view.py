"""Every widget read and write for choosing an imagery source and its zoom.

Holds no service (`spec/007_architecture.md` § Layer rules). The provider combo, the zoom combo
and the two tabs the source selection switches between live here; which provider that index means
is `ProviderService`'s, and what to do about it is `ProviderController`'s.
"""
from typing import Optional

from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import QWidget

from ...dialogs.main_dialog import MainDialog


class ProviderView(QObject):
    """The source combo, the zoom combo, and the tabs a source change brings forward."""

    #: Object names of the tabs in the .ui file. "providersTab" is the imagery-search tab —
    #: historical, and renaming it in Designer would break every findChild that uses it.
    CATALOG_TAB = "catalogTab"
    IMAGERY_SEARCH_TAB = "providersTab"

    def __init__(self, dlg: MainDialog):
        super().__init__()
        self.dlg = dlg

    # ---------- the source combo ----------

    def provider_index(self) -> int:
        return self.dlg.providerIndex()

    def set_provider_index(self, index: int) -> None:
        self.dlg.setProviderIndex(index)

    def add_providers(self, provider_names: dict) -> None:
        """Append {name: api_name} entries to the provider combo (the list changed)."""
        for name, api_name in provider_names.items():
            self.dlg.providerCombo.addItem(name, api_name)

    def set_raster_sources(self, provider_names: dict, default_provider_names) -> None:
        """Rebuild both source combos from the current providers, defaulting to the given names."""
        self.dlg.set_raster_sources(provider_names=provider_names,
                                    default_provider_names=default_provider_names)

    def select_data_provider(self, index: int, zoom) -> None:
        """Duplicating a processing: pick the source by index, and its zoom (index 0 = native)."""
        self.dlg.sourceCombo.setCurrentIndex(index)
        if zoom:
            self.dlg.zoomCombo.setCurrentText(str(zoom))
        else:
            self.dlg.zoomCombo.setCurrentIndex(0)

    def select_source_by_name(self, name: str) -> None:
        self.dlg.sourceCombo.setCurrentText(name)

    def set_zoom_text(self, zoom: str) -> None:
        self.dlg.zoomCombo.setCurrentText(str(zoom))

    # ---------- the zoom combo ----------

    def enable_zoom(self, enabled: bool) -> None:
        """Only tiled sources take a zoom: imagery search and My Imagery serve fixed resolutions,
        so the combo is disabled rather than ignored, to say so."""
        self.dlg.zoomCombo.setEnabled(enabled)

    def reset_zoom(self) -> None:
        self.dlg.zoomCombo.setCurrentIndex(0)

    def zoom_is_default(self) -> bool:
        """Index 0 is the 'native/maximum' entry, which means 'do not send a zoom'."""
        return self.dlg.zoomCombo.currentIndex() == 0

    def zoom_text(self) -> Optional[str]:
        return self.dlg.zoomCombo.currentText()

    # ---------- tabs ----------

    def show_catalog_tab(self) -> None:
        self._show_tab(self.CATALOG_TAB)

    def show_imagery_search_tab(self) -> None:
        self._show_tab(self.IMAGERY_SEARCH_TAB)

    def _show_tab(self, object_name: str) -> None:
        tab = self.dlg.tabWidget.findChild(QWidget, object_name)
        if tab is not None:
            self.dlg.tabWidget.setCurrentWidget(tab)
