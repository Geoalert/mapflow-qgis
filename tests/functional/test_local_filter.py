"""Functional-tier tests for LocalFilterService — the pure client-side narrowing of an
already-fetched imagery-search / template result set, and the widen `(!)` comparison.

Pure computation, so no QGIS runtime: a `FilterCriteria` carries the resolved widget state in,
and features are plain GeoJSON dicts (the same shape that fills the table). The widget reads that
build a `FilterCriteria`, and the table/layer changes that act on the result, live in
`mapflow.py` and are covered in `tests/qgis/test_local_filter.py`.

Ported from that qgis-tier file when the computation moved to LocalFilterService; the behaviours
(missing metadata matches any filter, backend intersection %, string cloud, Mosaic/Image split)
are unchanged.
"""
from PyQt5.QtCore import QDate

from mapflow.functional.service.local_filter_service import FilterCriteria, LocalFilterService


def _criteria(date_from=None, date_to=None, max_cloud_cover=50, min_intersection=50,
              off_nadir_filtered=False, min_off_nadir=0, max_off_nadir=30,
              provider_set=None, product_filter=None) -> FilterCriteria:
    return FilterCriteria(
        date_from=date_from or QDate(2025, 1, 1),
        date_to=date_to or QDate(2025, 12, 31),
        max_cloud_cover=max_cloud_cover,
        min_intersection=min_intersection,
        off_nadir_filtered=off_nadir_filtered,
        min_off_nadir=min_off_nadir,
        max_off_nadir=max_off_nadir,
        provider_set=provider_set,
        product_filter=product_filter,
    )


def _feature(local_index, date, cloud, intersection=None):
    props = {"local_index": local_index, "acquisitionDate": date, "cloudCover": cloud}
    if intersection is not None:
        props["aoiIntersectionPercent"] = intersection
    return {"type": "Feature", "properties": props}


def _features():
    """Index 0 fits; 1 out of date range; 2 too cloudy; 3 low backend AOI intersection (~1%)."""
    return [
        _feature(0, "2025-03-01T00:00:00Z", 10, intersection=100),
        _feature(1, "2020-01-01T00:00:00Z", 5, intersection=100),
        _feature(2, "2025-03-01T00:00:00Z", 90, intersection=100),
        _feature(3, "2025-03-01T00:00:00Z", 10, intersection=1),
    ]


def _service():
    return LocalFilterService()


# ---------- off-nadir ----------

def _off_nadir_feature(local_index, angle):
    return {"type": "Feature", "properties": {
        "local_index": local_index, "acquisitionDate": "2025-03-01T00:00:00Z",
        "cloudCover": 0, "offNadirAngle": angle}}


def test_off_nadir_out_of_range_demoted_missing_passes():
    criteria = _criteria(min_intersection=0, max_cloud_cover=100,
                         off_nadir_filtered=True, min_off_nadir=0, max_off_nadir=5)
    features = [
        _off_nadir_feature(0, 3),     # within [0, 5] -> fit
        _off_nadir_feature(1, 10),    # outside -> unfit
        _off_nadir_feature(2, None),  # missing angle -> passes (missing matches any)
    ]

    assert _service().unfit_indices(features, criteria) == {1}


def test_off_nadir_full_range_does_not_filter():
    criteria = _criteria(min_intersection=0, max_cloud_cover=100, off_nadir_filtered=False)

    # Even an angle beyond the slider maximum passes when the range is full (= no filter).
    assert _service().unfit_indices([_off_nadir_feature(0, 45)], criteria) == set()


# ---------- date / cloud / intersection ----------

def test_unfit_indices_reject_date_cloud_and_intersection():
    unfit = _service().unfit_indices(_features(), _criteria())
    # 0 passes; 1 (date), 2 (cloud), 3 (intersection) fail.
    assert unfit == {1, 2, 3}


def test_unfit_matches_displayed_cloud_value():
    # At 50% the 90-cloud image is out and the 10-cloud one stays.
    unfit = _service().unfit_indices(_features(), _criteria(min_intersection=0, max_cloud_cover=50))
    assert 2 in unfit and 0 not in unfit


def test_unfit_handles_string_cloud_without_crashing():
    # Cloud arriving as a string must not abort the whole pass.
    features = _features()
    features[2]["properties"]["cloudCover"] = "90"  # string, still > 50
    unfit = _service().unfit_indices(features, _criteria(min_intersection=0, max_cloud_cover=50))
    assert 2 in unfit


def test_intersection_not_applied_when_min_is_zero():
    unfit = _service().unfit_indices(_features(), _criteria(min_intersection=0))
    # Only date (1) and cloud (2) fail; the tiny-overlap image (3) now passes.
    assert unfit == {1, 2}


def test_cloud_100_disables_cloud_filter():
    unfit = _service().unfit_indices(_features(), _criteria(min_intersection=0, max_cloud_cover=100))
    # Cloud no longer filters (image 2 passes); only the out-of-range date (1) fails.
    assert unfit == {1}


def test_intersection_uses_backend_percent():
    # The filter compares the backend aoiIntersectionPercent to the widget; footprint geometry
    # is irrelevant.
    features = [
        _feature(0, "2025-03-01T00:00:00Z", 10, intersection=80),
        _feature(1, "2025-03-01T00:00:00Z", 10, intersection=20),
    ]
    assert _service().unfit_indices(features, _criteria(min_intersection=50)) == {1}


def test_missing_intersection_percent_passes():
    # A result without a backend intersection value must not be hidden (missing matches any).
    feature = _feature(0, "2025-03-01T00:00:00Z", 10)
    assert _service().unfit_indices([feature], _criteria(min_intersection=50)) == set()


# ---------- My Imagery: missing metadata matches any filter ----------

def _my_imagery_feature(local_index):
    return _feature(local_index, None, None)


def test_missing_date_passes_date_filter():
    unfit = _service().unfit_indices([_my_imagery_feature(0)],
                                     _criteria(min_intersection=0, max_cloud_cover=100))
    assert unfit == set()


def test_missing_cloud_passes_cloud_filter():
    unfit = _service().unfit_indices([_my_imagery_feature(0)],
                                     _criteria(min_intersection=0, max_cloud_cover=30))
    assert unfit == set()


def test_missing_date_and_cloud_pass_with_both_filters_active():
    criteria = _criteria(min_intersection=0, max_cloud_cover=30,
                         date_from=QDate(2025, 1, 1), date_to=QDate(2025, 2, 1))
    assert _service().unfit_indices([_my_imagery_feature(0)], criteria) == set()


def test_populated_values_still_filter_both_directions():
    # Guard against over-correcting into "never filter": real out-of-range values must still fail.
    criteria = _criteria(min_intersection=0, max_cloud_cover=50,
                         date_from=QDate(2025, 1, 1), date_to=QDate(2025, 12, 31))
    features = [
        _feature(0, "2025-06-01T00:00:00Z", 10),   # in range, clear
        _feature(1, "2019-06-01T00:00:00Z", 10),   # date too old
        _feature(2, "2025-06-01T00:00:00Z", 80),   # too cloudy
    ]
    assert _service().unfit_indices(features, criteria) == {1, 2}


# ---------- provider / product-type ----------

def _feature_p(local_index, provider, product_type="OPTICAL"):
    f = _feature(local_index, "2025-03-01T00:00:00Z", 10)
    f["properties"]["providerName"] = provider
    f["properties"]["productType"] = product_type
    return f


def test_provider_filter_greys_disallowed_providers():
    criteria = _criteria(min_intersection=0, max_cloud_cover=100,
                         provider_set={"orbview_svn1"})
    features = [_feature_p(0, "orbview_svn1"), _feature_p(1, "orbview_svn3")]
    assert _service().unfit_indices(features, criteria) == {1}  # svn3 not allowed


def test_provider_filter_is_case_insensitive():
    criteria = _criteria(min_intersection=0, max_cloud_cover=100,
                         provider_set={"orbview_svn1"})
    assert _service().unfit_indices([_feature_p(0, "OrbView_SVN1")], criteria) == set()


def test_provider_filter_off_shows_all():
    criteria = _criteria(min_intersection=0, max_cloud_cover=100, provider_set=None)
    features = [_feature_p(0, "orbview_svn1"), _feature_p(1, "orbview_svn3")]
    assert _service().unfit_indices(features, criteria) == set()


def test_product_type_mosaic_only_greys_images():
    criteria = _criteria(min_intersection=0, max_cloud_cover=100, product_filter={"MOSAIC"})
    features = [_feature_p(0, "p", product_type="Mosaic"),
               _feature_p(1, "p", product_type="OPTICAL")]
    assert _service().unfit_indices(features, criteria) == {1}  # OPTICAL -> Image, filtered out


def test_product_type_image_only_greys_mosaics():
    criteria = _criteria(min_intersection=0, max_cloud_cover=100, product_filter={"IMAGE"})
    features = [_feature_p(0, "p", product_type="Mosaic"),
               _feature_p(1, "p", product_type="OPTICAL")]
    assert _service().unfit_indices(features, criteria) == {0}  # the Mosaic is filtered out


# ---------- pure helpers ----------

def test_passes_optional_rule():
    assert LocalFilterService.passes_optional(None, lambda v: False) is True  # missing -> passes
    assert LocalFilterService.passes_optional(5, lambda v: v < 10) is True
    assert LocalFilterService.passes_optional(50, lambda v: v < 10) is False


def test_product_category_maps_mosaic_else_image():
    assert LocalFilterService.product_category("Mosaic") == "MOSAIC"
    assert LocalFilterService.product_category("mosaic") == "MOSAIC"
    assert LocalFilterService.product_category("OPTICAL") == "IMAGE"
    assert LocalFilterService.product_category("") == "IMAGE"
    assert LocalFilterService.product_category(None) == "IMAGE"


# ---------- widen (!) comparison ----------

def _current(date_from=QDate(2025, 1, 1), date_to=QDate(2025, 6, 1), max_cloud_cover=30,
             min_intersection=40, min_off_nadir=0, max_off_nadir=30,
             product_types=("IMAGE",), data_providers=("providerA",)) -> dict:
    return {
        "date_from": date_from, "date_to": date_to,
        "max_cloud_cover": max_cloud_cover, "min_intersection": min_intersection,
        "min_off_nadir": min_off_nadir, "max_off_nadir": max_off_nadir,
        "product_types": list(product_types), "data_providers": list(data_providers),
    }


def test_no_widen_when_widgets_match_baseline():
    baseline = _current()  # identical
    assert _service().widen_messages(_current(), baseline) == []


def test_no_widen_without_a_baseline():
    assert _service().widen_messages(_current(), None) == []


def test_widen_detects_wider_cloud_and_earlier_date():
    baseline = _current(date_from=QDate(2025, 2, 1), max_cloud_cover=10)

    messages = _service().widen_messages(_current(), baseline)

    # Start date earlier (Jan < Feb) and cloud higher (30 > 10) are both flagged.
    assert any("Start date" in m for m in messages)
    assert any("cloud cover" in m for m in messages)
    assert not any("End date" in m for m in messages)


def test_widen_detects_lower_intersection_and_extra_provider():
    baseline = _current(min_intersection=80, data_providers=("providerB",))

    messages = _service().widen_messages(_current(), baseline)

    assert any("intersection" in m for m in messages)      # 40 < 80
    assert any("Provider" in m for m in messages)          # providerA not in [providerB]
