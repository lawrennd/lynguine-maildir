"""In-process IMAP stand-in. No sockets."""


def header_bytes(
    subject="Hello",
    from_addr="a@example.org",
    date="Fri, 30 Oct 2026 12:00:00 +0000",
    message_id="<m1@example.org>",
):
    return (
        f"Subject: {subject}\r\n"
        f"From: {from_addr}\r\n"
        f"Date: {date}\r\n"
        f"Message-ID: {message_id}\r\n"
        "\r\n"
    ).encode("utf-8")


class FakeIMAP:
    def __init__(self, messages=None, select_status="OK", search_status="OK"):
        self.messages = dict(messages or {})
        self.select_status = select_status
        self.search_status = search_status
        self.selected = None
        self.readonly = None
        self.logged_out = False
        self.fetch_specs = []
        self.login_calls = []

    def login(self, user, password):
        self.login_calls.append((user, password))
        return "OK", [b"Logged in"]

    def select(self, folder, readonly=False):
        self.selected = folder
        self.readonly = readonly
        return self.select_status, [b"0"]

    def uid(self, command, *args):
        command = command.upper()
        if command == "SEARCH":
            if self.search_status != "OK":
                return self.search_status, [None]
            uids = " ".join(self.messages)
            return "OK", [uids.encode("ascii")]
        if command == "FETCH":
            uid = args[0]
            spec = args[1]
            self.fetch_specs.append(spec)
            text = uid.decode("ascii") if isinstance(uid, bytes) else str(uid)
            payload = self.messages[text]
            meta = (
                f"1 (UID {text} BODY[HEADER.FIELDS "
                f"(SUBJECT FROM DATE MESSAGE-ID)] {{{len(payload)}}}"
            ).encode("ascii")
            return "OK", [(meta, payload), b")"]
        raise AssertionError(f"unexpected UID command {command}")

    def logout(self):
        self.logged_out = True
        return "BYE", []
