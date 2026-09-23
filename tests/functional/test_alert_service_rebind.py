"""The message tier's shared AlertService follows the latest plugin construction.

The instance stays shared on purpose — the module-level `alert()` helpers resolve it — but a plugin
rebuilt by QGIS (an in-place upgrade, Plugin Reloader) constructs it again with its own name, and
that name must win. Returning early on re-construction kept the first plugin's name in every title.
"""
from mapflow.infra.alert_service import AlertService


def test_reconstruction_rebinds_the_name_on_the_shared_instance():
    try:
        first = AlertService("First plugin")
        second = AlertService("Second plugin")

        assert second is first  # still one instance: the module-level helpers resolve it
        assert second.plugin_name == "Second plugin"
        assert AlertService.instance().plugin_name == "Second plugin"
    finally:
        AlertService("Mapflow")  # leave the process-wide instance as the rest of the tier expects
