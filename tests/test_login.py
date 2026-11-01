"""Bootstrap command tests. MSAL is stubbed. No network."""

import io

from lynguine_maildir.login import bootstrap, main

GRANT = {
    "access_token": "access-secret",
    "refresh_token": "refresh-secret",
}


def test_bootstrap_stores_xoauth2_without_password():
    stored = {}
    printed = []

    def store(name, value, credential_type=None):
        stored["name"] = name
        stored["value"] = dict(value)
        stored["type"] = credential_type

    def acquire(**kwargs):
        return GRANT

    payload = bootstrap(
        name="office_mail",
        host="outlook.office365.com",
        user="user@example.com",
        client_id="client-id",
        tenant="organizations",
        acquire=acquire,
        store=store,
        printer=printed.append,
    )
    assert stored["name"] == "office_mail"
    assert stored["type"] == "imap"
    assert stored["value"]["auth"] == "xoauth2"
    assert "password" not in stored["value"]
    assert stored["value"]["refresh_token"] == "refresh-secret"
    assert payload["refresh_token"] == "refresh-secret"
    joined = "\n".join(printed)
    assert "office_mail" in joined
    assert "refresh-secret" not in joined
    assert "access-secret" not in joined


def test_main_passes_operator_client_id(monkeypatch):
    seen = {}

    def fake_bootstrap(**kwargs):
        seen.update(kwargs)

    code = main(
        [
            "--name",
            "office_mail",
            "--host",
            "outlook.office365.com",
            "--user",
            "user@example.com",
            "--client-id",
            "operator-client-id",
            "--tenant",
            "organizations",
        ],
        bootstrap_fn=fake_bootstrap,
    )
    assert code == 0
    assert seen["client_id"] == "operator-client-id"
    assert seen["name"] == "office_mail"
    assert seen["host"] == "outlook.office365.com"


def test_bootstrap_does_not_print_tokens_to_stderr():
    buf = io.StringIO()

    bootstrap(
        name="office_mail",
        host="outlook.office365.com",
        user="user@example.com",
        client_id="client-id",
        tenant="organizations",
        acquire=lambda **k: GRANT,
        store=lambda *a, **k: None,
        printer=lambda msg: buf.write(msg + "\n"),
    )
    out = buf.getvalue()
    assert "refresh-secret" not in out
    assert "access-secret" not in out
