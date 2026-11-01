---
id: "2026-10-30_two-form-imap-validator"
title: "Two-form imap credential validator"
status: "Completed"
priority: "High"
created: "2026-10-30"
last_updated: "2026-10-30"
category: "features"
related_cips: ["0002"]
owner: "Neil D. Lawrence"
dependencies: []
tags:
- backlog
- imap
- oauth
- credentials
---

# Task: Two-form imap credential validator

> Backlog tasks are DOING the work defined in CIPs (HOW).
> Use `related_cips` to link to CIPs. Don't link directly to requirements.

## Description

Extend `validate_imap` so a stored CIP-0005 dict is either IMAP `LOGIN`
(`host`, `user`, `password`; `auth` omitted or `login`) or SASL
`XOAUTH2` (`auth: xoauth2` plus `host`, `user`, `client_id`, `tenant`,
`refresh_token`). Mixed fields and unknown `auth` values are rejected.
Do not infer the form from the hostname.

## Acceptance Criteria

- [x] LOGIN form (with or without `auth: login`) still validates
- [x] XOAUTH2 form validates when required fields are present and
      `password` is absent
- [x] Mixed LOGIN and XOAUTH2 fields fail validation
- [x] Unknown `auth` values fail validation

## Implementation Notes

Keep the validator a boolean predicate for CIP-0005. Raise a clear
`ValueError` from the reader when a bound `credential_value` is the
wrong form.

## Related

- CIP: 0002

## Progress Updates

### 2026-10-30

Task created In Progress with CIP-0002 implementation.

Validator and tests landed in `lynguine_imap/credentials.py`. Status
Completed.
