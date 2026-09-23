from mapflow.schema.project import ShareProject, UserRole


def test_get_user_role_returns_owner_for_owner_email():
    share = ShareProject.from_dict(
        {
            "owners": [{"role": "owner", "email": "owner@example.com"}],
            "users": [{"role": "contributor", "email": "user@example.com"}],
        }
    )

    assert share.get_user_role("owner@example.com") == UserRole.owner


def test_get_user_role_returns_user_role_for_shared_user_email():
    share = ShareProject.from_dict(
        {
            "owners": [{"role": "owner", "email": "owner@example.com"}],
            "users": [{"role": "maintainer", "email": "user@example.com"}],
        }
    )

    assert share.get_user_role("user@example.com") == UserRole.maintainer


def test_get_user_role_falls_back_to_readonly_when_email_not_found():
    share = ShareProject.from_dict(
        {
            "owners": [{"role": "owner", "email": "owner@example.com"}],
            "users": [{"role": "contributor", "email": "user@example.com"}],
        }
    )

    assert share.get_user_role("missing@example.com") == UserRole.readonly


def test_get_user_role_falls_back_to_readonly_when_lists_are_none():
    share = ShareProject.from_dict({"owners": None, "users": None})

    assert share.get_user_role("any@example.com") == UserRole.readonly


def test_get_user_role_ignores_case_and_padding():
    """The email arrives either from the API or from a Basic token the user typed by hand; a
    difference in case must not cost them their rights."""
    share = ShareProject.from_dict(
        {"owners": [{"role": "owner", "email": "Owner@Example.com"}], "users": []}
    )

    assert share.get_user_role(" owner@example.COM ") == UserRole.owner


def test_get_user_role_is_readonly_when_the_current_user_is_unknown():
    """A blank email means we do not know who is logged in — it must never match an entry whose
    own email is missing, which would hand out rights to the wrong person."""
    share = ShareProject.from_dict(
        {"owners": [{"role": "owner", "email": ""}], "users": [{"role": "maintainer", "email": None}]}
    )

    assert share.get_user_role("") == UserRole.readonly
    assert share.get_user_role(None) == UserRole.readonly
