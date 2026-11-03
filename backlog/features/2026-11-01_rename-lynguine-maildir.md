---
id: "2026-11-01_rename-lynguine-maildir"
title: "Rename package to lynguine-maildir"
status: "Completed"
priority: "High"
created: "2026-11-01"
last_updated: "2026-11-01"
category: "features"
related_cips: ["0003"]
owner: "Neil D. Lawrence"
dependencies: []
tags:
- backlog
- rename
- maildir
---

# Task: Rename package to lynguine-maildir

> Backlog tasks are DOING the work defined in CIPs (HOW).
> Use `related_cips` to link to CIPs. Don't link directly to requirements.

## Description

Rename the distribution, import, Poetry entry points, and tests from
`lynguine-imap` / `lynguine_imap` to `lynguine-maildir` /
`lynguine_maildir`. Both `type: imap` and the coming `type: maildir`
load from the new package. No compatibility shim.

## Acceptance Criteria

- [x] `pyproject.toml` name is `lynguine-maildir`; package is
      `lynguine_maildir`
- [x] Import `lynguine_imap` fails; `lynguine_maildir` registers
      `type: imap`
- [x] Poetry plugin and `lynguine-maildir-login` script use the new
      module
- [x] Existing IMAP tests import `lynguine_maildir` and pass

## Implementation Notes

GitHub and on-disk clone names are an operator step, not this task.
Move `lynguine_imap/` to `lynguine_maildir/` and update every import.
CIP-0002 login extra (`oauth`) stays; only the module path changes.

## Related

- CIP: 0003

## Progress Updates

### 2026-11-01

Task created Ready after CIP-0003 acceptance.

GitHub repo is `lynguine-maildir`. Python package renamed. Status
Completed.
