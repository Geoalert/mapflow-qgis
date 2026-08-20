"""The plugin loads into QGIS and exposes its main dialog.

The precondition for every other behavioral test, and the most expensive regression the
refactoring could introduce: a plugin that fails to construct does not degrade, it simply
never appears in QGIS.

Asserted on widget object names rather than on plugin internals, because the `.ui` files are
the contract the refactoring preserves.
"""
from PyQt5.QtWidgets import QWidget


def test_plugin_constructs(plugin):
    assert plugin.dlg is not None, "the main dialog is the handle every behavioral test uses"


def test_init_gui_runs(plugin):
    """QGIS calls initGui() on load; anything raising here means no toolbar and no plugin."""
    plugin.initGui()


def test_main_dialog_exposes_the_widgets_the_journeys_drive(plugin):
    """Names the later behavioral tests depend on, checked in one place.

    If the refactoring renames one of these, this test names it directly instead of the
    failure surfacing as an AttributeError inside an unrelated journey.
    """
    expected = [
        "startProcessing",
        "processingsTable",
        "metadataTable",
        "polygonCombo",
        "modelCombo",
        "outputDirectory",
        "balanceLabel",
        "providerCombo",
    ]
    # `hasattr` is not enough: an attribute set to None still answers True, and a journey
    # would then fail with an unhelpful AttributeError far from here.
    missing = [name for name in expected
               if not isinstance(getattr(plugin.dlg, name, None), QWidget)]
    assert not missing, f"main dialog is missing widget(s) the behavioral journeys drive: {missing}"
