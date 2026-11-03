"""Microsoft XOAUTH2 for IMAP. MSAL stays in this package, not in lynguine."""

from __future__ import annotations

import warnings

DEFAULT_IMAP_SCOPE = "https://outlook.office.com/IMAP.AccessAsUser.All"
OFFLINE_SCOPE = "offline_access"

_WRITEBACK_WARNED = False


class ImapOAuthError(RuntimeError):
    """OAuth client or extra missing — not an IMAP protocol failure."""


def xoauth2_sasl_payload(user: str, access_token: str) -> bytes:
    """SASL XOAUTH2 response. imaplib base64-encodes the return value."""
    return f"user={user}\x01auth=Bearer {access_token}\x01\x01".encode("utf-8")


def xoauth2_scopes(cred: dict) -> list[str]:
    scope = cred.get("scope") or DEFAULT_IMAP_SCOPE
    scopes = [scope]
    if OFFLINE_SCOPE not in scopes:
        scopes.append(OFFLINE_SCOPE)
    return scopes


def acquire_xoauth2_access_token(cred: dict) -> tuple[str, str | None]:
    """Refresh an access token. Return ``(access_token, new_refresh_or_none)``."""
    app = _public_client(cred["client_id"], cred["tenant"])
    result = app.acquire_token_by_refresh_token(
        cred["refresh_token"],
        scopes=xoauth2_scopes(cred),
    )
    if not isinstance(result, dict) or "access_token" not in result:
        raise ImapOAuthError(
            f"XOAUTH2 token refresh failed for user {cred['user']!r} "
            f"on {cred['host']!r}"
        )
    new_refresh = result.get("refresh_token")
    if not isinstance(new_refresh, str) or not new_refresh.strip():
        new_refresh = None
    elif new_refresh == cred["refresh_token"]:
        new_refresh = None
    return result["access_token"], new_refresh


def persist_rotated_refresh_token(
    details: dict | None,
    cred: dict,
    new_refresh: str,
) -> None:
    """Write a rotated refresh token via CIP-001A. Warn once if persist fails."""
    global _WRITEBACK_WARNED
    cred["refresh_token"] = new_refresh
    key = (details or {}).get("credential")
    if not isinstance(key, str) or not key.strip():
        return
    payload = {
        "auth": "xoauth2",
        "host": cred["host"],
        "user": cred["user"],
        "client_id": cred["client_id"],
        "tenant": cred["tenant"],
        "refresh_token": new_refresh,
    }
    if cred.get("scope"):
        payload["scope"] = cred["scope"]
    try:
        from lynguine.security import set_credential

        set_credential(key.strip(), payload, credential_type="imap")
    except Exception:
        if not _WRITEBACK_WARNED:
            _WRITEBACK_WARNED = True
            warnings.warn(
                "IMAP XOAUTH2 refresh token rotated but could not be stored; "
                "the new token is kept for this process only",
                UserWarning,
                stacklevel=2,
            )


def acquire_interactive_grant(
    *,
    client_id: str,
    tenant: str,
    scopes: list[str],
    printer=None,
) -> dict:
    """Device-code sign-in, with interactive fallback if device flow is blocked."""
    app = _public_client(client_id, tenant)
    flow = app.initiate_device_flow(scopes=scopes)
    if isinstance(flow, dict) and flow.get("user_code"):
        message = flow.get("message") or (
            "Complete device-code sign-in in the browser."
        )
        if printer is not None:
            printer(message)
        result = app.acquire_token_by_device_flow(flow)
    else:
        result = app.acquire_token_interactive(scopes=scopes)
    if not isinstance(result, dict) or "refresh_token" not in result:
        raise ImapOAuthError(
            "Microsoft sign-in did not return a refresh token; "
            "the Entra app needs delegated IMAP.AccessAsUser.All and offline_access"
        )
    return result


def _public_client(client_id: str, tenant: str):
    PublicClientApplication = _load_public_client_application()
    return PublicClientApplication(
        client_id,
        authority=f"https://login.microsoftonline.com/{tenant}",
    )


def _load_public_client_application():
    try:
        from msal import PublicClientApplication
    except ImportError as exc:
        raise ImapOAuthError(
            "XOAUTH2 IMAP requires the oauth extra: pip install 'lynguine-maildir[oauth]'"
        ) from exc
    return PublicClientApplication
