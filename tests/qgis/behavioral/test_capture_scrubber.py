"""The scrubber in capture_fixtures.py.

This is the only thing standing between a real account's data and a committed fixture, so it
is tested rather than trusted. The properties that matter:

* nothing identifying survives — ids, emails, credentials, presigned URLs;
* replacement is *consistent*, because a project id in the list response must still match the
  id in the detail response or the two fixtures cannot be used in one test.
"""
from capture_fixtures import EMAIL_RE, UUID_RE, Scrubber

#: What the scrubber writes in place of a credential. Held in a constant so the assertions
#: below do not put a quoted string next to the word "password" — detect-secrets reads that
#: shape as a hardcoded credential, and it is right to.
REDACTED = "redacted"


def test_uuids_are_replaced():
    payload = {"id": "3f2504e0-4f89-41d3-9a0c-0305e82c3301"}
    scrubbed = Scrubber().scrub(payload)
    assert scrubbed["id"] != payload["id"]
    assert UUID_RE.fullmatch(scrubbed["id"]), "the shape must survive so parsing still works"


def test_the_same_id_scrubs_to_the_same_value_across_files():
    """Cross-file references are the whole point of a fixture set."""
    scrubber = Scrubber()
    real = "3f2504e0-4f89-41d3-9a0c-0305e82c3301"
    in_list = scrubber.scrub({"results": [{"id": real}]})
    in_detail = scrubber.scrub({"id": real, "name": "Project A"})
    assert in_list["results"][0]["id"] == in_detail["id"]


def test_different_ids_stay_different():
    scrubber = Scrubber()
    out = scrubber.scrub({
        "a": "3f2504e0-4f89-41d3-9a0c-0305e82c3301",
        "b": "9c858901-8a57-4791-81fe-4c455b099bc9",
    })
    assert out["a"] != out["b"]


def test_emails_are_replaced_wherever_they_appear():
    out = Scrubber().scrub({"owner": {"email": "real.person@customer.com"},
                            "note": "contact real.person@customer.com about this"})
    assert "real.person@customer.com" not in repr(out)
    assert EMAIL_RE.fullmatch(out["owner"]["email"])


def test_credentials_are_redacted_not_transformed():
    # The literals below are invented for this assertion. detect-secrets flags any value under
    # a credential-ish key, which is the behaviour we want everywhere else in the repo.
    out = Scrubber().scrub({
        "token": "Basic aW52ZW50ZWQtZm9yLXRoaXMtdGVzdA==",  # pragma: allowlist secret
        "password": "not-a-real-password",  # pragma: allowlist secret
    })
    assert set(out.values()) == {REDACTED}, "both credential fields must be replaced"


def test_presigned_url_signature_is_stripped():
    """A live AWS signature in a fixture would be both a leak and a detect-secrets failure."""
    url = ("https://bucket.s3.amazonaws.com/tile.tif"
           "?X-Amz-Signature=deadbeefcafe&X-Amz-Credential=AKIAEXAMPLE")
    out = Scrubber().scrub({"downloadUrl": url})
    assert "deadbeefcafe" not in out["downloadUrl"]
    assert "AKIAEXAMPLE" not in out["downloadUrl"]
    assert out["downloadUrl"].startswith("https://bucket.s3.amazonaws.com/tile.tif")


def test_access_token_is_stripped_whatever_key_holds_the_url():
    """The leak this test exists for: a live Mapbox token reached a commit.

    The scrubber used to strip query strings only under a list of known key names, and
    `/user/status` returns the Mapbox tile URL under `webPreviewUrl`, which was not on it.
    detect-secrets did not flag it either; GitHub push protection did. So the rule is now
    about the *value* being URL-shaped, and no key list can go stale again.
    """
    out = Scrubber().scrub({
        "webPreviewUrl": "https://api.tiles.mapbox.com/v4/mapbox.satellite/"
                         "{z}/{x}/{y}.jpg?access_token=pk.eyJ1IjoiZXhhbXBsZSJ9.aGVsbG8",
    })
    assert "pk.eyJ1IjoiZXhhbXBsZSJ9" not in out["webPreviewUrl"]
    assert "access_token=scrubbed" in out["webPreviewUrl"]


def test_the_useful_part_of_a_url_survives():
    """Over-stripping would cost the fixture its realism — the tile template must remain."""
    out = Scrubber().scrub({
        "webPreviewUrl": "https://tiles.example.com/v4/sat/{z}/{x}/{y}.jpg"
                         "?access_token=SECRETVALUE&format=jpg&quality=90",
    })
    url = out["webPreviewUrl"]
    assert "{z}/{x}/{y}" in url, "the XYZ template is what the provider code parses"
    assert "format=jpg" in url and "quality=90" in url, "non-credential params are kept"
    assert "SECRETVALUE" not in url


def test_file_hashes_are_blanked_but_keep_their_shape():
    """Not a credential, but detect-secrets reads a long hex string as one, so a captured
    checksum fails lint on every future capture."""
    out = Scrubber().scrub({"checksum": "9f2a4c1e" * 8})
    assert set(out["checksum"]) == {"0"}
    assert len(out["checksum"]) == 64, "anything parsing the field still sees a hash shape"


def test_a_url_without_a_query_is_untouched():
    url = "https://tiles.example.com/v4/sat/{z}/{x}/{y}.jpg"
    assert Scrubber().scrub({"url": url})["url"] == url


def test_ids_inside_urls_are_scrubbed_too():
    out = Scrubber().scrub(
        {"url": "https://host/rest/rasters/image/3f2504e0-4f89-41d3-9a0c-0305e82c3301/download"})
    assert "3f2504e0-4f89-41d3-9a0c-0305e82c3301" not in out["url"]


def test_non_identifying_values_are_left_alone():
    """Over-scrubbing is a failure too — the fixture has to stay a realistic payload."""
    payload = {"name": "🏠 Buildings", "status": "OK", "percentCompleted": 100,
               "workflowDef": "buildings", "enabled": True, "cost": None}
    assert Scrubber().scrub(payload) == payload


def test_nested_lists_and_dicts_are_walked():
    out = Scrubber().scrub({"results": [{"aois": [{"id": "3f2504e0-4f89-41d3-9a0c-0305e82c3301"}]}]})
    assert out["results"][0]["aois"][0]["id"] != "3f2504e0-4f89-41d3-9a0c-0305e82c3301"


def test_report_counts_what_it_changed():
    scrubber = Scrubber()
    scrubber.scrub({"id": "3f2504e0-4f89-41d3-9a0c-0305e82c3301",
                    "email": "a@b.com",
                    "token": "secret-value"})
    assert scrubber.report["uuids"] == 1
    assert scrubber.report["pii_values"] >= 1
