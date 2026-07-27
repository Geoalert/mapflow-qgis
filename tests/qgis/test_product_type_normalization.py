"""QGIS-tier tests for case-insensitive productType handling in the mosaic selection rules.

`productType` casing varies by provider: My Imagery search sends 'MOSAIC'/'IMAGE', other search
providers send 'Mosaic'/'Image'. The mosaic-specific selection rules used the title-case literal
'Mosaic', so a My Imagery 'MOSAIC' was not recognized as a mosaic. Normalization fixes that.
"""
from mapflow.functional.service.provider_service import (
    normalized_product_types, MOSAIC_PRODUCT_TYPES,
)


def test_mosaic_casings_all_recognized_as_mosaic():
    for casing in ("MOSAIC", "Mosaic", "mosaic"):
        assert normalized_product_types([casing]) == MOSAIC_PRODUCT_TYPES


def test_mixed_casing_of_same_category_collapses_to_one():
    # My Imagery 'MOSAIC' + another provider's 'Mosaic' must count as the SAME product type,
    # so "must be of the same product type" no longer trips (len == 1).
    assert normalized_product_types(["MOSAIC", "Mosaic"]) == MOSAIC_PRODUCT_TYPES
    assert len(normalized_product_types(["IMAGE", "Image"])) == 1


def test_mosaic_and_image_stay_distinct():
    # Case-insensitivity must not collapse genuinely different categories.
    assert len(normalized_product_types(["MOSAIC", "IMAGE"])) == 2
    assert normalized_product_types(["IMAGE"]) != MOSAIC_PRODUCT_TYPES


def test_all_mosaic_selection_is_recognized():
    # The multi-provider "mosaics are combinable" rule keys off this equality.
    assert normalized_product_types(["MOSAIC", "mosaic", "Mosaic"]) == MOSAIC_PRODUCT_TYPES
