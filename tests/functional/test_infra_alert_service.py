"""The message tier lives in `mapflow/infra/`, not `functional/service/` (error-reporting phase).

A service may not import a widget and a view may not import a service, yet both raise message-tier
alerts — so `alert_service` moved to the `infra/` layer, which every layer may import and which may
hold Qt (`spec/006_error_reporting.md` § Where each tier lives; `spec/007_architecture.md` § Layer
rules). This pins the new home and guards the old one from coming back.
"""
import importlib
from pathlib import Path

PLUGIN = Path(__file__).resolve().parents[2] / "mapflow"


def test_the_message_tier_is_importable_from_infra():
    # Safe in the no-QGIS functional tier: alert_service imports only PyQt5, not qgis.core.
    module = importlib.import_module("mapflow.infra.alert_service")
    for name in ("AlertService", "alert", "alert_info", "alert_warning", "alert_error",
                 "alert_confirm", "ask_text", "report_http_error"):
        assert hasattr(module, name), f"infra.alert_service is missing {name}"


def test_the_old_service_path_is_gone():
    """The file must not come back under `functional/service/` — that is the layer violation the
    move removed. Checked on disk rather than by import: importing the old package pulls in qgis,
    which the functional tier lacks, so an import would fail for the wrong reason."""
    assert not (PLUGIN / "functional" / "service" / "alert_service.py").exists()
    assert (PLUGIN / "infra" / "alert_service.py").exists()
