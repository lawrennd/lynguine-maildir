---
id: "2026-10-30_xoauth2-imap-connect"
title: "XOAUTH2 IMAP connect path"
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
- xoauth2
---

# Task: XOAUTH2 IMAP connect path

> Backlog tasks are DOING the work defined in CIPs (HOW).
> Use `related_cips` to link to CIPs. Don't link directly to requirements.

## Description

Branch IMAP connect on the stored `auth` field. `LOGIN` stays
`client.login`. `xoauth2` refreshes an access token with MSAL and
calls `AUTHENTICATE XOAUTH2`. Header fetch from CIP-0001 is unchanged.
If Microsoft returns a new refresh token, persist it with
`set_credential` when the YAML key is known; otherwise warn once and
keep the in-memory token.

## Acceptance Criteria

- [x] XOAUTH2 sessions call `authenticate("XOAUTH2", ...)` and never
      `login()`
- [x] LOGIN sessions still call `login()` and never `authenticate`
- [x] Failures name host and user, never the access or refresh token
- [x] Missing `msal` raises an install-extra error, not an IMAP error
- [x] Rotated refresh tokens are written back when `set_credential`
      is available

## Implementation Notes

Default IMAP scope is `https://outlook.office.com/IMAP.AccessAsUser.All`
plus `offline_access`. Access tokens are not stored. SASL payload is
`user=<user>^Aauth=Bearer <token>^A^A` (imaplib base64-encodes it).

## Related

- CIP: 0002

## Progress Updates

### 2026-10-30

Task created In Progress with CIP-0002 implementation.

`connect_from_credential` / `connect_imap_xoauth2` landed. Status
Completed.
