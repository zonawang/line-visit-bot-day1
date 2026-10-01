"""Day 1 LINE visit assistant: signed webhook and safe, static FAQs."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import unicodedata
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


FAQ = json.loads(Path(__file__).with_name("faq.json").read_text(encoding="utf-8"))
MAX_BODY_BYTES = 1_000_000
REPLY_URL = "https://api.line.me/v2/bot/message/reply"


def normalize(text: str) -> str:
    return "".join(
        char for char in unicodedata.normalize("NFKC", text).lower() if not char.isspace()
    )


def answer(question: str) -> str:
    normalized = normalize(question)
    for item in FAQ["answers"]:
        if any(normalize(keyword) in normalized for keyword in item["keywords"]):
            return item["answer"]
    return FAQ["fallback"]


def is_for_bot(event: dict) -> bool:
    if event.get("type") != "message":
        return False
    message = event.get("message") or {}
    if message.get("type") != "text":
        return False
    source_type = (event.get("source") or {}).get("type")
    if source_type == "user":
        return True
    if source_type not in {"group", "room"}:
        return False
    mentionees = (message.get("mention") or {}).get("mentionees") or []
    return any(person.get("isSelf") is True for person in mentionees)


def answer_for_event(event: dict) -> str | None:
    if not is_for_bot(event):
        return None
    return answer(event["message"].get("text", ""))


def valid_signature(body: bytes, signature: str, secret: str) -> bool:
    if not signature or not secret:
        return False
    digest = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).digest()
    expected = base64.b64encode(digest).decode("ascii")
    return hmac.compare_digest(signature, expected)


def send_reply(reply_token: str, message: str, access_token: str) -> None:
    payload = json.dumps(
        {"replyToken": reply_token, "messages": [{"type": "text", "text": message}]},
        ensure_ascii=False,
    ).encode("utf-8")
    request = urllib.request.Request(
        REPLY_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=5):
        pass


class Handler(BaseHTTPRequestHandler):
    def respond(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self.path == "/ready":
            self.respond(200, {"status": "ok"})
        else:
            self.respond(404, {"error": "not_found"})

    def do_POST(self) -> None:
        if self.path != "/webhook":
            self.respond(404, {"error": "not_found"})
            return
        secret = os.environ.get("LINE_CHANNEL_SECRET", "")
        access_token = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "")
        if not secret or not access_token:
            self.respond(503, {"error": "not_configured"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self.respond(400, {"error": "invalid_length"})
            return
        if length < 0 or length > MAX_BODY_BYTES:
            self.respond(413, {"error": "invalid_length"})
            return
        body = self.rfile.read(length)
        signature = self.headers.get("X-Line-Signature", "")
        if not valid_signature(body, signature, secret):
            self.respond(401, {"error": "invalid_signature"})
            return
        try:
            events = json.loads(body).get("events", [])
            for event in events:
                response = answer_for_event(event)
                if response is not None and event.get("replyToken"):
                    send_reply(event["replyToken"], response, access_token)
        except (ValueError, TypeError, KeyError):
            self.respond(400, {"error": "invalid_payload"})
            return
        except urllib.error.HTTPError as error:
            self.log_error("LINE reply failed with HTTP %s", error.code)
            self.respond(502, {"error": "reply_failed"})
            return
        except urllib.error.URLError:
            self.log_error("LINE reply connection failed")
            self.respond(502, {"error": "reply_failed"})
            return
        self.respond(200, {"status": "ok"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()
