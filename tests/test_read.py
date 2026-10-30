"""IMAP reader tests use a fake client. No network."""

from email.header import Header

import pandas as pd
import pytest

from lynguine_imap.reader import (
    COLUMNS,
    HEADER_FETCH,
    ImapAccessError,
    connect_imap,
    read_imap,
)

from .fake_imap import FakeIMAP, header_bytes as _header_bytes


def _cred(**extra):
    details = {
        "credential_value": {
            "host": "imap.example.org",
            "user": "inbox@example.org",
            "password": "secret",
        }
    }
    details.update(extra)
    return details


def test_read_empty_folder_has_columns():
    client = FakeIMAP()

    def connect(*args, **kwargs):
        return client

    df = read_imap(_cred(), connect=connect)
    assert list(df.columns) == COLUMNS
    assert df.empty
    assert client.selected == "INBOX"
    assert client.readonly is True
    assert client.logged_out is True


def test_read_headers_one_row_per_uid():
    client = FakeIMAP(
        {
            "11": _header_bytes(subject="One", message_id="<one@ex>"),
            "12": _header_bytes(subject="Two", from_addr="b@ex", message_id="<two@ex>"),
        }
    )

    df = read_imap(_cred(folder="Reviews"), connect=lambda *a, **k: client)
    assert list(df["uid"]) == ["11", "12"]
    assert list(df["subject"]) == ["One", "Two"]
    assert list(df["from"]) == ["a@example.org", "b@ex"]
    assert list(df["message_id"]) == ["<one@ex>", "<two@ex>"]
    assert client.selected == "Reviews"
    assert all("BODY.PEEK" in spec for spec in client.fetch_specs)
    assert all(spec == HEADER_FETCH for spec in client.fetch_specs)


def test_mailbox_alias_selects_same_folder():
    client = FakeIMAP()
    read_imap(_cred(mailbox="Sent"), connect=lambda *a, **k: client)
    assert client.selected == "Sent"


def test_folder_and_mailbox_must_match():
    with pytest.raises(ValueError, match="must match"):
        read_imap(
            _cred(folder="INBOX", mailbox="Sent"),
            connect=lambda *a, **k: FakeIMAP(),
        )


def test_limit_keeps_highest_uids():
    client = FakeIMAP(
        {
            "1": _header_bytes(subject="old", message_id="<old@ex>"),
            "2": _header_bytes(subject="mid", message_id="<mid@ex>"),
            "3": _header_bytes(subject="new", message_id="<new@ex>"),
        }
    )
    df = read_imap(_cred(limit=2), connect=lambda *a, **k: client)
    assert list(df["uid"]) == ["2", "3"]
    assert list(df["subject"]) == ["mid", "new"]


def test_mime_encoded_subject():
    encoded = Header("Café", "utf-8").encode()
    client = FakeIMAP({"7": _header_bytes(subject=encoded, message_id="<cafe@ex>")})
    df = read_imap(_cred(), connect=lambda *a, **k: client)
    assert df.loc[0, "subject"] == "Café"


def test_missing_folder_names_the_folder():
    client = FakeIMAP(select_status="NO")
    with pytest.raises(ImapAccessError, match="Missing"):
        read_imap(_cred(folder="Missing"), connect=lambda *a, **k: client)


def test_read_rejects_missing_credential_value():
    with pytest.raises(ValueError, match="credential_value"):
        read_imap({})


def test_read_rejects_incomplete_credential():
    with pytest.raises(ValueError, match="password"):
        read_imap(
            {"credential_value": {"host": "h", "user": "u", "password": "  "}}
        )


def test_limit_must_be_positive_int():
    with pytest.raises(ValueError, match="limit"):
        read_imap(_cred(limit=0), connect=lambda *a, **k: FakeIMAP())


def test_connect_uses_ssl_and_default_port(monkeypatch):
    seen = {}

    class FakeSSL:
        def __init__(self, host, port, timeout=None):
            seen["host"] = host
            seen["port"] = port
            seen["timeout"] = timeout
            seen["cls"] = "ssl"

        def login(self, user, password):
            seen["user"] = user
            seen["password"] = password
            return "OK", [b"ok"]

        def logout(self):
            return "BYE", []

    monkeypatch.setattr("lynguine_imap.reader.imaplib.IMAP4_SSL", FakeSSL)
    client = connect_imap("imap.example.org", "u", "p")
    assert seen["host"] == "imap.example.org"
    assert seen["port"] == 993
    assert seen["cls"] == "ssl"
    assert seen["user"] == "u"
    client.logout()


def test_plaintext_uses_port_143(monkeypatch):
    seen = {}

    class FakePlain:
        def __init__(self, host, port, timeout=None):
            seen["port"] = port

        def login(self, user, password):
            return "OK", [b"ok"]

        def logout(self):
            return "BYE", []

    monkeypatch.setattr("lynguine_imap.reader.imaplib.IMAP4", FakePlain)
    connect_imap("imap.example.org", "u", "p", ssl=False)
    assert seen["port"] == 143


def test_read_passes_ssl_and_port_to_connect():
    seen = {}

    def connect(host, user, password, *, port, ssl):
        seen["host"] = host
        seen["user"] = user
        seen["port"] = port
        seen["ssl"] = ssl
        return FakeIMAP()

    read_imap(_cred(ssl=False, port=1143), connect=connect)
    assert seen == {
        "host": "imap.example.org",
        "user": "inbox@example.org",
        "port": 1143,
        "ssl": False,
    }


def test_read_returns_dataframe_type():
    df = read_imap(_cred(), connect=lambda *a, **k: FakeIMAP())
    assert isinstance(df, pd.DataFrame)
