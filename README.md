# Get maps from pixels with Mapflow by Geoalert

At [Geoalert](https://www.geoalert.io/en-US/), we employ Artificial Intelligence (AI) and Machine Learning (ML) to detect and extract real-world objects a.k.a. 'features' from satellite or aerial imagery.

You choose what type of features you want to extract, where and from which imagery, and [Mapflow](https://mapflow.ai/) will do the work for you.

Currently we can detect:
- building footprints (optionally, with height)
- forest (optionally, with height)
- construction sites
- roads

More info about our AI models can be found [here](https://docs.mapflow.ai/userguides/pipelines).

Mapflow supports various imagery sources types. You can upload your local GeoTIFF image, or use one of the tile services on the Web. By default, we use [Mapbox Satellite](https://www.mapbox.com/maps/satellite), but you can specify a link to another imagery in XYZ, WMS, etc. Among the providers, we have a special support for Maxar [SecureWatch](https://www.maxar.com/products/securewatch) service.

![**Geoalert Mapflow plugin for QGIS**](images/plugin_showcase.png)


## Installation
The plugin can be found in the [official QGIS plugin repository](https://plugins.qgis.org/plugins/mapflow/) and can be installed by going to Plugins -> Manage and Install Plugins in QGIS, and then searching for 'Mapflow'. Make sure the 'all' tab is activated.

## Use

To learn how to use the plugin, please, follow our [guide](https://docs.mapflow.ai/api/qgis_mapflow).

## Contributing

### Running tests

Tests run inside the QGIS Python environment. Use the Python bundled with your QGIS installation.

**macOS** (QGIS-LTR):

```bash
# Install test dependencies (once)
/Applications/QGIS-LTR.app/Contents/MacOS/bin/python3 -m pip install pytest-qt

# Run tests
/Applications/QGIS-LTR.app/Contents/MacOS/bin/python3 -m pytest tests/
```

**Linux** (system package, e.g. `apt install qgis`):

```bash
# QGIS Python is typically the system Python with QGIS packages available
python3 -m pip install pytest-qt

python3 -m pytest tests/
```

If you installed QGIS from a non-standard location, use the Python binary bundled with it (e.g. `/usr/bin/qgis_python3` or similar).

**Windows** (OSGeo4W):

```cmd
:: Open the OSGeo4W Shell, then:
pip install pytest-qt

python -m pytest tests/
```

If using the standalone QGIS installer, open the **OSGeo4W Shell** shortcut that comes with QGIS — it sets up the correct Python environment automatically.

## License

This software is released under the [GNU Public License (GPL)](mapflow/LICENSE) Version 2 or any later version. This license means that you can inspect and modify the source code and guarantees that you always have access to this software under the same termas as QGIS, that is free of cost and can be freely modified.
