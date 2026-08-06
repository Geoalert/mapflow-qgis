"""Every test file must live inside a tier directory, or it silently never runs.

`make test` invokes pytest three times with explicit paths — `tests/functional`,
`tests/qgis`, `tests/ui` — which override `testpaths = tests` in pytest.ini. A file
dropped at the `tests/` root is therefore collected by neither, and CI stays green
while the tests inside it never execute.

That is not hypothetical: `tests/test_imagery_search_multi.py` sat there with 23 test
functions that had never run once. Four of them failed the moment they were wired in,
and three of those were masked by a harness bug that made the assertions vacuous.

This guard is deliberately a test rather than a lint rule: it costs nothing, it runs in
the same CI job as everything else, and it fails loudly with the offending filename.
"""
from pathlib import Path

TESTS_ROOT = Path(__file__).resolve().parent.parent
TIERS = ("functional", "qgis", "ui")


def test_no_test_files_outside_a_tier():
    stranded = sorted(path.name for path in TESTS_ROOT.glob("test_*.py"))
    assert not stranded, (
        f"Test file(s) at the tests/ root will never be collected by `make test`: "
        f"{stranded}. Move each into one of {TIERS} — pick the tier by runtime need "
        f"(see spec/004_stack.md), not by whether it looks like a unit test."
    )


def test_every_tier_directory_exists():
    """A renamed or deleted tier would make `make test` fail obscurely at the pytest
    invocation rather than here, where the reason is stated."""
    missing = [tier for tier in TIERS if not (TESTS_ROOT / tier).is_dir()]
    assert not missing, f"Missing tier director{'y' if len(missing) == 1 else 'ies'}: {missing}"
