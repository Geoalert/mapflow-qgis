"""QGIS-tier tests: the search "Providers" filter is only shown when the search is
limited to available providers ("Search only through available providers" is checked)."""
from unittest.mock import MagicMock

from mapflow.dialogs.main_dialog import MainDialog


def _dialog(available, checked):
    dlg = MainDialog.__new__(MainDialog)
    dlg.searchProvidersCombo = MagicMock()
    dlg.searchProvidersLabel = MagicMock()
    dlg.hideUnavailableResults = MagicMock()
    dlg.hideUnavailableResults.isChecked.return_value = checked
    dlg._search_providers_available = available
    return dlg


def test_filter_visible_only_when_available_and_limited_to_available():
    dlg = _dialog(available=True, checked=True)

    dlg.update_search_providers_filter_visibility()

    dlg.searchProvidersCombo.setVisible.assert_called_with(True)
    dlg.searchProvidersLabel.setVisible.assert_called_with(True)


def test_filter_hidden_when_checkbox_unset_even_with_providers():
    dlg = _dialog(available=True, checked=False)

    dlg.update_search_providers_filter_visibility()

    dlg.searchProvidersCombo.setVisible.assert_called_with(False)
    dlg.searchProvidersLabel.setVisible.assert_called_with(False)


def test_filter_hidden_without_providers_even_when_checked():
    dlg = _dialog(available=False, checked=True)

    dlg.update_search_providers_filter_visibility()

    dlg.searchProvidersCombo.setVisible.assert_called_with(False)


def test_enable_search_providers_filter_records_availability_and_applies_checkbox():
    dlg = _dialog(available=False, checked=True)

    dlg.enable_search_providers_filter(0)
    assert dlg._search_providers_available is False
    dlg.searchProvidersCombo.setVisible.assert_called_with(False)

    dlg.enable_search_providers_filter(3)
    assert dlg._search_providers_available is True
    dlg.searchProvidersCombo.setVisible.assert_called_with(True)
