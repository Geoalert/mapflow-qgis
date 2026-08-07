# Get maps from pixels with Mapflow by Geoalert

At [Geoalert](https://www.geoalert.io/en-US/), we employ Artificial Intelligence (AI) and Machine Learning (ML) to detect and extract real-world objects a.k.a. 'features' from satellite or aerial imagery.

You choose what type of features you want to extract, where and from which imagery, and [Mapflow](https://mapflow.ai/) will do the work for you.

Currently we can detect:
- building footprints (optionally, with height)
- forest (optionally, with height)
- construction sites
- roads

More info about our AI models can be found [here](https://docs.mapflow.ai/userguides/pipelines).

Mapflow supports various imagery sources types. You can upload your local GeoTIFF image, or use one of the tile services on the Web. By default, we use [Mapbox Satellite](https://www.mapbox.com/maps/satellite), but you can specify a link to another imagery in XYZ, WMS, etc. You can also search the Mapflow imagery catalog and process a specific image.

![**Geoalert Mapflow plugin for QGIS**](images/plugin_showcase.png)


## Installation
The plugin can be found in the [official QGIS plugin repository](https://plugins.qgis.org/plugins/mapflow/) and can be installed by going to Plugins -> Manage and Install Plugins in QGIS, and then searching for 'Mapflow'. Make sure the 'all' tab is activated.

## Use

To learn how to use the plugin, please, follow our [guide](https://docs.mapflow.ai/api/qgis_mapflow).

## Contributing

### Running tests

Automated tests run inside the official `qgis/qgis:release-3_28` Docker
image — no host QGIS install needed, only Docker.

```bash
make test-functional   # pure-logic tests
make test-qgis         # tests that touch real QGIS objects
make test-ui           # UI tests under xvfb (harness only — no tests yet)
make test              # all three tiers
```

Test layout, fixtures, and the policy for adding a test live in
[`tests/README.md`](tests/README.md).

### Linting

Static analysis runs in the **same Docker image as the tests** — no host
`pip install`, no project `venv`:

```bash
make lint   # flake8 + bandit + detect-secrets
```

These are the three checks [plugins.qgis.org](https://plugins.qgis.org/docs/security-scanning)
runs when a plugin is submitted, invoked the same way, so a green run here
predicts a clean scan there:

| tool | scope | qgis.org status |
|---|---|---|
| **flake8** at `--max-line-length=120` | `mapflow/` + `tests/` | advisory |
| **bandit** at `-ll` (medium+ severity) | `mapflow/` only | **blocking** |
| **detect-secrets** against `.secrets.baseline` | `mapflow/` + `tests/` | **blocking** |

bandit covers only `mapflow/` because that is the code that ships, and `B101`
(assert_used) would otherwise fire on every pytest assertion. Tool versions are
pinned in [`Dockerfile.tests`](Dockerfile.tests): an unpinned linter silently
changes its verdict when upstream adds a rule, turning an unrelated MR red.

[`.flake8`](.flake8) carries a **debt ledger** — the rule classes still
outstanding from the 3.6.0 scan, each tied to the WAL step that removes it. It
is a shrinking list, not a permanent exemption: the qgis.org scan runs against
the packaged `mapflow/` directory and never reads `.flake8`, so everything
listed there is debt still owed at submission time.

> **Coverage scope.** CI is pinned to **Linux + QGIS 3.28 LTR**. The
> `qgis/qgis` Docker image is Linux-only and we do not run a CI matrix
> across operating systems or QGIS versions. Verify macOS, Windows, and
> non-LTR QGIS versions by manual smoke testing before release.

## License

This software is released under the [GNU Public License (GPL)](mapflow/LICENSE) Version 2 or any later version. This license means that you can inspect and modify the source code and guarantees that you always have access to this software under the same termas as QGIS, that is free of cost and can be freely modified.
