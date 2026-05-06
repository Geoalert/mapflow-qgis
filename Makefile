# Test runner for mapflow-qgis.
#
# All targets run inside the qgis/qgis:release-3_28 Docker image so
# host setup is irrelevant. See spec/004_stack.md and tests/README.md
# for tier definitions.

IMAGE ?= mapflow-qgis-tests
DOCKERFILE ?= Dockerfile.tests
DOCKER_RUN = docker run --rm -v "$(CURDIR)":/app -w /app $(IMAGE)

.PHONY: help docker-build test test-functional test-qgis test-ui clean

help:
	@echo "Targets:"
	@echo "  docker-build      Build the test image ($(IMAGE))"
	@echo "  test-functional   Run pure-logic tests under tests/functional/"
	@echo "  test-qgis         Run QGIS-runtime tests under tests/qgis/"
	@echo "  test-ui           Run UI tests under tests/ui/ (xvfb-run)"
	@echo "  test              Run all three tiers"
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

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name '*.pyc' -delete
	rm -rf .pytest_cache
