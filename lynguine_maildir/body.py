"""Listing body from a Maildir message file.

Required IO columns stay headers. ``body`` prefers ``text/plain`` when
present (readable for units/LLM), else HTML→markdown. Outlook Safe Links
are unwrapped; images omitted unless ``body_images: url``.
"""

from __future__ import annotations

import html as html_lib
import re
from email import policy
from email.parser import BytesParser
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from lynguine.util.misc import html2markdown

BODY_LIMIT = 8000
BODY_IMAGES = ("omit", "url")
_BLANK = re.compile(r"\n{3,}")
_BLOCK = re.compile(r"(?is)<(script|style).*?>.*?</\1>")
_TAG = re.compile(r"<[^>]+>", re.DOTALL)
_BR = re.compile(r"(?i)<br\s*/?>")
_P = re.compile(r"(?i)</p>")
_DIV = re.compile(r"(?i)</div>")
_SAFE_LINK = re.compile(
    r"https?://[^\s\"'<>)\]]*?safelinks\.protection\.outlook\.com/\?[^\s\"'<>)\]]*",
    re.IGNORECASE,
)
_MD_IMAGE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
# Markdown table scaffolding from HTML email layouts (empty cells / rules).
_TABLE_CHROME_LINE = re.compile(r"^[\s|:\-]+$")


def listing_body(
    path: str | Path,
    *,
    limit: int = BODY_LIMIT,
    images: str = "omit",
) -> str:
    """Return truncated markdown for listing ``display.detail_field``."""
    images = _normalise_images(images)
    if not path:
        return ""
    file = Path(path)
    if not file.is_file():
        return ""
    try:
        with file.open("rb") as handle:
            message = BytesParser(policy=policy.default).parse(handle)
    except (OSError, ValueError):
        return ""
    text = _finish(_message_markdown(message), images=images)
    if limit and len(text) > limit:
        return text[:limit].rstrip() + "\n…"
    return text


plain_body = listing_body


def unwrap_safe_links(text: str) -> str:
    """Replace Outlook Safe Link URLs with the wrapped target."""
    if not text:
        return ""
    return _SAFE_LINK.sub(lambda match: unwrap_safe_link(match.group(0)), text)


def unwrap_safe_link(url: str) -> str:
    """Return the ``url=`` target from a Safe Link, or *url* unchanged."""
    candidate = url.strip().rstrip(".,;:>)")
    try:
        parsed = urlparse(candidate)
    except ValueError:
        return url
    host = (parsed.netloc or "").lower()
    if "safelinks.protection.outlook.com" not in host:
        return url
    raw = parse_qs(parsed.query).get("url") or parse_qs(parsed.query).get("URL")
    if not raw or not raw[0]:
        return url
    return unquote(raw[0])


def body_images_option(details: dict, *, type_name: str) -> str:
    raw = details.get("body_images", "omit")
    if raw is None:
        return "omit"
    if raw not in BODY_IMAGES:
        raise ValueError(
            f'Type "{type_name}" body_images: must be omit or url'
        )
    return raw


def _normalise_images(images: str) -> str:
    if images not in BODY_IMAGES:
        return "omit"
    return images


def _message_markdown(message) -> str:
    # Prefer text/plain when present. Multipart HTML newsletters often
    # markdownify into empty table chrome (| --- |) that is useless for
    # listing, paragraph units, and LLM extract — while the plain part
    # is the readable body. Fall back to HTML when there is no plain part.
    plain = _part_by_type(message, "text/plain")
    if plain.strip():
        return plain
    html = _part_by_type(message, "text/html")
    if html.strip():
        return _html_to_markdown(html)
    return ""


def _iter_parts(message):
    if message.is_multipart():
        yield from message.walk()
        return
    yield message


def _part_by_type(message, content_type: str) -> str:
    for item in _iter_parts(message):
        if item.get_content_type() == content_type:
            return _part_payload(item)
    return ""


def _part_payload(part) -> str:
    try:
        content = part.get_content()
    except (KeyError, LookupError, TypeError, ValueError):
        payload = part.get_payload(decode=True)
        if isinstance(payload, bytes):
            content = payload.decode("utf-8", errors="replace")
        else:
            content = payload or ""
    if isinstance(content, bytes):
        content = content.decode("utf-8", errors="replace")
    return str(content or "")


def _html_to_markdown(raw: str) -> str:
    cleaned = _BLOCK.sub(" ", raw)
    try:
        md = html2markdown(cleaned)
    except (RecursionError, TypeError, ValueError):
        return _strip_tags(cleaned)
    # Newsletter/layout HTML often becomes empty markdown tables with the
    # real sentences glued onto chrome lines. Prefer tag-stripped prose.
    if _markdown_is_pipe_heavy(md):
        return _strip_tags(cleaned)
    return md


def _markdown_is_pipe_heavy(text: str) -> bool:
    if not text or "|" not in text:
        return False
    pipes = text.count("|")
    return pipes > 20 and pipes > len(text) / 30


def _strip_tags(raw: str) -> str:
    raw = _BR.sub("\n", raw)
    raw = _P.sub("\n\n", raw)
    raw = _DIV.sub("\n", raw)
    return html_lib.unescape(_TAG.sub("", raw))


def _rewrite_images(text: str, *, images: str) -> str:
    def repl(match: re.Match[str]) -> str:
        alt = match.group(1).strip() or "image"
        src = unwrap_safe_link(match.group(2).strip())
        if images == "omit":
            return ""
        if src.lower().startswith(("http://", "https://")):
            return f"[{alt}]({src})"
        return ""

    return _MD_IMAGE.sub(repl, text)


def _finish(text: str, *, images: str) -> str:
    text = unwrap_safe_links(text)
    text = _rewrite_images(text, images=images)
    text = _drop_table_chrome(text)
    return _normalise_text(text)


def _drop_table_chrome(text: str) -> str:
    """Remove markdown table rule/empty-cell lines from HTML→markdown."""
    if not text or "|" not in text:
        return text
    kept: list[str] = []
    for line in text.split("\n"):
        if _TABLE_CHROME_LINE.match(line):
            continue
        kept.append(line)
    return "\n".join(kept)


def _normalise_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\xa0", " ")
    text = "\n".join(line.rstrip() for line in text.split("\n"))
    return _BLANK.sub("\n\n", text).strip()
