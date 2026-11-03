---
id: "2026-10-30_oauth-extra-mocked-tests"
title: "oauth extra, mocked tests, and README"
status: "Completed"
priority: "High"
created: "2026-10-30"
last_updated: "2026-10-30"
category: "features"
related_cips: ["0002"]
owner: "Neil D. Lawrence"
dependencies:
- "2026-10-30_xoauth2-imap-connect"
- "2026-10-30_imap-oauth-login-cli"
tags:
- backlog
- imap
- oauth
- tests
- documentation
---

# Task: oauth extra, mocked tests, and README

> Backlog tasks are DOING the work defined in CIPs (HOW).
> Use `related_cips` to link to CIPs. Don't link directly to requirements.

## Description

Declare optional extra `oauth` (`msal`) so LOGIN-only installs stay
thin. Cover the XOAUTH2 path with in-process fakes: SASL mechanism,
token refresh stub, LOGIN regression, missing-msal message, and
bootstrap storage. No sockets, no real tenant. Document the Entra
public client and CIP-001A store in the README. Do not ship a client
id.

## Acceptance Criteria

- [x] `lynguine-imap[oauth]` installs `msal`; the core extra is
      optional
- [x] Tests mock IMAP and MSAL; they do not open a network connection
- [x] LOGIN tests from CIP-0001 still pass
- [x] README documents XOAUTH2 credentials and the login command
- [x] No client id is hardcoded in the package

## Implementation Notes

Assert the Bearer token never appears in logs or exception text.
README may use Exchange Online as an example; operator registers the
Entra app.

## Related

- CIP: 0002

## Progress Updates

### 2026-10-30

Task created In Progress with CIP-0002 implementation.

40 tests passed. README documents XOAUTH2. Status Completed.
