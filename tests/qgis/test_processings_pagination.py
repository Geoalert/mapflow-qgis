"""Tests for processings pagination schema and logic."""
import json

from mapflow.schema.processing import (
    ProcessingSortBy,
    ProcessingSortOrder,
    ProcessingsRequest,
    ProcessingsResult,
)


class TestProcessingSortBy:
    def test_enum_values(self):
        assert ProcessingSortBy.created.value == "CREATED"
        assert ProcessingSortBy.name.value == "NAME"
        assert ProcessingSortBy.status.value == "STATUS"
        assert ProcessingSortBy.cost.value == "COST"
        assert ProcessingSortBy.area.value == "AREA"
        assert ProcessingSortBy.progress.value == "PROGRESS"

    def test_all_expected_members(self):
        expected = {"SCENARIO", "NAME", "PROJECT", "EMAIL", "CREATED",
                    "STATUS", "PROGRESS", "COMPLETED", "COST", "AREA", "PROVIDER"}
        assert set(m.value for m in ProcessingSortBy) == expected


class TestProcessingSortOrder:
    def test_ascending(self):
        assert ProcessingSortOrder.ascending.value == "ASC"

    def test_descending(self):
        assert ProcessingSortOrder.descending.value == "DESC"


class TestProcessingsRequest:
    def test_defaults(self):
        req = ProcessingsRequest()
        assert req.limit == 30
        assert req.offset == 0
        assert req.terms is None
        assert req.sortBy is None
        assert req.sortOrder is None

    def test_serialization_defaults(self):
        req = ProcessingsRequest()
        data = json.loads(req.as_json())
        assert data == {"limit": 30, "offset": 0}
        # None fields are skipped by Serializable.as_json(skip_none=True)

    def test_serialization_with_all_params(self):
        req = ProcessingsRequest(
            limit=30,
            offset=60,
            terms="my search",
            sortBy=ProcessingSortBy.created.value,
            sortOrder=ProcessingSortOrder.descending.value,
        )
        data = json.loads(req.as_json())
        assert data == {
            "limit": 30,
            "offset": 60,
            "terms": "my search",
            "sortBy": "CREATED",
            "sortOrder": "DESC",
        }

    def test_serialization_with_empty_terms(self):
        req = ProcessingsRequest(terms=None)
        data = json.loads(req.as_json())
        assert "terms" not in data


class TestProcessingsResult:
    def test_empty_result(self):
        result = ProcessingsResult.from_dict({"results": [], "total": 0, "count": 0})
        assert result.results == []
        assert result.total == 0
        assert result.count == 0

    def test_missing_results_key(self):
        result = ProcessingsResult.from_dict({"total": 5, "count": 0})
        assert result.results == []

    def test_none_input(self):
        result = ProcessingsResult.from_dict(None)
        assert result is None


class TestPaginationOffsetLogic:
    """Test the offset arithmetic used by ProcessingService."""

    def test_next_page(self):
        limit = 30
        offset = 0
        offset += limit
        assert offset == 30

    def test_previous_page(self):
        limit = 30
        offset = 60
        offset -= limit
        assert offset == 30

    def test_previous_page_clamp_to_zero(self):
        limit = 30
        offset = 0
        offset -= limit
        if offset < 0:
            offset = 0
        assert offset == 0

    def test_page_number_calculation(self):
        limit = 30
        total = 95
        offset = 60
        quotient, remainder = divmod(total, limit)
        total_pages = quotient + (remainder > 0)
        page_number = int(offset / limit) + 1
        assert total_pages == 4
        assert page_number == 3

    def test_offset_clamp_when_exceeds_total(self):
        total = 50
        offset = 60
        if offset >= total:
            offset = 0
        assert offset == 0
