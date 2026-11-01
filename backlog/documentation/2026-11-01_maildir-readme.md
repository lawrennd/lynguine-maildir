---
id: "2026-11-01_maildir-readme"
title: "README for Maildir as the primary store"
status: "Completed"
priority: "Medium"
created: "2026-11-01"
last_updated: "2026-11-01"
category: "documentation"
related_cips: ["0003"]
owner: "Neil D. Lawrence"
dependencies:
- "2026-11-01_rename-lynguine-maildir"
- "2026-11-01_read-maildir"
tags:
- backlog
- maildir
- documentation
---

# Task: README for Maildir as the primary store

> Backlog tasks are DOING the work defined in CIPs (HOW).
> Use `related_cips` to link to CIPs. Don't link directly to requirements.

## Description

Rewrite the project README so Maildir is the primary store: YAML
`type: maildir` and `path:`. Document live `type: imap` as the path
without a replica. State that IMAP/OAuth sync (offlineimap, mbsync,
or similar) is outside this package. Do not ship a client id.

## Acceptance Criteria

- [x] README uses package name `lynguine-maildir` and import
      `lynguine_maildir`
- [x] Maildir example is the first YAML; IMAP LOGIN / XOAUTH2 remain
      as the live path
- [x] Syncers are named as operator tools, not as code in this repo
- [x] `uid` for Maildir is documented as the unique basename, not an
      IMAP UID

## Implementation Notes

Keep the header-only, read-only contract. Point at CIP-0002 for live
XOAUTH2. Do not paste tenant-specific mailbox instructions.

## Related

- CIP: 0003

## Progress Updates

### 2026-11-01

Task created Ready after CIP-0003 acceptance.

README rewritten. Status Completed.
