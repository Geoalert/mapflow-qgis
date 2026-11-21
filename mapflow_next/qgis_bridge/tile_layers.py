"""The XYZ/TMS tile layers of the QGIS project as imagery (spec/002_B § Imagery from a QGIS tile layer).

A layer is offered when it is a raster layer of the `wms` provider whose source has `type=xyz`. QGIS 3.28 and
QGIS 4 give the parts in the layer's source text (`url`, `zmin`, `zmax`, `username`, `password`, `authcfg`,
`referer`, `http-header:<name>`); `core/tile_layers.py` splits and judges it. The plugin sets no property on such
a layer and stores nothing of it. Nothing here logs an address, a login or a password, and an exception that
could hold them is caught without its text.
"""
from __future__ import annotations

from typing import List, Optional, Tuple

from qgis.core import QgsApplication, QgsAuthMethodConfig, QgsProject, QgsRasterLayer

from ..config import PREVIEW_PROPERTY, PROCESSING_PROPERTY
from ..core.tile_layers import BASIC, TileOffer, TileSource, tile_params, tile_source


def _auth_method(config_id: str) -> str:
    """The method key of an authentication configuration ("Basic", "APIHeader", …), "" when QGIS has no such
    configuration. It reads no secret, so it never asks for the master password."""
    return QgsApplication.authManager().configAuthMethodKey(config_id) or ""


def _source_of(layer) -> Optional[TileSource]:
    """The tile source of a layer of the project, or None when the plugin does not look at it: not a valid raster
    layer of the `wms` provider, one the plugin added itself (a preview, a result), or not an XYZ source. A layer
    that QGIS could not load is left out: its source may be half of a connection."""
    if not isinstance(layer, QgsRasterLayer) or not layer.isValid() or layer.providerType() != "wms":
        return None
    if layer.customProperty(PREVIEW_PROPERTY) or layer.customProperty(PROCESSING_PROPERTY):
        return None
    return tile_source(layer.source(), _auth_method)


def tile_offers(project: Optional[QgsProject] = None) -> List[TileOffer]:
    """The tile layers of the project, by name: each usable, or disabled with its reason. A layer that cannot be
    read is left out."""
    project = project or QgsProject.instance()
    offers = [_offer_of(layer) for layer in list(project.mapLayers().values())]
    return sorted((offer for offer in offers if offer is not None),
                  key=lambda offer: (offer.name.lower(), offer.layer_id))


def _offer_of(layer) -> Optional[TileOffer]:
    try:
        source = _source_of(layer)
        if source is None:
            return None
        params, reason = tile_params(source)
        return TileOffer(layer.id(), layer.name(), params, reason)
    except Exception:  # noqa: BLE001 - a layer the plugin cannot read is not offered; the text may hold its source
        return None


def tile_credentials(layer_id: str, project: Optional[QgsProject] = None) -> Optional[Tuple[str, str]]:
    """The (login, password) of a tile layer, read now and never kept: from its Basic authentication configuration
    (the configuration wins when the source has both), else from `username` and `password` of its source. This
    reads the secrets, and QGIS may ask for the master password. None when the layer is gone, has no login, or
    the configuration cannot be read."""
    project = project or QgsProject.instance()
    try:
        layer = project.mapLayer(layer_id)
        source = _source_of(layer)
        if source is None:
            return None
        if source.auth_method:
            if source.auth_method != BASIC:
                return None
            config = QgsAuthMethodConfig()
            if not QgsApplication.authManager().loadAuthenticationConfig(source.auth_config_id, config, True):
                return None
            login, password = config.config("username"), config.config("password")
        else:
            login, password = source.login, source.password
    except Exception:  # noqa: BLE001 - the text may hold the secrets
        return None
    return (login, password) if login and password else None
