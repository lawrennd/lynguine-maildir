"""Maildir and IMAP subjects as lynguine IO types.

This is inbound mail for *access*, not referia's outbound ``type: email``
drafts. Importing this module registers ``type: maildir`` (local replica,
no credential) and ``type: imap`` (live mailbox; lynguine binds
``credential_value``).
"""

from __future__ import annotations

from lynguine.access.io import register_io_type
from lynguine.security.credentials import get_credential_manager

from .credentials import validate_imap
from .maildir import read_maildir
from .oauth import ImapOAuthError
from .reader import ImapAccessError, read_imap

get_credential_manager().register_validator("imap", validate_imap)

register_io_type("maildir", read=read_maildir)
register_io_type(
    "imap",
    read=read_imap,
    credential_type="imap",
)


def register():
    """Entry-point hook. Import already registers both types."""
    from lynguine.access.io_types import get_io_type

    return get_io_type("maildir")


__all__ = [
    "ImapAccessError",
    "ImapOAuthError",
    "read_imap",
    "read_maildir",
    "register",
    "validate_imap",
]
