"""CIP-0005 local storage bound into type: imap. No network."""

from contextlib import contextmanager

import pytest

from lynguine.access.io import read_data
from lynguine.security.credentials import (
    CRYPTO_AVAILABLE,
    CredentialManager,
    CredentialNotFoundError,
    CredentialValidationError,
    EncryptedFileCredentialProvider,
    EnvironmentCredentialProvider,
    get_credential_manager,
    set_credential_manager,
)

import lynguine_imap

from .fake_imap import FakeIMAP, header_bytes

IMAP_SECRET = {
    "host": "imap.example.org",
    "user": "inbox@example.org",
    "password": "s3cret-pass",
}

EXAMPLE_YAML = {
    "type": "imap",
    "folder": "INBOX",
    "credential": "my_mail",
}


@contextmanager
def _isolated_manager(manager):
    previous = get_credential_manager()
    set_credential_manager(manager)
    try:
        yield manager
    finally:
        set_credential_manager(previous)


def _manager_with(provider):
    manager = CredentialManager(providers=[provider], enable_cache=False)
    manager.register_validator("imap", lynguine_imap.validate_imap)
    return manager


def _patch_ssl(monkeypatch, messages=None):
    seen = {}
    mailbox = messages if messages is not None else {"1": header_bytes(subject="From store")}

    class FakeSSL(FakeIMAP):
        def __init__(self, host, port, timeout=None):
            super().__init__(messages=mailbox)
            seen["host"] = host
            seen["port"] = port
            seen["client"] = self

    monkeypatch.setattr("lynguine_imap.reader.imaplib.IMAP4_SSL", FakeSSL)
    return seen


@pytest.mark.skipif(not CRYPTO_AVAILABLE, reason="cryptography not installed")
def test_encrypted_file_store_feeds_imap_example(tmp_path, monkeypatch):
    provider = EncryptedFileCredentialProvider(
        storage_path=str(tmp_path),
        master_key="test-master-key-imap",
    )
    manager = _manager_with(provider)
    seen = _patch_ssl(monkeypatch)

    with _isolated_manager(manager):
        manager.set_credential("my_mail", IMAP_SECRET, credential_type="imap")

        cred_files = list(tmp_path.glob("*.cred"))
        assert len(cred_files) == 1
        raw = cred_files[0].read_bytes()
        assert b"s3cret-pass" not in raw
        assert b"inbox@example.org" not in raw

        df, details = read_data(EXAMPLE_YAML)

    assert list(df["subject"]) == ["From store"]
    assert seen["host"] == "imap.example.org"
    assert seen["port"] == 993
    assert seen["client"].login_calls == [
        ("inbox@example.org", "s3cret-pass")
    ]
    assert seen["client"].selected == "INBOX"
    assert details["credential"] == "my_mail"
    assert "credential_value" not in details
    assert "password" not in details


@pytest.mark.skipif(not CRYPTO_AVAILABLE, reason="cryptography not installed")
def test_encrypted_file_rejects_incomplete_imap_secret(tmp_path):
    provider = EncryptedFileCredentialProvider(
        storage_path=str(tmp_path),
        master_key="test-master-key-imap",
    )
    manager = _manager_with(provider)
    with pytest.raises(CredentialValidationError, match="imap"):
        manager.set_credential(
            "my_mail",
            {"host": "imap.example.org", "user": "inbox@example.org"},
            credential_type="imap",
        )
    assert list(tmp_path.glob("*.cred")) == []


@pytest.mark.skipif(not CRYPTO_AVAILABLE, reason="cryptography not installed")
def test_encrypted_file_missing_key_fails_read(tmp_path, monkeypatch):
    provider = EncryptedFileCredentialProvider(
        storage_path=str(tmp_path),
        master_key="test-master-key-imap",
    )
    manager = _manager_with(provider)
    _patch_ssl(monkeypatch)
    with _isolated_manager(manager):
        with pytest.raises(CredentialNotFoundError, match="my_mail"):
            read_data(EXAMPLE_YAML)


def test_environment_store_feeds_imap_example(monkeypatch):
    provider = EnvironmentCredentialProvider(prefix="LYNGUINE_IMAP_TEST")
    manager = _manager_with(provider)
    seen = _patch_ssl(monkeypatch)

    with _isolated_manager(manager):
        manager.set_credential("my_mail", IMAP_SECRET, credential_type="imap")
        try:
            df, details = read_data(EXAMPLE_YAML)
        finally:
            provider.delete_credential("my_mail")

    assert list(df["subject"]) == ["From store"]
    assert seen["client"].login_calls == [
        ("inbox@example.org", "s3cret-pass")
    ]
    assert details["credential"] == "my_mail"
    assert "credential_value" not in details
