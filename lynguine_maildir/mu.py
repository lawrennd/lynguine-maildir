"""Read a mu find query into a DataFrame.

The mu database is the store. This module runs ``mu find`` and does not
index, init, or alter Maildir files.
"""

from __future__ import annotations

import datetime as dt
import json
import subprocess
from pathlib import Path

import pandas as pd

from .body import body_images_option, listing_body
from .maildir import _maildir_uid
from .reader import COLUMNS

_EXTRA = ["path", "maildir", "body"]
_COLUMNS = COLUMNS + _EXTRA
_STDERR_LIMIT = 500
_NO_MATCH_EXIT = 2


def read_mu(details: dict) -> pd.DataFrame:
    """Read message metadata matching a mu query.

    Required YAML: ``query:``. Optional: ``limit``, ``muhome``,
    ``binary``, ``body_images`` (``omit`` or ``url``). ``credential:``,
    ``path:``, and ``folder:`` are not accepted.
    """
    if details.get("credential") is not None:
        raise ValueError('Type "mu" does not take credential:')
    if details.get("path") is not None or details.get("folder") is not None:
        raise ValueError(
            'Type "mu" does not take path: or folder: '
            "(put a maildir: constraint in query:)"
        )
    query = _query(details)
    argv = _argv(details, query)
    completed = _run(argv, binary=argv[0])
    images = body_images_option(details, type_name="mu")
    rows = [_row_from_hit(hit, images=images) for hit in _hits(completed)]
    return pd.DataFrame(rows, columns=_COLUMNS)


def _query(details: dict) -> str:
    query = details.get("query")
    if not isinstance(query, str) or not query.strip():
        raise ValueError('Type "mu" requires query: <mu-query expression>')
    return query.strip()


def _limit(details: dict) -> int | None:
    if "limit" not in details or details["limit"] is None:
        return None
    limit = details["limit"]
    if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
        raise ValueError('Type "mu" limit: must be a positive integer')
    return limit


def _argv(details: dict, query: str) -> list[str]:
    binary = details.get("binary", "mu")
    if not isinstance(binary, str) or not binary.strip():
        raise ValueError('Type "mu" binary: must be a non-empty string')
    binary = str(Path(binary.strip()).expanduser())
    argv = [
        binary,
        "find",
        "--format=json2",
        "--nocolor",
        "--sortfield=date",
        "--reverse",
    ]
    limit = _limit(details)
    if limit is not None:
        argv.append(f"--maxnum={limit}")
    muhome = details.get("muhome")
    if muhome is not None:
        if not isinstance(muhome, str) or not muhome.strip():
            raise ValueError('Type "mu" muhome: must be a non-empty string')
        argv.append(f"--muhome={str(Path(muhome.strip()).expanduser())}")
    argv.extend(["--", query])
    return argv


def _run(argv: list[str], *, binary: str) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(
            argv,
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError as exc:
        raise ValueError(
            f'Type "mu" requires the mu binary on PATH (or binary:); '
            f"looked for {binary!r}"
        ) from exc


def _hits(completed: subprocess.CompletedProcess) -> list[dict]:
    if completed.returncode == _NO_MATCH_EXIT:
        return []
    stderr = (completed.stderr or "").strip()
    if completed.returncode != 0:
        raise ValueError(
            'Type "mu" mu find failed'
            + (f": {_trim(stderr)}" if stderr else f" (exit {completed.returncode})")
        )
    text = (completed.stdout or "").strip()
    if not text or text.startswith("no matches"):
        return []
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f'Type "mu" mu find returned invalid JSON: {_trim(text)}'
        ) from exc
    if payload is None:
        return []
    if isinstance(payload, dict):
        return [payload]
    if not isinstance(payload, list):
        raise ValueError(
            f'Type "mu" mu find JSON must be an array, got {type(payload).__name__}'
        )
    return [item for item in payload if isinstance(item, dict)]


def _row_from_hit(hit: dict, *, images: str = "omit") -> dict[str, str]:
    path = str(hit.get("path") or "")
    return {
        "uid": _maildir_uid(Path(path).name) if path else "",
        "message_id": str(hit.get("message-id") or ""),
        "subject": str(hit.get("subject") or ""),
        "from": _from_field(hit.get("from")),
        "date": _date_field(hit),
        "path": path,
        "maildir": str(hit.get("maildir") or ""),
        "body": listing_body(path, images=images),
    }


def _from_field(value) -> str:
    if not value:
        return ""
    if isinstance(value, str):
        return value
    if not isinstance(value, list) or not value:
        return ""
    first = value[0]
    if not isinstance(first, dict):
        return str(first)
    name = str(first.get("name") or "").strip()
    email = str(first.get("email") or "").strip()
    if name and email:
        return f"{name} <{email}>"
    return name or email


def _date_field(hit: dict) -> str:
    unix = hit.get("date-unix")
    if unix is not None:
        try:
            stamp = dt.datetime.fromtimestamp(int(unix), tz=dt.timezone.utc)
            return stamp.strftime("%Y-%m-%dT%H:%M:%SZ")
        except (TypeError, ValueError, OSError, OverflowError):
            pass
    raw = hit.get("date")
    if isinstance(raw, str) and raw.strip():
        return raw.strip()
    return ""


def _trim(text: str) -> str:
    text = text.strip().replace("\n", " ")
    if len(text) <= _STDERR_LIMIT:
        return text
    return text[:_STDERR_LIMIT] + "…"
