---
id: "2026-11-01_maildir-fixture-tests"
title: "Fixture tests for type: maildir"
status: "Completed"
priority: "High"
created: "2026-11-01"
last_updated: "2026-11-01"
category: "features"
related_cips: ["0003"]
owner: "Neil D. Lawrence"
dependencies:
- "2026-11-01_read-maildir"
tags:
- backlog
- maildir
- tests
---

# Task: Fixture tests for type: maildir

> Backlog tasks are DOING the work defined in CIPs (HOW).
> Use `related_cips` to link to CIPs. Don't link directly to requirements.

## Description

Cover `type: maildir` with an in-process Maildir fixture. No sockets,
no live mailbox, no syncer. Keep CIP-0001 / CIP-0002 IMAP tests green
under `lynguine_maildir`.

## Acceptance Criteria

- [x] Fixture with one message in `cur/`, one in `new/`, junk in
      `tmp/` yields two rows; `tmp/` ignored; `new/` file unmoved
- [x] MIME-encoded Subject matches the IMAP reader behaviour
- [x] `path` with `~` expands; a non-Maildir directory fails naming
      the path
- [x] Empty Maildir returns the column frame with no rows
- [x] IMAP tests still pass; tests do not open a network connection

## Implementation Notes

Build the fixture under pytest `tmp_path`. Assert on filesystem after
read to prove `new/` was not renamed.

## Related

- CIP: 0003

## Progress Updates

### 2026-11-01

Task created Ready after CIP-0003 acceptance.

53 tests passed. Status Completed.
