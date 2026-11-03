---
id: "0004"
title: "A mu search is a lynguine message table"
status: "Implemented"
priority: "High"
created: "2026-11-02"
last_updated: "2026-11-02"
related_tenets: []
stakeholders:
- Operators who already index Maildir with mu
- Flows that need recent or filtered mail across folders
tags:
- requirement
- access
- maildir
- mu
- plugins
---

# REQ-0004: A mu search is a lynguine message table

> Requirements describe **WHAT** should be true (outcomes), not HOW to achieve it.

## Description

A flow can name a **mu query** and receive the same message-metadata
DataFrame as REQ-0001 / REQ-0003: one row per matching message, with
subject, from, date, and message id. The mu database is the store
lynguine reads. Building and refreshing that database (`mu init`,
`mu index`) is outside this package.

YAML names a query string, not a credential and not a Maildir folder
path. There is no OAuth, no password, and no live mailbox connection.
The type is read-only. Reading does not alter Maildir files or the mu
index.

**Why this matters**: operators already synchronise IMAP to Maildir and
index it with mu. A table over a query lets lynguine retrieve recent or
filtered mail across accounts without scanning every `cur/` directory
or stacking one spec per folder.

**Who benefits**: listing and review flows that want Date-ordered or
`from:`/`subject:` rows from an existing mu index.

## Acceptance Criteria

- [x] `type: mu` against a mu query returns the REQ-0001 columns
- [x] YAML names a query; it does not name a password or token
- [x] Reading does not alter Maildir files or the mu index
- [x] `write_data` on `type: mu` fails as read-only
- [x] Missing `mu` binary, missing index, or mu error fails clearly
- [x] Zero matches returns the column frame, no rows
- [x] CI tests do not require a live mu database (the `mu` binary may
      be mocked)
- [x] Message bodies are not returned as table columns

## Notes

`type: maildir` (REQ-0003) remains the folder scan and must work
without mu. This requirement is retrieval over an operator-maintained
index, not a fast path inside `type: maildir`.

notmuch is a different indexer and is not this requirement.

## References

- [REQ-0001](./req0001_imap-message-table.md) — same table grain
- [REQ-0003](./req0003_maildir-message-table.md) — local folder scan
- [mu-find(1)](https://manpages.debian.org/mu-find)
- [mu-query(7)](https://manpages.debian.org/mu-query)

## Progress Updates

### 2026-11-02

Requirement created with CIP-0004 (Proposed). `type: mu` implemented
(`read_mu`, register, fake-binary tests). Live index is operator-owned;
the referia mail Find listing is a demo, not CI.
