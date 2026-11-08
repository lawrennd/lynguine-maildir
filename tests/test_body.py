"""Listing body extra: markdown, Safe Links, image policy."""

from pathlib import Path
from urllib.parse import quote

import pytest

from lynguine_maildir.body import listing_body, unwrap_safe_link, unwrap_safe_links
from lynguine_maildir.maildir import read_maildir

SAFE = (
    "https://eur03.safelinks.protection.outlook.com/?url="
    + quote("https://example.com/path", safe="")
    + "&data=05%7C02&reserved=0"
)


def _maildir(root: Path) -> Path:
    (root / "cur").mkdir(parents=True)
    (root / "new").mkdir()
    (root / "tmp").mkdir()
    return root


def _write(path: Path, raw: str) -> None:
    path.write_bytes(raw.encode("utf-8"))


def test_unwrap_safe_link():
    assert unwrap_safe_link(SAFE) == "https://example.com/path"
    assert unwrap_safe_link("https://example.com") == "https://example.com"


def test_listing_body_unwraps_html_safe_links(tmp_path):
    path = tmp_path / "msg"
    _write(
        path,
        "From: a@example.org\r\n"
        "Content-Type: text/html; charset=utf-8\r\n"
        "\r\n"
        f'<p>See <a href="{SAFE}">the site</a>.</p>\r\n',
    )
    text = listing_body(path)
    assert "safelinks.protection.outlook.com" not in text
    assert "[the site](https://example.com/path)" in text


def test_listing_body_unwraps_plain_safe_links(tmp_path):
    path = tmp_path / "msg"
    _write(
        path,
        "From: a@example.org\r\n"
        "Content-Type: text/plain; charset=utf-8\r\n"
        "\r\n"
        f"See {SAFE}\r\n",
    )
    text = listing_body(path)
    assert "safelinks.protection.outlook.com" not in text
    assert "https://example.com/path" in text
    assert unwrap_safe_links(SAFE) == "https://example.com/path"


def test_listing_body_prefers_plain_over_html(tmp_path):
    path = tmp_path / "msg"
    _write(
        path,
        "From: a@example.org\r\n"
        "MIME-Version: 1.0\r\n"
        "Content-Type: multipart/alternative; boundary=b\r\n"
        "\r\n"
        "--b\r\n"
        "Content-Type: text/plain; charset=utf-8\r\n"
        "\r\n"
        "Hello plain\r\n"
        "--b\r\n"
        "Content-Type: text/html; charset=utf-8\r\n"
        "\r\n"
        "<table><tr><td></td></tr></table><p>Hello <b>html</b></p>\r\n"
        "--b--\r\n",
    )
    text = listing_body(path)
    assert "Hello plain" in text
    assert "**html**" not in text
    assert "| --- |" not in text


def test_listing_body_html_only_still_markdown(tmp_path):
    path = tmp_path / "msg"
    _write(
        path,
        "From: a@example.org\r\n"
        "Content-Type: text/html; charset=utf-8\r\n"
        "\r\n"
        "<p>Hello <b>html</b></p>\r\n",
    )
    text = listing_body(path)
    assert "**html**" in text
    assert "<b>" not in text


def test_listing_body_drops_empty_html_table_chrome(tmp_path):
    path = tmp_path / "msg"
    _write(
        path,
        "From: a@example.org\r\n"
        "Content-Type: text/html; charset=utf-8\r\n"
        "\r\n"
        "<table><tr><td></td><td></td></tr>"
        "<tr><td></td><td></td></tr></table>"
        "<p>Real newsletter sentence about a PhD fair.</p>\r\n",
    )
    text = listing_body(path)
    assert "Real newsletter sentence" in text
    assert "| --- |" not in text


def test_listing_body_pipe_heavy_html_falls_back_to_strip(tmp_path):
    # Mimic layout-table newsletters: many empty cells + one sentence.
    cells = "".join("<tr>" + "<td></td>" * 8 + "</tr>" for _ in range(12))
    path = tmp_path / "msg"
    _write(
        path,
        "From: a@example.org\r\n"
        "Content-Type: text/html; charset=utf-8\r\n"
        "\r\n"
        f"<html><body><table>{cells}</table>"
        "<p>Meet universities at the PhD study fair.</p>"
        "</body></html>\r\n",
    )
    text = listing_body(path)
    assert "PhD study fair" in text
    assert text.count("|") < 5


def test_listing_body_omits_images_by_default(tmp_path):
    path = tmp_path / "msg"
    _write(
        path,
        "From: a@example.org\r\n"
        "Content-Type: text/html; charset=utf-8\r\n"
        "\r\n"
        '<p>Hi</p><img src="https://tracker.example/pixel.gif" alt="pixel">'
        '<img src="cid:image001.png@01D" alt="sig">\r\n',
    )
    text = listing_body(path)
    assert "pixel" not in text
    assert "cid:" not in text
    assert "Hi" in text


def test_listing_body_images_url_are_links_not_embeds(tmp_path):
    path = tmp_path / "msg"
    _write(
        path,
        "From: a@example.org\r\n"
        "Content-Type: text/html; charset=utf-8\r\n"
        "\r\n"
        '<p>Hi</p><img src="https://cdn.example/logo.png" alt="Logo">'
        '<img src="cid:image001.png@01D" alt="sig">\r\n',
    )
    text = listing_body(path, images="url")
    assert "[Logo](https://cdn.example/logo.png)" in text
    assert "![" not in text
    assert "cid:" not in text


def test_listing_body_truncates(tmp_path):
    path = tmp_path / "msg"
    _write(path, "From: a@example.org\r\n\r\n" + ("x" * 50))
    text = listing_body(path, limit=20)
    assert text.endswith("…")
    assert len(text) <= 22


def test_listing_body_collapses_blank_lines(tmp_path):
    path = tmp_path / "msg"
    _write(
        path,
        "From: a@example.org\r\n"
        "Content-Type: text/html; charset=utf-8\r\n"
        "\r\n"
        "<div>Hello&nbsp;there</div><div><br></div><div><br></div>"
        "<div>Next</div>\r\n",
    )
    text = listing_body(path)
    assert "Hello there" in text
    assert "\n\n\n" not in text


def test_listing_body_deep_html_does_not_raise(tmp_path, monkeypatch):
    path = tmp_path / "msg"
    _write(
        path,
        "From: a@example.org\r\n"
        "Content-Type: text/html; charset=utf-8\r\n"
        "\r\n"
        "<p>Still readable</p>\r\n",
    )

    def boom(html, **args):
        raise RecursionError("nested")

    monkeypatch.setattr("lynguine_maildir.body.html2markdown", boom)
    text = listing_body(path)
    assert "Still readable" in text


def test_listing_body_missing_is_empty(tmp_path):
    assert listing_body(tmp_path / "nope") == ""
    assert listing_body("") == ""


def test_maildir_rejects_bad_body_images(tmp_path):
    root = _maildir(tmp_path / "INBOX")
    with pytest.raises(ValueError, match="body_images"):
        read_maildir({"path": str(root), "body_images": "embed"})


def test_maildir_row_includes_body(tmp_path):
    root = _maildir(tmp_path / "INBOX")
    _write(
        root / "cur" / "1.hostname:2,S",
        "Subject: Seen\r\n"
        "From: a@example.org\r\n"
        "Date: Fri, 30 Oct 2026 12:00:00 +0000\r\n"
        "Message-ID: <seen@ex>\r\n"
        "\r\n"
        "The body is here.\r\n",
    )
    df = read_maildir({"path": str(root)})
    assert "The body is here." in df.loc[0, "body"]
    assert df.loc[0, "path"].endswith("1.hostname:2,S")
