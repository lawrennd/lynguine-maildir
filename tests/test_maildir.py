"""Maildir reader tests use a fixture tree. No network."""

from email.header import Header
from pathlib import Path

import pandas as pd
import pytest

from lynguine.access.io import read_data, write_data
from lynguine.access.io_types import ReadOnlyIOTypeError, get_io_type

from lynguine_maildir.maildir import read_maildir
from lynguine_maildir.reader import COLUMNS


def _write_message(path: Path, *, subject, from_addr, date, message_id):
    path.write_bytes(
        (
            f"Subject: {subject}\r\n"
            f"From: {from_addr}\r\n"
            f"Date: {date}\r\n"
            f"Message-ID: {message_id}\r\n"
            "\r\n"
            "Body is not a column.\r\n"
        ).encode("utf-8")
    )


def _maildir(root: Path):
    (root / "cur").mkdir(parents=True)
    (root / "new").mkdir()
    (root / "tmp").mkdir()
    return root


def test_import_registers_maildir():
    import lynguine_maildir

    spec = get_io_type("maildir")
    assert spec is not None
    assert spec.name == "maildir"
    assert spec.credential_type is None
    assert spec.write is None
    assert spec.read is lynguine_maildir.read_maildir


def test_maildir_write_is_read_only():
    import lynguine_maildir  # noqa: F401

    with pytest.raises(ReadOnlyIOTypeError, match="read-only"):
        write_data(pd.DataFrame(), {"type": "maildir", "write": True})


def test_cur_and_new_two_rows_tmp_ignored(tmp_path):
    root = _maildir(tmp_path / "INBOX")
    _write_message(
        root / "cur" / "111.hostname:2,S",
        subject="Seen",
        from_addr="a@example.org",
        date="Fri, 30 Oct 2026 12:00:00 +0000",
        message_id="<seen@ex>",
    )
    new_file = root / "new" / "222.hostname"
    _write_message(
        new_file,
        subject="Unseen",
        from_addr="b@example.org",
        date="Fri, 30 Oct 2026 13:00:00 +0000",
        message_id="<new@ex>",
    )
    (root / "tmp" / "333.hostname").write_text("ignored\n")

    df = read_maildir({"path": str(root)})
    assert list(df.columns)[:5] == COLUMNS
    assert "body" in df.columns
    assert "path" in df.columns
    assert set(df["uid"]) == {"111.hostname", "222.hostname"}
    assert set(df["subject"]) == {"Seen", "Unseen"}
    assert new_file.exists()
    assert not (root / "cur" / "222.hostname").exists()
    assert not (root / "cur" / "222.hostname:2,").exists()


def test_empty_maildir_has_columns(tmp_path):
    root = _maildir(tmp_path / "INBOX")
    df = read_maildir({"path": str(root)})
    assert list(df.columns)[:5] == COLUMNS
    assert "body" in df.columns
    assert df.empty


def test_mime_encoded_subject(tmp_path):
    root = _maildir(tmp_path / "INBOX")
    encoded = Header("Café", "utf-8").encode()
    _write_message(
        root / "cur" / "7.hostname:2,S",
        subject=encoded,
        from_addr="a@example.org",
        date="Fri, 30 Oct 2026 12:00:00 +0000",
        message_id="<cafe@ex>",
    )
    df = read_maildir({"path": str(root)})
    assert df.loc[0, "subject"] == "Café"


def test_folder_alias(tmp_path):
    root = _maildir(tmp_path / "INBOX")
    _write_message(
        root / "cur" / "1.hostname:2,S",
        subject="One",
        from_addr="a@example.org",
        date="Fri, 30 Oct 2026 12:00:00 +0000",
        message_id="<one@ex>",
    )
    df = read_maildir({"folder": str(root)})
    assert list(df["subject"]) == ["One"]


def test_path_and_folder_must_match(tmp_path):
    with pytest.raises(ValueError, match="must match"):
        read_maildir({"path": str(tmp_path / "a"), "folder": str(tmp_path / "b")})


def test_tilde_expands(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    root = _maildir(tmp_path / "Mail" / "INBOX")
    _write_message(
        root / "cur" / "1.hostname:2,S",
        subject="Home",
        from_addr="a@example.org",
        date="Fri, 30 Oct 2026 12:00:00 +0000",
        message_id="<home@ex>",
    )
    df = read_maildir({"path": "~/Mail/INBOX"})
    assert list(df["subject"]) == ["Home"]


def test_non_maildir_names_the_path(tmp_path):
    other = tmp_path / "not-mail"
    other.mkdir()
    with pytest.raises(ValueError, match="not-mail") as excinfo:
        read_maildir({"path": str(other)})
    assert "Maildir" in str(excinfo.value)


def test_missing_path():
    with pytest.raises(ValueError, match="path"):
        read_maildir({})


def test_rejects_credential():
    with pytest.raises(ValueError, match="credential"):
        read_maildir({"path": "/tmp", "credential": "secret"})


def test_read_data_without_credential(tmp_path):
    import lynguine_maildir  # noqa: F401

    root = _maildir(tmp_path / "INBOX")
    _write_message(
        root / "cur" / "1.hostname:2,S",
        subject="Via read_data",
        from_addr="a@example.org",
        date="Fri, 30 Oct 2026 12:00:00 +0000",
        message_id="<rd@ex>",
    )
    df, details = read_data({"type": "maildir", "path": str(root)})
    assert list(df["subject"]) == ["Via read_data"]
    assert "credential_value" not in details


def test_limit_keeps_newest_mtime(tmp_path):
    root = _maildir(tmp_path / "INBOX")
    older = root / "cur" / "1.hostname:2,S"
    newer = root / "cur" / "2.hostname:2,S"
    _write_message(
        older,
        subject="old",
        from_addr="a@example.org",
        date="Fri, 30 Oct 2026 12:00:00 +0000",
        message_id="<old@ex>",
    )
    _write_message(
        newer,
        subject="new",
        from_addr="a@example.org",
        date="Fri, 30 Oct 2026 13:00:00 +0000",
        message_id="<new@ex>",
    )
    import os
    os.utime(older, (1_000_000, 1_000_000))
    os.utime(newer, (2_000_000, 2_000_000))
    df = read_maildir({"path": str(root), "limit": 1})
    assert list(df["subject"]) == ["new"]
