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
