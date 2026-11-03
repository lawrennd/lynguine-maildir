"""The package must declare type imap and type maildir on import."""

import pandas as pd
import pytest

from lynguine.access.io import write_data
from lynguine.access.io_types import ReadOnlyIOTypeError, get_io_type


def test_import_registers_imap():
    import lynguine_maildir  # noqa: F401

    spec = get_io_type("imap")
    assert spec is not None
    assert spec.name == "imap"
    assert spec.credential_type == "imap"
    assert spec.write is None
    assert spec.read is lynguine_maildir.read_imap


def test_read_rejects_missing_credential_value():
    import lynguine_maildir

    try:
        lynguine_maildir.read_imap({})
    except ValueError as exc:
        assert "credential_value" in str(exc)
    else:
        raise AssertionError("expected ValueError for missing credential_value")


def test_imap_write_is_read_only():
    import lynguine_maildir  # noqa: F401

    with pytest.raises(ReadOnlyIOTypeError, match="read-only"):
        write_data(pd.DataFrame(), {"type": "imap", "write": True})
