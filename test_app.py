import base64
import hashlib
import hmac
import unittest

from app import answer_for_event, valid_signature


def text_event(source, text, mention=None):
    message = {"type": "text", "text": text}
    if mention is not None:
        message["mention"] = {"mentionees": mention}
    return {"type": "message", "source": {"type": source}, "message": message}


class Day1Tests(unittest.TestCase):
    def test_signed_body(self):
        body = b'{"events":[]}'
        signature = base64.b64encode(hmac.new(b"secret", body, hashlib.sha256).digest()).decode()
        self.assertTrue(valid_signature(body, signature, "secret"))
        self.assertFalse(valid_signature(body + b" ", signature, "secret"))

    def test_group_only_replies_to_self_mention(self):
        self.assertIsNone(answer_for_event(text_event("group", "時間")))
        self.assertIsNone(
            answer_for_event(text_event("group", "時間", [{"type": "user", "isSelf": False}]))
        )
        self.assertIn(
            "尚未登錄",
            answer_for_event(text_event("group", "@Bot 時間", [{"type": "user", "isSelf": True}])),
        )

    def test_direct_message_can_ask_for_help(self):
        self.assertIn("企業參訪小幫手", answer_for_event(text_event("user", "功能")))

    def test_non_text_is_ignored(self):
        event = text_event("user", "功能")
        event["message"]["type"] = "image"
        self.assertIsNone(answer_for_event(event))


if __name__ == "__main__":
    unittest.main()
