"""Interactive Microsoft sign-in for IMAP XOAUTH2. lynguine-cred stays offline."""

from __future__ import annotations

import argparse
import sys

from .oauth import (
    DEFAULT_IMAP_SCOPE,
    ImapOAuthError,
    acquire_interactive_grant,
    xoauth2_scopes,
)


def bootstrap(
    *,
    name: str,
    host: str,
    user: str,
    client_id: str,
    tenant: str,
    scope: str | None = None,
    acquire=None,
    store=None,
    printer=None,
) -> dict:
    """Device-code grant, then ``set_credential``. Returns the stored dict."""
    cred = {
        "auth": "xoauth2",
        "host": host,
        "user": user,
        "client_id": client_id,
        "tenant": tenant,
    }
    if scope:
        cred["scope"] = scope
    grant_fn = acquire or _default_acquire
    result = grant_fn(
        client_id=client_id,
        tenant=tenant,
        scopes=xoauth2_scopes(cred),
        printer=printer or _stderr_printer,
    )
    refresh = result.get("refresh_token") if isinstance(result, dict) else None
    if not isinstance(refresh, str) or not refresh.strip():
        raise ImapOAuthError(
            "Microsoft sign-in did not return a refresh token; "
            "the Entra app needs delegated IMAP.AccessAsUser.All and offline_access"
        )
    cred["refresh_token"] = refresh.strip()
    store_fn = store or _default_store
    store_fn(name, cred, credential_type="imap")
    out = printer or _stderr_printer
    out(f"Stored IMAP credential {name!r}")
    return cred


def main(argv=None, *, bootstrap_fn=bootstrap) -> int:
    args = _parse_args(argv)
    bootstrap_fn(
        name=args.name,
        host=args.host,
        user=args.user,
        client_id=args.client_id,
        tenant=args.tenant,
        scope=args.scope,
    )
    return 0


def _parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="lynguine-maildir-login",
        description=(
            "Sign in to Microsoft 365 IMAP with a public client and store "
            "the refresh token via lynguine set_credential. "
            "Register the Entra app yourself; this command does not ship a client id."
        ),
    )
    parser.add_argument("--name", required=True, help="CIP-0005 credential key")
    parser.add_argument("--host", required=True, help="IMAP hostname")
    parser.add_argument("--user", required=True, help="Mailbox username")
    parser.add_argument(
        "--client-id",
        required=True,
        help="Entra public client id (operator-registered)",
    )
    parser.add_argument(
        "--tenant",
        required=True,
        help="Directory id, organizations, or common",
    )
    parser.add_argument(
        "--scope",
        default=None,
        help=f"IMAP scope (default {DEFAULT_IMAP_SCOPE})",
    )
    return parser.parse_args(argv)


def _default_acquire(**kwargs):
    return acquire_interactive_grant(**kwargs)


def _default_store(name, value, credential_type=None):
    from lynguine.security import set_credential

    set_credential(name, value, credential_type=credential_type)


def _stderr_printer(message: str) -> None:
    print(message, file=sys.stderr)


if __name__ == "__main__":
    sys.exit(main())
