"""CIP-0005 validator for IMAP host/user/password payloads."""

from __future__ import annotations


def validate_imap(credential) -> bool:
    """Accept a host/user/password mapping stored as the CIP-0005 value."""
    value = credential.get("value", credential) if isinstance(credential, dict) else credential
    if not isinstance(value, dict):
        return False
    return all(
        isinstance(value.get(k), str) and value[k].strip()
        for k in ("host", "user", "password")
    )
