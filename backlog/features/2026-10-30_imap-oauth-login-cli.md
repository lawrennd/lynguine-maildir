---
id: "2026-10-30_imap-oauth-login-cli"
title: "Plugin login command for XOAUTH2 bootstrap"
status: "Completed"
priority: "High"
created: "2026-10-30"
last_updated: "2026-10-30"
category: "features"
related_cips: ["0002"]
owner: "Neil D. Lawrence"
dependencies:
- "2026-10-30_two-form-imap-validator"
tags:
- backlog
- imap
- oauth
- cli
---

# Task: Plugin login command for XOAUTH2 bootstrap

> Backlog tasks are DOING the work defined in CIPs (HOW).
> Use `related_cips` to link to CIPs. Don't link directly to requirements.

## Description

Add `python -m lynguine_imap.login` (optional Poetry script
`lynguine-imap-login`) so the operator completes a Microsoft public-
client device-code sign-in once. The command stores `{auth: xoauth2,
host, user, client_id, tenant, refresh_token}` via lynguine
`set_credential`. `lynguine-cred` stays offline. This repository does
not ship a client id.

## Acceptance Criteria

- [x] Device-code (or interactive fallback) grant is acquired in this
      package, not in lynguine-cred
- [x] Stored dict has `auth: xoauth2` and no password
- [x] Command output prints the credential key, not tokens
- [x] Entra client id is an operator argument, not a default in code

## Implementation Notes

MSAL public client. Scopes: IMAP delegated access and `offline_access`.
If device code is blocked, fall back to auth-code with a local
redirect. Optional `oauth` extra supplies `msal`.

## Related

- CIP: 0002

## Progress Updates

### 2026-10-30

Task created In Progress with CIP-0002 implementation.

`python -m lynguine_imap.login` and `lynguine-imap-login` landed.
Status Completed.
