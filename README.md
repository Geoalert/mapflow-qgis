# Get maps from pixels with Mapflow by Geoalert

At [Geoalert](https://www.geoalert.io/en-US/), we employ Artificial Intelligence (AI) and Machine Learning (ML) to detect and extract real-world objects a.k.a. 'features' from satellite or aerial imagery.

You choose what type of features you want to extract, where and from which imagery, and [Mapflow](https://mapflow.ai/) will do the work for you.

Current we can detect:
- buildings (optionally, with height)
- forest (optionally, with height)
- construction sites
- roads

More info about our AI models can be found [here](https://docs.mapflow.ai/docs_userguides/pipelines.html).

Mapflow supports various imagery sources.You can upload your local GeoTIFF image, or use on of the tile services on the Web. By default, we use [Mapbox Satellite](https://www.mapbox.com/maps/satellite), but you can specify a link to another imagery tile provider, like Google or Bing. Among the providers, we have a special support for Maxar and its [SecureWatch](https://www.maxar.com/products/securewatch) service.

## Installation
The plugin can be found in the [official QGIS plugin repository](https://plugins.qgis.org/plugins) and can be installed by going to Plugins -> Manage and Install Plugins in QGIS, and then searching for 'Mapflow'. Make sure the 'all' tab is activated.

To learn how to use the plugin, please, see our [guide](https://docs.mapflow.ai/docs_api/qgis_mapflow.html).