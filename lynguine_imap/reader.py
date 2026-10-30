"""Read IMAP message metadata into a DataFrame.

The live mailbox is the store. This module fetches headers only
(``BODY.PEEK``) and does not mark messages seen.
"""

from __future__ import annotations

import imaplib
from email import message_from_bytes
from email.header import decode_header, make_header
from email.message import Message
from typing import Callable

import pandas as pd

COLUMNS = ["uid", "message_id", "subject", "from", "date"]
HEADER_FETCH = "(BODY.PEEK[HEADER.FIELDS (SUBJECT FROM DATE MESSAGE-ID)])"


class ImapAccessError(RuntimeError):
    """IMAP server or protocol failure (not a YAML contract error)."""


def connect_imap(
    host: str,
    user: str,
    password: str,
    *,
    port: int | None = None,
    ssl: bool = True,
    timeout: float = 30.0,
):
    """Open an IMAP session and log in. Caller must ``logout()``."""
    if port is None:
        port = 993 if ssl else 143
    factory = imaplib.IMAP4_SSL if ssl else imaplib.IMAP4
    client = factory(host, port, timeout=timeout)
    try:
        status, _ = client.login(user, password)
    except imaplib.IMAP4.error as exc:
        _close_quietly(client)
        raise ImapAccessError(
            f"IMAP login failed for user {user!r} on {host!r}"
        ) from exc
    except Exception:
        _close_quietly(client)
        raise
    if status != "OK":
        _close_quietly(client)
        raise ImapAccessError(
            f"IMAP login failed for user {user!r} on {host!r}"
        )
    return client


def read_imap(
    details: dict,
    *,
    connect: Callable[..., object] = connect_imap,
) -> pd.DataFrame:
    """Read mailbox subjects.

    Required YAML:

    * ``credential:`` — CIP-0005 key (lynguine binds ``credential_value``)
    * ``folder:`` — mailbox folder, default ``INBOX`` (``mailbox:`` is an alias)

    Optional: ``limit`` (positive int), ``ssl`` (default true), ``port``.
    """
    cred = _credential(details)
    folder = _folder(details)
    limit = _limit(details)
    ssl = _ssl(details)
    port = _port(details, ssl=ssl)
    client = connect(
        cred["host"],
        cred["user"],
        cred["password"],
        port=port,
        ssl=ssl,
    )
    try:
        rows = fetch_message_rows(client, folder, limit)
    finally:
        _close_quietly(client)
    return pd.DataFrame(rows, columns=COLUMNS)


def fetch_message_rows(client, folder: str, limit: int | None) -> list[dict]:
    """SELECT *folder* read-only and return header rows for UIDs."""
    status, _ = client.select(folder, readonly=True)
    if status != "OK":
        raise ImapAccessError(f"Could not select IMAP folder {folder!r}")
    status, data = client.uid("SEARCH", None, "ALL")
    if status != "OK":
        raise ImapAccessError(f"UID SEARCH failed in folder {folder!r}")
    uids = _parse_uids(data)
    if limit is not None:
        uids = uids[-limit:]
    rows = []
    for uid in uids:
        status, fetched = client.uid("FETCH", uid, HEADER_FETCH)
        if status != "OK":
            raise ImapAccessError(
                f"UID FETCH failed for uid {_uid_text(uid)} in folder {folder!r}"
            )
        payload = _extract_fetch_payload(fetched)
        rows.append(_row_from_headers(uid, payload))
    return rows


def _credential(details: dict) -> dict[str, str]:
    cred = details.get("credential_value")
    if not isinstance(cred, dict):
        raise ValueError("IMAP read expected credential_value mapping from lynguine")
    missing = [
        key
        for key in ("host", "user", "password")
        if not (isinstance(cred.get(key), str) and cred[key].strip())
    ]
    if missing:
        raise ValueError(
            "IMAP credential_value missing " + ", ".join(missing)
        )
    return {key: cred[key].strip() for key in ("host", "user", "password")}


def _folder(details: dict) -> str:
    folder = details.get("folder")
    mailbox = details.get("mailbox")
    if folder is not None and mailbox is not None and folder != mailbox:
        raise ValueError(
            'Type "imap" has both folder and mailbox; they must match'
        )
    name = folder if folder is not None else mailbox
    if name is None:
        return "INBOX"
    if not isinstance(name, str) or not name.strip():
        raise ValueError('Type "imap" requires folder: <mailbox name>')
    return name.strip()


def _limit(details: dict) -> int | None:
    if "limit" not in details or details["limit"] is None:
        return None
    limit = details["limit"]
    if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
        raise ValueError('Type "imap" limit: must be a positive integer')
    return limit


def _ssl(details: dict) -> bool:
    if "ssl" not in details or details["ssl"] is None:
        return True
    ssl = details["ssl"]
    if not isinstance(ssl, bool):
        raise ValueError('Type "imap" ssl: must be true or false')
    return ssl


def _port(details: dict, *, ssl: bool) -> int:
    if "port" not in details or details["port"] is None:
        return 993 if ssl else 143
    port = details["port"]
    if isinstance(port, bool) or not isinstance(port, int):
        raise ValueError('Type "imap" port: must be an integer 1-65535')
    if not 1 <= port <= 65535:
        raise ValueError('Type "imap" port: must be an integer 1-65535')
    return port


def _parse_uids(data) -> list:
    if not data or data[0] in (None, b"", ""):
        return []
    raw = data[0]
    if isinstance(raw, str):
        raw = raw.encode("ascii", "strict")
    return raw.split()


def _extract_fetch_payload(data) -> bytes:
    if not data:
        raise ImapAccessError("empty FETCH response")
    for part in data:
        if isinstance(part, tuple) and len(part) >= 2:
            payload = part[1]
            if isinstance(payload, (bytes, bytearray)):
                return bytes(payload)
    raise ImapAccessError("FETCH response had no header payload")


def _row_from_headers(uid, payload: bytes) -> dict[str, str]:
    message = message_from_bytes(payload)
    return {
        "uid": _uid_text(uid),
        "message_id": _header(message, "Message-ID"),
        "subject": _header(message, "Subject"),
        "from": _header(message, "From"),
        "date": _header(message, "Date"),
    }


def _header(message: Message, name: str) -> str:
    raw = message.get(name)
    if not raw:
        return ""
    try:
        return str(make_header(decode_header(raw)))
    except (LookupError, UnicodeDecodeError, ValueError):
        return raw


def _uid_text(uid) -> str:
    if isinstance(uid, bytes):
        return uid.decode("ascii")
    return str(uid)


def _close_quietly(client) -> None:
    logout = getattr(client, "logout", None)
    if not callable(logout):
        return
    try:
        logout()
    except Exception:
        pass
