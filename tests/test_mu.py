"""mu reader tests fake the binary. No live index."""

from __future__ import annotations

import json
from pathlib import Path
from subprocess import CompletedProcess

import pandas as pd
import pytest

from lynguine.access.io import write_data
from lynguine.access.io_types import ReadOnlyIOTypeError, get_io_type

from lynguine_maildir.mu import read_mu
from lynguine_maildir.reader import COLUMNS

SAMPLE_PATH = (
    "/tmp/Maildir/cam/INBOX/cur/"
    "1793607149_7.host,U=521910,FMD5=abc:2,S"
)
SAMPLE_HIT = {
    "path": SAMPLE_PATH,
    "subject": "Hello",
    "message-id": "<id@ex>",
    "from": [{"email": "a@example.org", "name": "Ada"}],
    "date-unix": 1793531510,
    "maildir": "/cam/INBOX",
}


def _run_ok(stdout: str, returncode: int = 0, stderr: str = ""):
    def run(argv, **kwargs):
        return CompletedProcess(argv, returncode, stdout=stdout, stderr=stderr)

    return run


def test_import_registers_mu():
    import lynguine_maildir

    spec = get_io_type("mu")
    assert spec is not None
    assert spec.name == "mu"
    assert spec.credential_type is None
    assert spec.write is None
    assert spec.read is lynguine_maildir.read_mu


def test_mu_write_is_read_only():
    import lynguine_maildir  # noqa: F401

    with pytest.raises(ReadOnlyIOTypeError, match="read-only"):
        write_data(pd.DataFrame(), {"type": "mu", "write": True, "query": "x"})


def test_read_mu_maps_json2(monkeypatch):
    captured = {}

    def run(argv, **kwargs):
        captured["argv"] = argv
        captured["kwargs"] = kwargs
        return CompletedProcess(
            argv, 0, stdout=json.dumps([SAMPLE_HIT]), stderr=""
        )

    monkeypatch.setattr("lynguine_maildir.mu.subprocess.run", run)
    df = read_mu({"query": "date:today", "limit": 7})
    assert list(df.columns)[:5] == COLUMNS
    assert "body" in df.columns
    assert df["uid"].tolist() == [
        "1793607149_7.host,U=521910,FMD5=abc"
    ]
    assert df["from"].tolist() == ["Ada <a@example.org>"]
    assert df["date"].tolist() == ["2026-11-01T11:11:50Z"]
    assert df["maildir"].tolist() == ["/cam/INBOX"]
    argv = captured["argv"]
    assert argv[:6] == [
        "mu",
        "find",
        "--format=json2",
        "--nocolor",
        "--sortfield=date",
        "--reverse",
    ]
    assert "--maxnum=7" in argv
    assert argv[-2:] == ["--", "date:today"]
    assert captured["kwargs"]["shell"] is False if "shell" in captured["kwargs"] else True
    assert captured["kwargs"].get("shell") in (False, None)


def test_read_mu_exit_2_empty(monkeypatch):
    monkeypatch.setattr(
        "lynguine_maildir.mu.subprocess.run",
        _run_ok("no matches for search expression\n", returncode=2),
    )
    df = read_mu({"query": "date:2w"})
    assert list(df.columns)[:5] == COLUMNS
    assert len(df) == 0


def test_read_mu_nonzero_includes_stderr(monkeypatch):
    monkeypatch.setattr(
        "lynguine_maildir.mu.subprocess.run",
        _run_ok("", returncode=1, stderr="database locked\n"),
    )
    with pytest.raises(ValueError, match="database locked"):
        read_mu({"query": "from:x"})


def test_read_mu_missing_binary(monkeypatch):
    def boom(*args, **kwargs):
        raise FileNotFoundError("mu")

    monkeypatch.setattr("lynguine_maildir.mu.subprocess.run", boom)
    with pytest.raises(ValueError, match="mu binary"):
        read_mu({"query": "from:x"})


@pytest.mark.parametrize(
    "details, match",
    [
        ({}, "query"),
        ({"query": "   "}, "query"),
        ({"query": "x", "credential": "k"}, "credential"),
        ({"query": "x", "path": "~/Maildir/INBOX"}, "path"),
        ({"query": "x", "limit": 0}, "limit"),
    ],
)
def test_read_mu_yaml_errors(details, match):
    with pytest.raises(ValueError, match=match):
        read_mu(details)


def test_read_mu_muhome_and_binary(monkeypatch, tmp_path):
    captured = {}

    def run(argv, **kwargs):
        captured["argv"] = argv
        return CompletedProcess(argv, 0, stdout="[]", stderr="")

    monkeypatch.setattr("lynguine_maildir.mu.subprocess.run", run)
    binary = tmp_path / "mu"
    muhome = tmp_path / "cache"
    read_mu(
        {
            "query": "flag:unread",
            "binary": str(binary),
            "muhome": str(muhome),
        }
    )
    argv = captured["argv"]
    assert argv[0] == str(binary)
    assert f"--muhome={muhome}" in argv
    assert argv[-1] == "flag:unread"
