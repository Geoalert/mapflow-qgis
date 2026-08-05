# Test and lint runner for mapflow-qgis.
#
# All targets run inside the qgis/qgis:release-3_28 Docker image so
# host setup is irrelevant. See spec/004_stack.md and tests/README.md
# for tier definitions.

IMAGE ?= mapflow-qgis-tests
DOCKERFILE ?= Dockerfile.tests
DOCKER_RUN = docker run --rm -v "$(CURDIR)":/app -w /app $(IMAGE)

.PHONY: help docker-build test test-functional test-qgis test-ui lint clean

help:
	@echo "Targets:"
	@echo "  docker-build      Build the test image ($(IMAGE))"
	@echo "  test-functional   Run pure-logic tests under tests/functional/"
	@echo "  test-qgis         Run QGIS-runtime tests under tests/qgis/"
	@echo "  test-ui           Run UI tests under tests/ui/ (xvfb-run)"
	@echo "  test              Run all three tiers"
	@echo "  lint              Run the plugins.qgis.org checks (flake8 + bandit + detect-secrets)"
	@echo "  clean             Remove pytest cache + bytecode"

docker-build:
	docker build -f $(DOCKERFILE) -t $(IMAGE) .

test-functional: docker-build
	$(DOCKER_RUN) pytest tests/functional

test-qgis: docker-build
	$(DOCKER_RUN) pytest tests/qgis

test-ui: docker-build
	# pytest exits 5 when no tests are collected; the UI tier is an
	# empty harness today, so treat that as a pass. Remove this guard
	# once the first UI test lands.
	$(DOCKER_RUN) bash -c 'xvfb-run -a pytest tests/ui; rc=$$?; [ $$rc -eq 0 ] || [ $$rc -eq 5 ]'

test: test-functional test-qgis test-ui

# Static analysis mirrors the three checks plugins.qgis.org runs on plugin
# submission, using their invocations so a green run here predicts a clean
# scan there: default flake8 rules at line-length 120, bandit at medium-or-
# higher severity, detect-secrets against the committed baseline.
#
# Scope differs per tool on purpose. flake8 covers tests too — style debt in
# tests is still debt. bandit covers only mapflow/: it is the code that ships,
# and B101 (assert_used) would otherwise fire on every pytest assertion.
lint: docker-build
	$(DOCKER_RUN) flake8 --max-line-length=120 mapflow tests
	$(DOCKER_RUN) bandit -r mapflow -ll --quiet
	$(DOCKER_RUN) bash -c 'detect-secrets-hook --baseline .secrets.baseline $$(find mapflow tests -type f)'

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name '*.pyc' -delete
	rm -rf .pytest_cache
