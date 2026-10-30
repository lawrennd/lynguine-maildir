"""IMAP subjects as a lynguine IO type.

This is inbound mail for *access*, not referia's outbound ``type: email``
drafts. Importing this module registers ``type: imap`` and the ``imap``
credential validator. lynguine fetches the secret; this package reads
``credential_value``.
"""

from __future__ import annotations

from lynguine.access.io import register_io_type
from lynguine.security.credentials import get_credential_manager

from .credentials import validate_imap
from .reader import ImapAccessError, read_imap

get_credential_manager().register_validator("imap", validate_imap)

register_io_type(
    "imap",
    read=read_imap,
    credential_type="imap",
)


def register():
    """Entry-point hook. Import already registers ``type: imap``."""
    from lynguine.access.io_types import get_io_type

    return get_io_type("imap")


__all__ = [
    "ImapAccessError",
    "read_imap",
    "register",
    "validate_imap",
]
