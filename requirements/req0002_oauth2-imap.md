---
id: "0002"
title: "OAuth2 IMAP mailboxes work as type: imap"
status: "Implemented"
priority: "High"
created: "2026-10-30"
last_updated: "2026-10-30"
related_tenets: []
stakeholders:
- Operators on Microsoft 365 / Exchange Online (including University of Cambridge)
- Application developers using type: imap
tags:
- requirement
- access
- imap
- oauth
- plugins
---

# REQ-0002: OAuth2 IMAP mailboxes work as type: imap

> Requirements describe **WHAT** should be true (outcomes), not HOW to achieve it.

## Description

A flow can name `type: imap` against a mailbox that refuses IMAP
`LOGIN` (Microsoft 365 / Exchange Online, including `@cam.ac.uk`) and
still receive the same message-metadata DataFrame as REQ-0001.

YAML still names a CIP-0005 credential key, not a token. The operator
completes interactive sign-in (password + MFA) once; later reads use
the stored grant. Classic password IMAP keeps working. lynguine does
not grow a Microsoft OAuth SDK.

**Why this matters**: University Exchange Online documents IMAP on
`outlook.office365.com:993` with **Modern / OAuth2** only. Basic auth
is retired. REQ-0001's password credential cannot open that store.

**Who benefits**: Cambridge and other Microsoft 365 operators who want
inbox rows without exporting mail to YAML; plugin authors who must not
put MSAL in lynguine.

## Acceptance Criteria

- [x] `type: imap` against Exchange Online returns the REQ-0001 columns
      after an OAuth2 sign-in, without IMAP `LOGIN`
- [x] YAML contains `credential:` only; no access token, refresh token,
      or password
- [x] Password `LOGIN` mailboxes keep today's behaviour
- [x] Auth mode is named in the stored credential; it is not inferred
      from the hostname
- [x] CI tests do not open a network connection, a browser, or a real
      tenant
- [x] lynguine core does not gain `msal` or a Microsoft validator

## Notes

Obtaining the grant is this package's job. Storing it is lynguine
CIP-0005 / CIP-001A. `lynguine-cred` does not talk to Microsoft.

Admin consent for an Entra app, if the tenant requires it, is an
operator step, not software in this repository.

## References

- [REQ-0001](./req0001_imap-message-table.md) — same table grain
- lynguine [CIP-0019](https://github.com/lawrennd/lynguine/blob/main/cip/cip0019.md)
- lynguine [CIP-001A](https://github.com/lawrennd/lynguine/blob/main/cip/cip001A.md)
- [UIS: How to access your mailbox](https://help.uis.cam.ac.uk/service/collaboration/365/exchange-online/how-access-your-mailbox)

## Progress Updates

### 2026-10-30

Requirement created with CIP-0002 (Proposed). CIP accepted and
implementation started.

CIP-0002 implemented with mocked XOAUTH2 tests (40 passed, no
network). Live Exchange Online sign-in is operator validation before
the CIP is Closed.
