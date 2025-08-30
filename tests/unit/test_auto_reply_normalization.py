#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

# Import the function under test
from functions.auto_reply.main import normalize_email_body


class TestEmailBodyNormalization(unittest.TestCase):
    def test_collapse_multiple_blank_lines(self):
        raw = (
            "Q1: Apa biaya admin?\n"
            "\n\n\n"  # 3 blank lines
            "Q2: Bagaimana cara ubah PIN?\n"
            "\n\n\n\n"  # 4 blank lines
            "Q3: Apakah ada promo?\n"
        )
        normalized = normalize_email_body(raw)
        # Expect maximum of two consecutive newlines
        self.assertIn("\n\n", normalized)
        self.assertNotIn("\n\n\n", normalized)
        # Should preserve content order
        self.assertTrue(normalized.startswith("Q1: Apa biaya admin?"))
        self.assertTrue(normalized.endswith("Q3: Apakah ada promo?"))

    def test_trim_space_only_lines(self):
        raw = "Line 1\n   \n\t\nLine 2\n"
        normalized = normalize_email_body(raw)
        # Space-only lines become truly blank, and collapse to at most two newlines
        self.assertIn("Line 1\n\nLine 2", normalized)
        self.assertNotIn("\n\n\n", normalized)


if __name__ == "__main__":
    unittest.main()
