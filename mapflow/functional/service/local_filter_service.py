"""Client-side narrowing of an already-fetched imagery-search result set.

Pure computation: features in, the set of results that fail the current filter out; and the
comparison that decides whether the filter widgets now ask for MORE than the last search fetched
(the widen `(!)` indicator). No widget, no QGIS, no network — so it is tested in the functional
tier. The widget reads that produce a `FilterCriteria`, and the table/layer changes that act on
the result, stay with the caller (`mapflow.py`), which is why they are not here.

`spec/007_architecture.md` § Services: LocalFilterService owns "client-side narrowing of an
already-fetched result set, and the 'filter is wider than what was fetched' warning".
"""
from dataclasses import dataclass
from typing import Callable, List, Optional, Set

from PyQt5.QtCore import QDate, QDateTime, QObject, Qt

from ...schema.catalog import ProductType


def utc_date_from_iso(value: Optional[str]) -> Optional[QDate]:
    """Parse an ISO-8601 timestamp (as stored in ``searchParams`` or a result's
    ``acquisitionDate``) into a UTC QDate, or None when absent/unparseable.

    A free function, not a method: the template baseline (`mapflow.py`, → TemplateService) needs
    the same parse, and a pure date conversion is no reason for template code to depend on the
    filter service.
    """
    if not value:
        return None
    parsed = QDateTime.fromString(value, Qt.ISODateWithMs)
    if not parsed.isValid():
        parsed = QDateTime.fromString(value, Qt.ISODate)
    return parsed.toUTC().date() if parsed.isValid() else None


@dataclass
class FilterCriteria:
    """The filter-widget state, resolved to values, that a local filter pass needs.

    Assembled by the caller from the widgets and `app_context` (the provider set folds in the
    user's available providers), so the service reads neither. ``None`` on ``provider_set`` /
    ``product_filter`` means "no filtering on that axis"; the cloud/intersection sentinels
    (>=100, <=0) match the widgets' "off" positions.
    """
    date_from: Optional[QDate]
    date_to: Optional[QDate]
    max_cloud_cover: float
    min_intersection: float
    off_nadir_filtered: bool
    min_off_nadir: float
    max_off_nadir: float
    provider_set: Optional[Set[str]]   # lowercased api-names to keep, or None for all
    product_filter: Optional[Set[str]]  # {'MOSAIC'} / {'IMAGE'}, or None for all


class LocalFilterService(QObject):

    @staticmethod
    def to_float(value) -> Optional[float]:
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def passes_optional(value, predicate: Callable) -> bool:
        """A metadata filter clause where a missing value matches any condition: ``None`` passes,
        otherwise the row must satisfy ``predicate``. My Imagery results carry mostly-empty
        metadata (no date/cloud), which the server counts as matching every filter; the local
        filter follows the same rule so user imagery is not hidden when a filter is set."""
        return value is None or predicate(value)

    @staticmethod
    def product_category(product_type) -> str:
        """Map a result's ``productType`` to a Mosaic/Image category: 'Mosaic' -> MOSAIC, anything
        else -> IMAGE.
        #WARNING: ``productType`` is free text (e.g. 'OPTICAL', 'Image', ''); this
        Mosaic-vs-everything-else split is a product decision and may misclassify some providers."""
        if str(product_type).strip().lower() == ProductType.mosaic.lower():
            return ProductType.mosaic.upper()
        return ProductType.image.upper()

    def unfit_indices(self, features: list, criteria: FilterCriteria) -> Set[int]:
        """``local_index`` of every result (GeoJSON feature) that FAILS ``criteria``: date range,
        cloud cover, off-nadir range, provider selection / availability, product type, and (where
        an intersection reference exists) min intersection %. A per-feature parsing error never
        hides the row (treated as fit)."""
        unfit: Set[int] = set()
        for feature in features:
            props = feature.get("properties", {})
            local_index = props.get("local_index")
            if local_index is None:
                continue
            try:
                # Missing metadata matches any condition: user imagery (My Imagery search) has no
                # acquisition date / cloud cover, and the server already treats a NULL column as
                # satisfying every predicate — the local filter must not then demote those rows.
                acquisition_date = utc_date_from_iso(props.get("acquisitionDate"))
                date_ok = self.passes_optional(
                    acquisition_date, lambda d: criteria.date_from <= d <= criteria.date_to)
                cloud_cover = self.to_float(props.get("cloudCover"))
                # 100% = don't filter by cloud at all.
                cloud_ok = criteria.max_cloud_cover >= 100 or self.passes_optional(
                    cloud_cover, lambda c: c <= criteria.max_cloud_cover)
                off_nadir = self.to_float(props.get("offNadirAngle"))
                # Full 0-30 range = don't filter; a missing angle passes the range check.
                off_nadir_ok = not criteria.off_nadir_filtered or self.passes_optional(
                    off_nadir, lambda a: criteria.min_off_nadir <= a <= criteria.max_off_nadir)
                if criteria.provider_set is None:
                    provider_ok = True
                else:
                    provider_name = props.get("providerName")
                    provider_ok = (provider_name is not None
                                   and str(provider_name).lower() in criteria.provider_set)
                product_ok = (criteria.product_filter is None
                              or self.product_category(props.get("productType"))
                              in criteria.product_filter)
                # Intersection % comes from the backend (aoiIntersectionPercent, computed against
                # the searched AOI / the template's AOIs), not recomputed locally against a
                # sub-selection. 0 = don't filter; a missing value passes (like other metadata).
                if criteria.min_intersection <= 0:
                    intersection_ok = True
                else:
                    aoi_intersection = self.to_float(props.get("aoiIntersectionPercent"))
                    intersection_ok = self.passes_optional(
                        aoi_intersection, lambda pct: pct >= criteria.min_intersection)
                fit = (date_ok and cloud_ok and off_nadir_ok and provider_ok
                       and product_ok and intersection_ok)
            except (AttributeError, TypeError, ValueError):
                # Metadata that is not the shape this code expects: a non-mapping `properties`
                # raises AttributeError, a value of the wrong type raises TypeError on the
                # comparisons, an unparseable one ValueError.
                fit = True  # never hide a row because of a parsing error
            if not fit:
                unfit.add(local_index)
        return unfit

    def widen_messages(self, current: dict, baseline: Optional[dict]) -> List[str]:
        """Human-readable list of the ways ``current`` filter values are WIDER than the
        ``baseline`` that fetched the current results — relaxing them cannot surface more images
        without a new search. Empty when none, or when there is no baseline. Both dicts are the
        shape `mapflow.py` builds for a search baseline."""
        if not baseline:
            return []
        messages = []
        cur_from, cur_to = current.get("date_from"), current.get("date_to")
        base_from, base_to = baseline.get("date_from"), baseline.get("date_to")
        if base_from is not None and cur_from is not None and cur_from < base_from:
            messages.append(self.tr("Start date {cur} is earlier than searched ({base})").format(
                cur=cur_from.toString("yyyy-MM-dd"), base=base_from.toString("yyyy-MM-dd")))
        if base_to is not None and cur_to is not None and cur_to > base_to:
            messages.append(self.tr("End date {cur} is later than searched ({base})").format(
                cur=cur_to.toString("yyyy-MM-dd"), base=base_to.toString("yyyy-MM-dd")))
        cur_cloud, base_cloud = current.get("max_cloud_cover"), baseline.get("max_cloud_cover")
        if base_cloud is not None and cur_cloud is not None and cur_cloud > base_cloud:
            messages.append(self.tr("Max cloud cover {cur}% is higher than searched ({base}%)")
                            .format(cur=cur_cloud, base=int(base_cloud)))
        cur_int, base_int = current.get("min_intersection"), baseline.get("min_intersection")
        if base_int is not None and cur_int is not None and cur_int < base_int:
            messages.append(self.tr("Min intersection {cur}% is lower than searched ({base}%)")
                            .format(cur=cur_int, base=int(base_int)))
        cur_off_lo, cur_off_hi = current.get("min_off_nadir"), current.get("max_off_nadir")
        base_off_lo, base_off_hi = baseline.get("min_off_nadir"), baseline.get("max_off_nadir")
        if base_off_lo is not None and base_off_hi is not None \
                and cur_off_lo is not None and cur_off_hi is not None \
                and (cur_off_lo < base_off_lo or cur_off_hi > base_off_hi):
            messages.append(self.tr("Off-nadir range {lo}-{hi}° is wider than searched ({blo}-{bhi}°)")
                            .format(lo=cur_off_lo, hi=cur_off_hi,
                                    blo=int(base_off_lo), bhi=int(base_off_hi)))
        base_products = baseline.get("product_types")
        if base_products:
            extra = [p for p in (current.get("product_types") or []) if p not in base_products]
            if extra:
                messages.append(self.tr("Product type(s) not searched: {extra}").format(
                    extra=", ".join(extra)))
        base_providers = baseline.get("data_providers")
        if base_providers:
            cur_providers = current.get("data_providers") or []
            if not cur_providers:
                messages.append(self.tr("Showing all providers, but search was limited to: {base}")
                                .format(base=", ".join(base_providers)))
            else:
                extra = [p for p in cur_providers if p not in base_providers]
                if extra:
                    messages.append(self.tr("Provider(s) not searched: {extra}").format(
                        extra=", ".join(extra)))
        return messages
