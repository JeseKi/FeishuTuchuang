# -*- coding: utf-8 -*-
"""SMTP mail mock service."""

from __future__ import annotations

import threading
from email import message_from_bytes
from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from socketserver import BaseRequestHandler, ThreadingTCPServer
from typing import ClassVar, cast
from urllib.parse import parse_qs, urlparse

from src.server.providers.constants import PROVIDER_MAIL
from src.server.providers.mock_server import (
    RunningMockService,
    send_html,
    server_host_port,
)


def _parse_smtp_path(value: str) -> str:
    if ":" in value:
        value = value.split(":", 1)[1].strip()
    if value.startswith("<") and ">" in value:
        return value[1 : value.index(">")]
    return value


class MailMockServer(ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True

    messages: ClassVar[list[tuple[str, list[str], bytes]]] = []


class MailSMTPHandler(BaseRequestHandler):
    def handle(self) -> None:
        server = cast(MailMockServer, self.server)
        reader = self.request.makefile("rb")
        writer = self.request.makefile("wb")
        mailfrom = ""
        rcpttos: list[str] = []

        def send_line(line: str) -> None:
            writer.write(f"{line}\r\n".encode("utf-8"))
            writer.flush()

        send_line("220 mock-mail ESMTP ready")

        while raw_line := reader.readline():
            line = raw_line.decode("utf-8", errors="replace").rstrip("\r\n")
            if not line:
                send_line("500 empty command")
                continue

            command, _, rest = line.partition(" ")
            command = command.upper()

            if command in {"EHLO", "HELO"}:
                send_line("250-mock-mail")
                send_line("250 8BITMIME")
                continue
            if command == "MAIL":
                mailfrom = _parse_smtp_path(rest)
                rcpttos = []
                send_line("250 OK")
                continue
            if command == "RCPT":
                rcpttos.append(_parse_smtp_path(rest))
                send_line("250 OK")
                continue
            if command == "DATA":
                chunks: list[bytes] = []
                send_line("354 End data with <CR><LF>.<CR><LF>")
                while data_line := reader.readline():
                    data_line = data_line.rstrip(b"\r\n")
                    if data_line == b".":
                        break
                    if data_line.startswith(b".."):
                        data_line = data_line[1:]
                    chunks.append(data_line)
                raw_data = b"\n".join(chunks)
                server.messages.append((mailfrom, list(rcpttos), raw_data))
                print(
                    f"[mock-mail] accepted message from={mailfrom} "
                    f"to={','.join(rcpttos)}"
                )
                send_line("250 OK")
                continue
            if command == "RSET":
                mailfrom = ""
                rcpttos = []
                send_line("250 OK")
                continue
            if command == "NOOP":
                send_line("250 OK")
                continue
            if command == "QUIT":
                send_line("221 Bye")
                break

            send_line("502 Command not implemented")


class MailInboxHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self._render_inbox()
            return
        if parsed.path == "/messages":
            self._render_inbox()
            return
        if parsed.path == "/messages/view":
            query = parse_qs(parsed.query)
            raw_index = query.get("index", [""])[0]
            if not raw_index.isdigit():
                self.send_error(404)
                return
            self._render_message(int(raw_index))
            return
        self.send_error(404)

    def log_message(self, format: str, *args) -> None:
        print(f"[mock-mail-ui] {self.address_string()} - {format % args}")

    def _render_inbox(self) -> None:
        rows = []
        for index, (mailfrom, rcpttos, raw_data) in enumerate(MailMockServer.messages):
            message = message_from_bytes(raw_data)
            subject = message.get("Subject", "(no subject)")
            rows.append(
                "<tr>"
                f"<td>{index + 1}</td>"
                f"<td>{escape(mailfrom)}</td>"
                f"<td>{escape(', '.join(rcpttos))}</td>"
                f"<td><a href='/messages/view?index={index}'>{escape(subject)}</a></td>"
                "</tr>"
            )
        table_body = "".join(rows) or "<tr><td colspan='4' class='muted'>暂无邮件</td></tr>"
        send_html(
            self,
            title="Mock Mail Inbox",
            body=f"""
            <h1>Mock Mail Inbox</h1>
            <p class="muted">邮件仅保存在当前 mock service 进程内存中。</p>
            <table>
              <thead><tr><th>#</th><th>From</th><th>To</th><th>Subject</th></tr></thead>
              <tbody>{table_body}</tbody>
            </table>
            """,
        )

    def _render_message(self, index: int) -> None:
        if index < 0 or index >= len(MailMockServer.messages):
            self.send_error(404)
            return
        mailfrom, rcpttos, raw_data = MailMockServer.messages[index]
        message = message_from_bytes(raw_data)
        payload = message.get_payload(decode=True)
        body = payload.decode("utf-8", errors="replace") if isinstance(payload, bytes) else str(message.get_payload())
        headers = "\n".join(f"{key}: {value}" for key, value in message.items())
        send_html(
            self,
            title=f"Mock Mail #{index + 1}",
            body=f"""
            <h1>{escape(message.get("Subject", "(no subject)"))}</h1>
            <p><a href="/messages">返回收件箱</a></p>
            <p><strong>From:</strong> {escape(mailfrom)}</p>
            <p><strong>To:</strong> {escape(', '.join(rcpttos))}</p>
            <h2>Headers</h2>
            <pre>{escape(headers)}</pre>
            <h2>Body</h2>
            <pre>{escape(body)}</pre>
            """,
        )


def start() -> RunningMockService:
    MailMockServer.messages = []
    server = MailMockServer(("127.0.0.1", 0), MailSMTPHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server_host_port(server)
    inbox_server = ThreadingHTTPServer(("127.0.0.1", 0), MailInboxHandler)
    inbox_thread = threading.Thread(target=inbox_server.serve_forever, daemon=True)
    inbox_thread.start()
    inbox_host, inbox_port = server_host_port(inbox_server)
    inbox_url = f"http://{inbox_host}:{inbox_port}/messages"

    def _shutdown() -> None:
        server.shutdown()
        server.server_close()
        inbox_server.shutdown()
        inbox_server.server_close()

    return RunningMockService(
        provider_key=PROVIDER_MAIL,
        name="SMTP Mail",
        config={
            "smtp_host": host,
            "smtp_port": port,
            "use_ssl": False,
            "use_tls": False,
            "sender_email": "mock-sender@example.com",
            "sender_password": "",
            "sender_name": "Mock Mail",
            "inbox_url": inbox_url,
        },
        shutdown=_shutdown,
    )
