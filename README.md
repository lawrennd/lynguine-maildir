# lynguine-imap

IMAP mailbox *subjects* as a lynguine tabular source (`type: imap`).

This is inbound access. It is not referia's outbound `type: email` drafts.

Point at the plugin form in lynguine:

https://github.com/lawrennd/lynguine/blob/main/docs/getting_started/io_plugins.rst

## Authorisation

This package **declares** `credential_type="imap"`. lynguine fetches the CIP-0005
secret named by `credential:` and passes it as `credential_value` (host, user,
password). Store that secret in lynguine's local encrypted files (or
`LYNGUINE_CRED_*`); do not put the password in YAML.

```python
from lynguine.security import set_credential

set_credential(
    "my_mail",
    {
        "host": "imap.example.org",
        "user": "inbox@example.org",
        "password": "...",
    },
    credential_type="imap",
)
```

Encrypted-file storage needs `LYNGUINE_MASTER_KEY` and writes under
`~/.lynguine/credentials/` (see lynguine's credential user guide).

```yaml
input:
  type: imap
  folder: INBOX
  credential: my_mail
  index: message_id
plugins:
  - lynguine_imap
```

Optional keys: `limit` (newest UIDs), `ssl` (default true), `port`
(default 993 with SSL). `mailbox:` is an alias for `folder:`.

Each row is one message: `uid`, `message_id`, `subject`, `from`, `date`.
Bodies are not fetched. Unseen mail stays unseen (`BODY.PEEK`, read-only
`SELECT`). The type is read-only.

## Status

Registration, credentials, and the IMAP header reader are in place.
Tests mock IMAP; they do not open a network connection.
