"""Logging in with a project remembered from the last session.

Every other journey starts from a fresh profile, where startup has no saved project to wait for and
opens the projects list. A returning user's startup is different: the plugin looks the saved project
up, and only once it answers does it configure itself and open that project's processings. If the
lookup's answer never reached startup, nothing would fail — the plugin would simply never finish
configuring, with no table opened and no imagery sources listed — so this journey asserts on what
the user sees.
"""
import pytest
from qgis.core import QgsProject, QgsSettings

from conftest import log_in, settle
from fake_network import fixture


@pytest.fixture
def returning_user(plugin_iface, network, fresh_profile, tmp_path):
    """The plugin as QGIS builds it for a user whose last session left a project open.

    The saved project has to be in the profile before construction, which reads it; that is why this
    cannot reuse the `plugin` fixture.
    """
    from mapflow.mapflow import Mapflow

    QgsSettings().setValue("mapflow/project_id", fixture("project_detail")["id"])
    instance = Mapflow(plugin_iface)
    instance.dlg.outputDirectory.setText(str(tmp_path))
    instance.app_context.settings.setValue("outputDir", str(tmp_path))
    instance.app_context.temp_dir = tmp_path
    instance.initGui()
    instance.main()
    settle(network, rounds=2)
    log_in(instance)
    settle(network)
    settle(network, rounds=4)
    yield instance
    instance.unload()
    QgsProject.instance().removeAllMapLayers()


def test_the_saved_project_is_looked_up(returning_user, network):
    project_id = fixture("project_detail")["id"]
    # By exact path: the processings page for that project contains the same prefix.
    lookups = [r for r in network.requests
               if r.method == "GET" and r.path.rstrip("/").endswith(f"projects/{project_id}")]
    assert lookups, f"the remembered project was never requested; sent: {network.paths()}"


def test_startup_opens_the_saved_projects_processings(returning_user, network):
    assert network.sent_to("processings/v2/page"), (
        f"a returning user lands on their project's processings; sent: {network.paths()}")
    assert not network.sent_to("projects/page"), (
        "the project list is for a user with no project to return to")


def test_startup_finishes_configuring_for_a_returning_user(returning_user):
    """The imagery sources are the last thing startup configures, and they are filtered by the
    project's model list — so they only appear when startup waited for the project and then ran."""
    combo = returning_user.dlg.providerCombo
    shown = [combo.itemText(i) for i in range(combo.count())]

    expected = [p["displayName"] for p in fixture("user_status")["dataProviders"]]
    missing = [name for name in expected if name not in shown]
    assert not missing, f"imagery sources {missing} missing; combo shows {shown}"


def test_every_request_of_a_returning_user_has_a_fixture(returning_user, network):
    assert network.unmatched == [], f"no fixture for: {sorted(set(network.unmatched))}"
