---
id: "2026-11-01_read-maildir"
title: "Read Maildir headers into a DataFrame"
status: "Completed"
priority: "High"
created: "2026-11-01"
last_updated: "2026-11-01"
category: "features"
related_cips: ["0003"]
owner: "Neil D. Lawrence"
dependencies:
- "2026-11-01_rename-lynguine-maildir"
tags:
- backlog
- maildir
- access
---

# Task: Read Maildir headers into a DataFrame

> Backlog tasks are DOING the work defined in CIPs (HOW).
> Use `related_cips` to link to CIPs. Don't link directly to requirements.

## Description

Implement `read_maildir` and register `type: maildir` with no
credential bind. YAML names `path:` (alias `folder:`) to one Maildir
directory (`cur/` and/or `new/`). Rows use the same columns as live
IMAP. Skip `tmp/`. Do not move files out of `new/`. Do not run a
syncer.

## Acceptance Criteria

- [x] `type: maildir` returns columns `uid`, `message_id`, `subject`,
      `from`, `date`
- [x] `uid` is the Maildir unique basename with flags stripped, not an
      IMAP UID
- [x] `tmp/` is ignored; files in `new/` stay in `new/`
- [x] Missing or non-Maildir path fails with the path in the message
- [x] `write_data` on `type: maildir` fails as read-only
- [x] YAML has no `credential:`; `~` in `path` is expanded

## Implementation Notes

Parse headers only. Optional `limit` keeps newest files by mtime.
`folder:` is an alias of `path:`; both set and different is an error.
Do not recurse an account root into many folders.

## Related

- CIP: 0003

## Progress Updates

### 2026-11-01

Task created Ready after CIP-0003 acceptance.

`read_maildir` landed. Status Completed.
