from lynguine_maildir.credentials import validate_imap

XOAUTH2 = {
    "auth": "xoauth2",
    "host": "outlook.office365.com",
    "user": "user@example.com",
    "client_id": "client-id",
    "tenant": "organizations",
    "refresh_token": "rt",
}


def test_validate_imap_requires_host_user_password():
    assert validate_imap(
        {"host": "imap.example.org", "user": "u", "password": "p"}
    )
    assert validate_imap(
        {"value": {"host": "imap.example.org", "user": "u", "password": "p"}}
    )
    assert validate_imap(
        {
            "auth": "login",
            "host": "imap.example.org",
            "user": "u",
            "password": "p",
        }
    )


def test_validate_imap_rejects_blank_and_non_mapping():
    assert not validate_imap({"host": "h", "user": "u", "password": " "})
    assert not validate_imap("imap.example.org")
    assert not validate_imap({"host": "h", "user": "u"})


def test_validate_imap_xoauth2_form():
    assert validate_imap(XOAUTH2)
    assert validate_imap({"value": dict(XOAUTH2)})


def test_validate_imap_rejects_mixed_fields():
    mixed_login = {
        "host": "h",
        "user": "u",
        "password": "p",
        "client_id": "cid",
    }
    mixed_xoauth = dict(XOAUTH2)
    mixed_xoauth["password"] = "p"
    assert not validate_imap(mixed_login)
    assert not validate_imap(mixed_xoauth)


def test_validate_imap_rejects_unknown_auth():
    assert not validate_imap(
        {"auth": "plain", "host": "h", "user": "u", "password": "p"}
    )
    assert not validate_imap({**XOAUTH2, "auth": "XOAUTH2"})
