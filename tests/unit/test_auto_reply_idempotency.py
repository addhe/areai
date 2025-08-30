#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest
from unittest.mock import MagicMock, patch

from functions.auto_reply.main import send_reply


class TestSendReplyIdempotency(unittest.TestCase):
    def make_fake_service(self):
        service = MagicMock()
        # Chain: service.users().messages().send(...).execute()
        service.users.return_value = service
        service.messages.return_value = service
        service.send.return_value = service
        service.execute.return_value = {"id": "sent123"}
        return service

    def test_send_reply_skips_when_already_labeled(self):
        service = self.make_fake_service()
        email_data = {
            "id": "orig123",
            "threadId": "thr123",
            "subject": "Test Subject",
            "reply_to": "sender@example.com",
        }
        with patch("functions.auto_reply.main.has_auto_reply_label", return_value=True):
            result = send_reply(service, email_data, "Hello")
            self.assertIsNone(result)
            # Ensure send is never called
            service.send.assert_not_called()

    def test_send_reply_sends_once_when_not_labeled(self):
        service = self.make_fake_service()
        email_data = {
            "id": "orig123",
            "threadId": "thr123",
            "subject": "Test Subject",
            "reply_to": "sender@example.com",
        }
        with patch("functions.auto_reply.main.has_auto_reply_label", return_value=False):
            result = send_reply(service, email_data, "Hello")
            self.assertEqual(result, "sent123")
            service.send.assert_called_once()


if __name__ == "__main__":
    unittest.main()
