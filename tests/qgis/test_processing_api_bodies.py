"""QGIS-tier tests pinning the request bodies the processing API puts on the wire.

The template-images body is built from a ``Serializable`` schema rather than hand-rolled dict
juggling, so ``skip_none`` decides which optional fields appear. These tests lock that in."""
import json
from unittest.mock import MagicMock

from mapflow.functional.api.processing_api import ProcessingApi
from mapflow.http import RequestMode


def _api():
    api = ProcessingApi.__new__(ProcessingApi)
    api.http = MagicMock()
    return api


def _posted_body(api):
    return json.loads(api.http.post.call_args.kwargs["body"].decode())


def test_template_images_body_omits_aoi_ids_when_not_scoped():
    api = _api()

    api.get_template_images(template_id="tpl-1", callback=lambda r: None, limit=25, offset=50,
                            mode=RequestMode.INTERACTIVE)

    body = _posted_body(api)
    assert body == {"limit": 25, "offset": 50}  # aoiIds skipped (None), no filter fields sent


def test_template_images_body_includes_aoi_ids_when_scoped():
    api = _api()

    api.get_template_images(template_id="tpl-1", callback=lambda r: None,
                            limit=10, offset=0, aoi_ids=["a-1", "a-2"], mode=RequestMode.INTERACTIVE)

    body = _posted_body(api)
    assert body == {"limit": 10, "offset": 0, "aoiIds": ["a-1", "a-2"]}


def test_template_images_posts_to_images_endpoint():
    api = _api()

    api.get_template_images(template_id="tpl-9", callback=lambda r: None, mode=RequestMode.INTERACTIVE)

    assert api.http.post.call_args.kwargs["path"] == "processings/template/tpl-9/images"


def test_a_read_passes_on_the_mode_its_caller_chose():
    """The api cannot know what triggered a read; the caller does (spec/005 § Request modes)."""
    api = _api()

    api.get_template_images(template_id="tpl-9", callback=lambda r: None, mode=RequestMode.BACKGROUND)

    assert api.http.post.call_args.kwargs["mode"] is RequestMode.BACKGROUND


def test_a_request_that_changes_state_is_always_interactive():
    """A create that timed out may still have landed; sending it again would create twice."""
    api = _api()

    api.create_processing(data=MagicMock(), callback=MagicMock(), error_handler=MagicMock())

    assert api.http.post.call_args.kwargs["mode"] is RequestMode.INTERACTIVE
