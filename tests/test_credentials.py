from lynguine_imap.credentials import validate_imap


def test_validate_imap_requires_host_user_password():
    assert validate_imap(
        {"host": "imap.example.org", "user": "u", "password": "p"}
    )
    assert validate_imap(
        {"value": {"host": "imap.example.org", "user": "u", "password": "p"}}
    )


def test_validate_imap_rejects_blank_and_non_mapping():
    assert not validate_imap({"host": "h", "user": "u", "password": " "})
    assert not validate_imap("imap.example.org")
    assert not validate_imap({"host": "h", "user": "u"})
