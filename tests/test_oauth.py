"""XOAUTH2 connect tests. MSAL and IMAP are faked. No network."""

import logging

import pytest

from lynguine_maildir.oauth import (
    ImapOAuthError,
    acquire_xoauth2_access_token,
    persist_rotated_refresh_token,
    xoauth2_sasl_payload,
)
from lynguine_maildir.reader import ImapAccessError, connect_from_credential, read_imap

from .fake_imap import FakeIMAP, header_bytes

XOAUTH2 = {
    "auth": "xoauth2",
    "host": "outlook.office365.com",
    "user": "user@example.com",
    "client_id": "client-id",
    "tenant": "organizations",
    "refresh_token": "refresh-secret",
}

ACCESS = "access-secret-token"


def _xoauth_details(**extra):
    details = {"credential": "office_mail", "credential_value": dict(XOAUTH2)}
    details.update(extra)
    return details


def _patch_xoauth_ssl(monkeypatch, messages=None):
    seen = {}
    mailbox = messages if messages is not None else {
        "1": header_bytes(subject="From oauth")
    }

    class FakeSSL(FakeIMAP):
        def __init__(self, host, port, timeout=None):
            super().__init__(messages=mailbox)
            seen["host"] = host
            seen["port"] = port
            seen["client"] = self

        def login(self, *args, **kwargs):
            raise AssertionError("login() must not be called for XOAUTH2")

    monkeypatch.setattr("lynguine_maildir.reader.imaplib.IMAP4_SSL", FakeSSL)
    return seen


def test_xoauth2_sasl_payload_is_not_pre_base64():
    payload = xoauth2_sasl_payload("user@example.com", ACCESS)
    assert payload.startswith(b"user=user@example.com")
    assert b"auth=Bearer access-secret-token" in payload
    assert not payload.startswith(b"dXNlcj0")  # base64 of "user="


def test_xoauth2_authenticate_not_login(monkeypatch):
    seen = _patch_xoauth_ssl(monkeypatch)
    monkeypatch.setattr(
        "lynguine_maildir.reader.acquire_xoauth2_access_token",
        lambda cred: (ACCESS, None),
    )
    client = connect_from_credential(dict(XOAUTH2))
    assert seen["host"] == "outlook.office365.com"
    assert seen["port"] == 993
    assert seen["client"].login_calls == []
    assert seen["client"].authenticate_calls[0][0] == "XOAUTH2"
    assert ACCESS.encode() in seen["client"].authenticate_calls[0][1]
    client.logout()


def test_read_imap_xoauth2_returns_columns(monkeypatch):
    seen = _patch_xoauth_ssl(monkeypatch)
    monkeypatch.setattr(
        "lynguine_maildir.reader.acquire_xoauth2_access_token",
        lambda cred: (ACCESS, None),
    )
    df = read_imap(_xoauth_details())
    assert list(df["subject"]) == ["From oauth"]
    assert seen["client"].authenticate_calls[0][0] == "XOAUTH2"
    assert seen["client"].login_calls == []


def test_access_token_not_logged_or_raised(monkeypatch, caplog):
    import imaplib

    caplog.set_level(logging.DEBUG)

    class FakeSSL(FakeIMAP):
        def __init__(self, host, port, timeout=None):
            super().__init__()

        def login(self, *args, **kwargs):
            raise AssertionError("login() must not be called for XOAUTH2")

        def authenticate(self, mechanism, authobject):
            authobject(b"")
            raise imaplib.IMAP4.error("NO AUTHENTICATE failed")

    monkeypatch.setattr("lynguine_maildir.reader.imaplib.IMAP4_SSL", FakeSSL)
    monkeypatch.setattr(
        "lynguine_maildir.reader.acquire_xoauth2_access_token",
        lambda cred: (ACCESS, None),
    )
    with pytest.raises(ImapAccessError, match="user@example.com") as excinfo:
        connect_from_credential(dict(XOAUTH2))
    text = str(excinfo.value)
    assert ACCESS not in text
    assert "refresh-secret" not in text
    assert ACCESS not in caplog.text
    assert "refresh-secret" not in caplog.text


def test_missing_msal_is_oauth_error_not_imap(monkeypatch):
    import sys

    monkeypatch.delitem(sys.modules, "msal", raising=False)
    monkeypatch.setitem(sys.modules, "msal", None)
    with pytest.raises(ImapOAuthError, match="lynguine-maildir\\[oauth\\]") as excinfo:
        acquire_xoauth2_access_token(dict(XOAUTH2))
    assert not isinstance(excinfo.value, ImapAccessError)


def test_refresh_stub_used_for_bearer(monkeypatch):
    seen = {}

    class App:
        def acquire_token_by_refresh_token(self, refresh_token, scopes):
            seen["refresh_token"] = refresh_token
            seen["scopes"] = scopes
            return {"access_token": ACCESS}

    monkeypatch.setattr(
        "lynguine_maildir.oauth._public_client",
        lambda client_id, tenant: App(),
    )
    token, new_refresh = acquire_xoauth2_access_token(dict(XOAUTH2))
    assert token == ACCESS
    assert new_refresh is None
    assert seen["refresh_token"] == "refresh-secret"
    assert "https://outlook.office.com/IMAP.AccessAsUser.All" in seen["scopes"]
    assert "offline_access" in seen["scopes"]


def test_rotated_refresh_token_writeback(monkeypatch):
    stored = {}

    def fake_set(key, value, credential_type=None):
        stored["key"] = key
        stored["value"] = value
        stored["type"] = credential_type

    monkeypatch.setattr("lynguine.security.set_credential", fake_set)
    cred = dict(XOAUTH2)
    persist_rotated_refresh_token(
        {"credential": "office_mail"}, cred, "new-refresh"
    )
    assert cred["refresh_token"] == "new-refresh"
    assert stored["key"] == "office_mail"
    assert stored["type"] == "imap"
    assert stored["value"]["refresh_token"] == "new-refresh"
    assert stored["value"]["auth"] == "xoauth2"
    assert "password" not in stored["value"]


def test_rotated_refresh_warns_once_when_store_missing(monkeypatch):
    def boom(*args, **kwargs):
        raise RuntimeError("no persist")

    monkeypatch.setattr("lynguine.security.set_credential", boom)
    monkeypatch.setattr("lynguine_maildir.oauth._WRITEBACK_WARNED", False)
    cred = dict(XOAUTH2)
    with pytest.warns(UserWarning, match="could not be stored"):
        persist_rotated_refresh_token(
            {"credential": "office_mail"}, cred, "new-refresh"
        )
    persist_rotated_refresh_token(
        {"credential": "office_mail"}, cred, "newer-refresh"
    )
    assert cred["refresh_token"] == "newer-refresh"


def test_xoauth2_persists_rotated_refresh(monkeypatch):
    seen = {}
    _patch_xoauth_ssl(monkeypatch)
    monkeypatch.setattr(
        "lynguine_maildir.reader.acquire_xoauth2_access_token",
        lambda cred: (ACCESS, "rotated-rt"),
    )
    monkeypatch.setattr(
        "lynguine_maildir.reader.persist_rotated_refresh_token",
        lambda details, cred, new: seen.update(
            refresh=new,
            key=(details or {}).get("credential"),
        ),
    )
    connect_from_credential(
        dict(XOAUTH2), details={"credential": "office_mail"}
    )
    assert seen["refresh"] == "rotated-rt"
    assert seen["key"] == "office_mail"


def test_login_path_still_uses_login(monkeypatch):
    seen = {}

    class FakeSSL(FakeIMAP):
        def __init__(self, host, port, timeout=None):
            super().__init__()
            seen["client"] = self

        def authenticate(self, *args, **kwargs):
            raise AssertionError("authenticate() must not be called for LOGIN")

    monkeypatch.setattr("lynguine_maildir.reader.imaplib.IMAP4_SSL", FakeSSL)
    client = connect_from_credential(
        {"auth": "login", "host": "imap.example.org", "user": "u", "password": "p"}
    )
    assert seen["client"].login_calls == [("u", "p")]
    assert seen["client"].authenticate_calls == []
    client.logout()


def test_read_rejects_unknown_auth():
    with pytest.raises(ValueError, match="unknown auth"):
        read_imap(
            {
                "credential_value": {
                    "auth": "plain",
                    "host": "h",
                    "user": "u",
                    "password": "p",
                }
            }
        )
