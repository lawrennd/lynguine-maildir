# lynguine-maildir

Mailbox *subjects* as a lynguine tabular source. The primary store is a
local **Maildir** (`type: maildir`). Live IMAP (`type: imap`) is the path
without a replica.

This is inbound access. It is not referia's outbound `type: email` drafts.

Point at the plugin form in lynguine:

https://github.com/lawrennd/lynguine/blob/main/docs/getting_started/io_plugins.rst

## Maildir

YAML names a filesystem path to **one** Maildir folder (the directory that
contains `cur/` and `new/`). There is no credential. Syncing that tree from
IMAP (offlineimap, mbsync, or similar) is outside this package.

```yaml
input:
  type: maildir
  path: ~/Maildir/fastmail/INBOX
  index: message_id
plugins:
  - lynguine_maildir
```

Optional keys: `limit` (newest files by mtime). `folder:` is an alias for
`path:`.

Each row is one message: `uid`, `message_id`, `subject`, `from`, `date`.
For Maildir, `uid` is the unique basename with flags stripped (`:2,…`
removed). That is not an IMAP UID. Bodies are not returned as columns.
Reading does not move mail from `new/` to `cur/`. The type is read-only.

## Live IMAP

When there is no local replica, `type: imap` still reads the mailbox.
This package **declares** `credential_type="imap"`. lynguine fetches the
CIP-0005 secret named by `credential:` and passes it as `credential_value`.
Store that secret in lynguine's local encrypted files (or `LYNGUINE_CRED_*`);
do not put passwords or tokens in YAML.

Two explicit forms. The `auth` field names the IMAP SASL method; it is not
inferred from the hostname.

**LOGIN** (default when `auth` is omitted):

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

**XOAUTH2** (Microsoft 365 / Exchange Online). Install the extra, register an
Entra **public** client with delegated `IMAP.AccessAsUser.All` and
`offline_access`, then bootstrap once. This repository does not ship a client
id. Operators may instead sync to Maildir with offlineimap and use
`type: maildir`.

```bash
pip install 'lynguine-maildir[oauth]'

python -m lynguine_maildir.login --name office_mail \
  --host outlook.office365.com \
  --user user@example.com \
  --client-id <entra-public-client-id> \
  --tenant organizations
```

Encrypted-file storage needs a master key (lynguine CIP-001A / OS keyring)
and writes under `~/.lynguine/credentials/` (see lynguine's credential user
guide).

```yaml
input:
  type: imap
  folder: INBOX
  credential: my_mail
  index: message_id
plugins:
  - lynguine_maildir
```

Optional keys: `limit` (newest UIDs), `ssl` (default true), `port`
(default 993 with SSL). `mailbox:` is an alias for `folder:`. Unseen mail
stays unseen (`BODY.PEEK`, read-only `SELECT`).

## Status

`type: maildir` and live `type: imap` (LOGIN and XOAUTH2) are in place.
Tests use a Maildir fixture and mock IMAP/MSAL; they do not open a network
connection.
