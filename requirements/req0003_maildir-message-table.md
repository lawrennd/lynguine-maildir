---
id: "0003"
title: "A local Maildir is a lynguine message table"
status: "Implemented"
priority: "High"
created: "2026-11-01"
last_updated: "2026-11-01"
related_tenets: []
stakeholders:
- Operators who already sync mail to Maildir
- Application developers using type: imap who want an offline replica
tags:
- requirement
- access
- maildir
- plugins
---

# REQ-0003: A local Maildir is a lynguine message table

> Requirements describe **WHAT** should be true (outcomes), not HOW to achieve it.

## Description

A flow can name a local Maildir directory and receive the same
message-metadata DataFrame as REQ-0001: one row per message, with
subject, from, date, and message id. The directory on disk is the store
lynguine reads. Syncing that directory from an IMAP server is outside
this package.

YAML names a filesystem path, not a credential. There is no OAuth, no
password, and no live mailbox connection. The type is read-only.
Unseen messages stay unseen: reading does not move mail from `new/` to
`cur/`.

**Why this matters**: operators already synchronise IMAP to Maildir
(offlineimap, mbsync). A table over that tree lets lynguine use mail
without embedding a syncer or a vendor OAuth client.

**Who benefits**: flows that want inbox rows from an existing Maildir;
operators who keep OAuth and IMAP sync in tools that already do them.

## Acceptance Criteria

- [x] `type: maildir` against a Maildir directory returns the REQ-0001
      columns
- [x] YAML names a path; it does not name a password or token
- [x] Reading does not alter the Maildir (no `new/` → `cur/` moves)
- [x] `write_data` on `type: maildir` fails as read-only
- [x] CI tests do not open a network connection or use a live mailbox
- [x] Message bodies are not returned as table columns

## Notes

Live IMAP remains REQ-0001 / REQ-0002. This requirement is the local
replica, not a replacement for the live type.

How the Maildir is filled (offlineimap, mbsync, or otherwise) is an
operator choice.

## References

- [REQ-0001](./req0001_imap-message-table.md) — same table grain
- lynguine [CIP-0019](https://github.com/lawrennd/lynguine/blob/main/cip/cip0019.md)

## Progress Updates

### 2026-11-01

Requirement created with CIP-0003 (Proposed). CIP-0003 accepted.
Ready for implementation.

CIP-0003 In Progress. Backlog tasks created (rename, reader, tests,
README).

CIP-0003 implemented. 53 tests passed (Maildir fixture, no network).
Live Maildir on a laptop is operator validation before the CIP is
Closed.
