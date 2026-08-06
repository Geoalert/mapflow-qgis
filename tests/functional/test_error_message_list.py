"""The merged error registry must not lose entries to key collisions.

``mapflow/errors/errors.py`` builds one ``ErrorMessageList`` at import time by
merging ``ProcessingErrors``, ``DataErrors`` and ``ApiErrors``. ``update()``
delegates to ``dict.update``, which overwrites silently on conflict — so the
same code defined in two registries would shadow one description and the user
would be shown the wrong error text, with nothing to indicate it happened.

This invariant lived as two ``assert`` statements inside ``update()`` until
WAL 3.7.0 §1 (Bandit B101: asserts are stripped under ``python -O``, so the
check could vanish in exactly the packaged builds where it still mattered).
The three registries are statically defined, so the invariant is a property of
the source rather than of any particular run: a test proves it in CI, keeps
working under ``-O``, and costs nothing at plugin start-up.

Tier note: this is pure logic — dict keys, no QGIS state — so it belongs in
``tests/functional/`` per spec/004_stack.md, not ``tests/qgis/`` as WAL 3.7.0
originally specified. ``tests/functional/test_error_message.py`` already
imports this same module.
"""
import itertools

import pytest

from mapflow.errors.api_errors import ApiErrors
from mapflow.errors.data_errors import DataErrors
from mapflow.errors.processing_errors import ProcessingErrors

# The exact set merged in mapflow/errors/errors.py. If a fourth registry is
# added there, add it here too — otherwise its collisions go unnoticed.
REGISTRIES = (ProcessingErrors, DataErrors, ApiErrors)

REGISTRY_PAIRS = tuple(itertools.combinations(REGISTRIES, 2))
PAIR_IDS = tuple(f"{left.__name__}-vs-{right.__name__}" for left, right in REGISTRY_PAIRS)


@pytest.mark.parametrize("left,right", REGISTRY_PAIRS, ids=PAIR_IDS)
def test_error_descriptions_do_not_collide(left, right):
    overlap = set(left().error_descriptions) & set(right().error_descriptions)
    assert not overlap, (
        f"{left.__name__} and {right.__name__} both define error code(s) "
        f"{sorted(overlap)}; the later update() would silently win"
    )


@pytest.mark.parametrize("left,right", REGISTRY_PAIRS, ids=PAIR_IDS)
def test_message_descriptions_do_not_collide(left, right):
    overlap = set(left().message_descriptions) & set(right().message_descriptions)
    assert not overlap, (
        f"{left.__name__} and {right.__name__} both define message key(s) "
        f"{sorted(overlap)}; the later update() would silently win"
    )


def test_merged_registry_keeps_every_key():
    """Belt-and-braces: the assembled registry holds the sum of its parts.

    The pairwise tests above localise a collision to a specific pair; this one
    catches the case where the merge itself drops entries for some other
    reason, and exercises the real module-level object the plugin uses.
    """
    from mapflow.errors.errors import error_message_list

    expected_errors = sum(len(registry().error_descriptions) for registry in REGISTRIES)
    expected_messages = sum(len(registry().message_descriptions) for registry in REGISTRIES)

    assert len(error_message_list.error_descriptions) == expected_errors
    assert len(error_message_list.message_descriptions) == expected_messages
