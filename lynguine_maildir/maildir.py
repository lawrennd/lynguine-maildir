"""Read Maildir message metadata into a DataFrame.

The directory on disk is the store. This module parses headers only and
does not move mail from ``new/`` to ``cur/``.
"""

from __future__ import annotations

from email.header import decode_header, make_header
from email.message import Message
from email.parser import BytesHeaderParser
from pathlib import Path

import pandas as pd

from .reader import COLUMNS

_HEADER_PARSER = BytesHeaderParser()


def read_maildir(details: dict) -> pd.DataFrame:
    """Read one Maildir folder.

    Required YAML:

    * ``path:`` — directory containing ``cur/`` and/or ``new/``
      (``folder:`` is an alias)

    Optional: ``limit`` (newest files by mtime). ``credential:`` is not
    accepted.
    """
    if details.get("credential") is not None:
        raise ValueError('Type "maildir" does not take credential:')
    path = _path(details)
    limit = _limit(details)
    files = _message_files(path)
    files.sort(key=lambda item: item.stat().st_mtime)
    if limit is not None:
        files = files[-limit:]
    rows = [_row_from_file(item) for item in files]
    return pd.DataFrame(rows, columns=COLUMNS)


def _path(details: dict) -> Path:
    path = details.get("path")
    folder = details.get("folder")
    if path is not None and folder is not None and path != folder:
        raise ValueError(
            'Type "maildir" has both path and folder; they must match'
        )
    name = path if path is not None else folder
    if name is None:
        raise ValueError('Type "maildir" requires path: <Maildir directory>')
    if not isinstance(name, str) or not name.strip():
        raise ValueError('Type "maildir" requires path: <Maildir directory>')
    expanded = Path(name.strip()).expanduser()
    if not expanded.is_dir():
        raise ValueError(
            f'Type "maildir" path is not a directory: {expanded}'
        )
    cur = expanded / "cur"
    new = expanded / "new"
    if not cur.is_dir() and not new.is_dir():
        raise ValueError(
            f'Type "maildir" path is not a Maildir (no cur/ or new/): {expanded}'
        )
    return expanded


def _limit(details: dict) -> int | None:
    if "limit" not in details or details["limit"] is None:
        return None
    limit = details["limit"]
    if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
        raise ValueError('Type "maildir" limit: must be a positive integer')
    return limit


def _message_files(root: Path) -> list[Path]:
    files = []
    for subdir in ("cur", "new"):
        folder = root / subdir
        if not folder.is_dir():
            continue
        for item in folder.iterdir():
            if item.is_file() and not item.name.startswith("."):
                files.append(item)
    return files


def _row_from_file(path: Path) -> dict[str, str]:
    with path.open("rb") as handle:
        message = _HEADER_PARSER.parse(handle)
    return {
        "uid": _maildir_uid(path.name),
        "message_id": _header(message, "Message-ID"),
        "subject": _header(message, "Subject"),
        "from": _header(message, "From"),
        "date": _header(message, "Date"),
    }


def _maildir_uid(filename: str) -> str:
    if ":2," in filename:
        return filename.split(":2,", 1)[0]
    if ":" in filename:
        return filename.split(":", 1)[0]
    return filename


def _header(message: Message, name: str) -> str:
    raw = message.get(name)
    if not raw:
        return ""
    try:
        return str(make_header(decode_header(raw)))
    except (LookupError, UnicodeDecodeError, ValueError):
        return raw
