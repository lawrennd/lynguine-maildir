"""CIP-0005 validator for IMAP LOGIN and XOAUTH2 payloads."""

from __future__ import annotations

LOGIN_FIELDS = ("host", "user", "password")
XOAUTH2_FIELDS = ("host", "user", "client_id", "tenant", "refresh_token")
XOAUTH2_ONLY_FIELDS = ("client_id", "tenant", "refresh_token")


def validate_imap(credential) -> bool:
    """Accept LOGIN or XOAUTH2 mappings stored as the CIP-0005 value."""
    value = _unwrap(credential)
    if not isinstance(value, dict):
        return False
    try:
        classify_imap_credential(value)
    except ValueError:
        return False
    return True


def classify_imap_credential(value: dict) -> str:
    """Return ``login`` or ``xoauth2``. Raise ``ValueError`` if mixed or incomplete."""
    if not isinstance(value, dict):
        raise ValueError("IMAP credential_value must be a mapping")
    mode = _auth_mode(value)
    if mode == "login":
        mixed = [key for key in XOAUTH2_ONLY_FIELDS if _nonempty(value, key)]
        if mixed:
            raise ValueError(
                "IMAP credential_value mixes login and xoauth2 fields"
            )
        missing = [key for key in LOGIN_FIELDS if not _nonempty(value, key)]
        if missing:
            raise ValueError(
                "IMAP credential_value missing " + ", ".join(missing)
            )
        return "login"
    if _nonempty(value, "password"):
        raise ValueError(
            "IMAP credential_value mixes login and xoauth2 fields"
        )
    missing = [key for key in XOAUTH2_FIELDS if not _nonempty(value, key)]
    if missing:
        raise ValueError(
            "IMAP credential_value missing " + ", ".join(missing)
        )
    scope = value.get("scope")
    if scope is not None and not _nonempty(value, "scope"):
        raise ValueError("IMAP credential_value scope must be a non-empty string")
    return "xoauth2"


def normalize_imap_credential(value: dict) -> dict[str, str]:
    """Return a stripped LOGIN or XOAUTH2 dict with ``auth`` set."""
    mode = classify_imap_credential(value)
    if mode == "login":
        return {
            "auth": "login",
            **{key: value[key].strip() for key in LOGIN_FIELDS},
        }
    out = {
        "auth": "xoauth2",
        **{key: value[key].strip() for key in XOAUTH2_FIELDS},
    }
    if _nonempty(value, "scope"):
        out["scope"] = value["scope"].strip()
    return out


def _auth_mode(value: dict) -> str:
    auth = value.get("auth")
    if auth is None:
        return "login"
    if not isinstance(auth, str):
        raise ValueError(
            "IMAP credential_value unknown auth; use 'login' or 'xoauth2'"
        )
    token = auth.strip()
    if token in ("", "login"):
        return "login"
    if token == "xoauth2":
        return "xoauth2"
    raise ValueError(
        f"IMAP credential_value unknown auth {auth!r}; use 'login' or 'xoauth2'"
    )


def _unwrap(credential):
    if isinstance(credential, dict) and "value" in credential and isinstance(
        credential.get("value"), dict
    ):
        return credential["value"]
    return credential


def _nonempty(value: dict, key: str) -> bool:
    item = value.get(key)
    return isinstance(item, str) and bool(item.strip())
