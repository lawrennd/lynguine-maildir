---
id: "0001"
title: "IMAP mailbox subjects as a lynguine table"
status: "In Progress"
priority: "High"
created: "2026-10-30"
last_updated: "2026-10-30"
related_tenets: []
stakeholders:
- Application developers (referia and other lynguine flows)
- Operators who already have IMAP credentials
tags:
- requirement
- access
- imap
- plugins
---

# REQ-0001: IMAP mailbox subjects as a lynguine table

> Requirements describe **WHAT** should be true (outcomes), not HOW to achieve it.

## Description

A lynguine flow can name `type: imap` and receive a DataFrame of mailbox
**metadata**: one row per message, with subject, from, date, and message
id. The live mailbox is the authoritative store. Message **bodies** are
out of scope.

Lynguine stays thin: this package implements the type. Secrets stay in
CIP-0005; YAML names a credential key, not a password. The type is
read-only. Unknown folders and missing credentials fail clearly.

**Why this matters**: lynguine CIP-0019 / REQ-0010 exists so vendor
stores do not land in `io.py`. Mail subjects are the first real plugin.

**Who benefits**: review and allocation flows that want an inbox table
without exporting mail to YAML first.

## Acceptance Criteria

- [x] A flow with `type: imap` receives a DataFrame of message metadata
- [x] Credentials come from lynguine (`credential_value`); passwords are not in YAML
- [x] Selecting a missing folder fails with the folder name
- [x] `write_data` on `type: imap` fails as read-only
- [x] CI tests do not open a network connection or use real mailboxes
- [x] Message bodies are not returned as table columns

## Notes

Inbound access only. referia's outbound `type: email` drafts are a
different type in a different package.

lynguine CIP-0019 sketched this package as `lynguine-mail` with `type:
imap`. This repository is that plugin, named `lynguine-imap`.

## References

- lynguine [CIP-0019](https://github.com/lawrennd/lynguine/blob/main/cip/cip0019.md)
- lynguine [REQ-0010](https://github.com/lawrennd/lynguine/blob/main/requirements/req0010_pluggable-io-types.md)
- [Writing a tabular IO plugin](https://github.com/lawrennd/lynguine/blob/main/docs/getting_started/io_plugins.rst)

## Progress Updates

### 2026-10-30

Requirement created with the plugin form already registered. Status In
Progress while the IMAP fetch lands.

OAuth2 / Exchange Online is [REQ-0002](./req0002_oauth2-imap.md), not
this requirement. Password `LOGIN` stays here.

A local Maildir replica is [REQ-0003](./req0003_maildir-message-table.md).
