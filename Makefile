# Test, lint and packaging for the Mapflow QGIS plugin (mapflow_next/).
#
# The plugin supports QGIS 3 (Qt 5) and QGIS 4 (Qt 6), so the tests run twice, in two official
# qgis/qgis Docker images built from the same Dockerfile.tests. No host QGIS is needed: the repo is
# bind-mounted at /app, so the containers always see the current working tree.
#
# With QGIS installed, the *-local targets run the same tests with its own Python instead:
#   make test-local QGIS_PYTHON=/Applications/QGIS-LTR.app/Contents/MacOS/bin/python3

PLUGIN := mapflow_next
VERSION := $(shell sed -n 's/^version=//p' $(PLUGIN)/metadata.txt)

DOCKERFILE ?= Dockerfile.tests
# QGIS 3: the oldest LTR image CI already used. QGIS 4: the current release.
QGIS3_BASE ?= qgis/qgis:release-3_28
QGIS4_BASE ?= qgis/qgis:4.2
IMAGE ?= mapflow-qgis-tests
IMAGE_QGIS4 ?= mapflow-qgis-tests-qgis4
DOCKER_RUN = docker run --rm -v "$(CURDIR)":/app -w /app $(IMAGE)
DOCKER_RUN_QGIS4 = docker run --rm -v "$(CURDIR)":/app -w /app $(IMAGE_QGIS4)

QGIS_PYTHON ?= python3
# Any Python with PyQt6 (pip install PyQt6): Qt 6 checks without QGIS 4 installed
QT6_PYTHON ?= python3
# QGIS 4 keeps its profiles in .../QGIS/QGIS4/...: make link QGIS_MAJOR=4
QGIS_MAJOR ?= 3
PLUGINS_DIR ?= $(HOME)/Library/Application Support/QGIS/QGIS$(QGIS_MAJOR)/profiles/default/python/plugins

.PHONY: help docker-build docker-build-qgis4 test test-core test-qgis3 test-qgis4 lint screens \
        test-local test-core-local test-qt6 check-qt6 link zip clean

help:
	@echo "Targets (Docker, no host QGIS needed):"
	@echo "  test              QGIS 3 and QGIS 4 test runs (the gate before review)"
	@echo "  test-core         pure-Python tests only (fast)"
	@echo "  test-qgis3        unit + end-to-end tests on QGIS 3 ($(QGIS3_BASE))"
	@echo "  test-qgis4        unit + end-to-end tests on QGIS 4 ($(QGIS4_BASE)), plus the Qt 6 code check"
	@echo "  lint              the plugins.qgis.org checks (flake8 + bandit + detect-secrets)"
	@echo "  screens           run the end-to-end flow and save docs/screens/*.png"
	@echo "  docker-build      build the QGIS 3 test image; docker-build-qgis4 builds the QGIS 4 one"
	@echo "With a local QGIS or PyQt6:"
	@echo "  test-local        unit + end-to-end tests with QGIS_PYTHON"
	@echo "  test-qt6          the plugin's pages, sign-in and HTTP client on PyQt6 (QT6_PYTHON)"
	@echo "  check-qt6         Qt enum names and calls that only Qt 5 accepts (QT6_PYTHON)"
	@echo "  link              symlink $(PLUGIN)/ into the QGIS profile (QGIS_MAJOR=4 for QGIS 4)"
	@echo "  zip               $(PLUGIN)-$(VERSION).zip for Plugins › Install from ZIP"
	@echo "  clean             remove caches, test results and the zip"

docker-build:
	docker build -f $(DOCKERFILE) --build-arg QGIS_IMAGE=$(QGIS3_BASE) -t $(IMAGE) .

docker-build-qgis4:
	docker build -f $(DOCKERFILE) --build-arg QGIS_IMAGE=$(QGIS4_BASE) -t $(IMAGE_QGIS4) .

test: test-qgis3 test-qgis4

test-core: docker-build
	$(DOCKER_RUN) pytest -q tests/test_core.py

test-qgis3: docker-build
	$(DOCKER_RUN) pytest -q tests

test-qgis4: docker-build-qgis4
	$(DOCKER_RUN_QGIS4) pytest -q tests
	$(DOCKER_RUN_QGIS4) python3 tools/qt6_check.py $(PLUGIN) tests tools

# Static analysis mirrors the three checks plugins.qgis.org runs on plugin submission: default
# flake8 rules at line-length 120, bandit, detect-secrets.
#
# Scope differs per tool on purpose. flake8 covers tests and tools too — style debt in tests is
# still debt. bandit covers only the plugin: it is the code that ships, and B101 (assert_used)
# would otherwise fire on every pytest assertion.
#
# NO SEVERITY FLOOR ON BANDIT. qgis.org applies its own per-rule severity (B110 try_except_pass is
# critical there, LOW in bandit), so -ll would hide exactly what qgis.org blocks on.
#
# detect-secrets runs WITHOUT --baseline: with it, detect-secrets-hook calls `git diff` to check the
# baseline is staged, which fails wherever the container cannot read the repo (the CI runner).
# Allowlist findings with an inline `# pragma: allowlist secret`. .secrets.baseline stays committed
# because the qgis.org scanner looks for it.
lint: docker-build
	$(DOCKER_RUN) flake8 --max-line-length=120 $(PLUGIN) tests tools
	$(DOCKER_RUN) bandit -r $(PLUGIN) --quiet
	$(DOCKER_RUN) bash -c 'detect-secrets-hook $$(find $(PLUGIN) tests tools -type f)'

screens: docker-build
	$(DOCKER_RUN) python3 -m tests.e2e_flow docs/screens

test-local:
	$(QGIS_PYTHON) -m pytest -q tests

test-core-local:
	$(QGIS_PYTHON) -m pytest -q tests/test_core.py

test-qt6:
	QT_QPA_PLATFORM=offscreen $(QT6_PYTHON) -m tests.qt6_ui

check-qt6:
	$(QT6_PYTHON) tools/qt6_check.py $(PLUGIN) tests tools

link:
	ln -sfn "$(CURDIR)/$(PLUGIN)" "$(PLUGINS_DIR)/$(PLUGIN)"

zip:
	rm -f $(PLUGIN)-$(VERSION).zip
	zip -qr $(PLUGIN)-$(VERSION).zip $(PLUGIN) -x '*/__pycache__/*' '*.pyc'
	@echo $(PLUGIN)-$(VERSION).zip

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name '*.pyc' -delete
	rm -rf .pytest_cache test-results $(PLUGIN)-*.zip
