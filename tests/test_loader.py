"""
tests/test_loader.py
~~~~~~~~~~~~~~~~~~~~
Unit tests for sqam_analyzer.loader.load_srs_from_json.
"""

import json
import tempfile
from pathlib import Path
import unittest

from sqam_analyzer.loader import load_srs_from_json


class TestSRSLoader(unittest.TestCase):
    def test_load_full_srs_object(self):
        data = {
            "document_title": "Custom Test System SRS",
            "domain_summary": "Domain test description",
            "glossary": {"TermA": "Definition A"},
            "applicable_standards": ["ISO 29148"],
            "surrounding_requirements": ["REQ-0: Background context"],
            "requirements": [
                {
                    "req_id": "REQ-001",
                    "text": "The system shall respond within 100ms.",
                    "req_type": "Performance",
                    "section": "3.1 Core",
                }
            ],
        }
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
            json.dump(data, f)
            temp_path = f.name

        try:
            context, reqs = load_srs_from_json(temp_path)
            self.assertEqual(context.document_title, "Custom Test System SRS")
            self.assertEqual(context.domain_summary, "Domain test description")
            self.assertEqual(context.glossary["TermA"], "Definition A")
            self.assertEqual(len(reqs), 1)
            self.assertEqual(reqs[0].req_id, "REQ-001")
            self.assertEqual(reqs[0].text, "The system shall respond within 100ms.")
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_load_simple_requirements_list(self):
        data = [
            {"req_id": "R1", "text": "The system shall encrypt all stored data."},
            {"id": "R2", "statement": "The UI shall render in less than 1 second."},
        ]
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
            json.dump(data, f)
            temp_path = f.name

        try:
            context, reqs = load_srs_from_json(temp_path)
            self.assertIn("SRS", context.document_title)
            self.assertEqual(len(reqs), 2)
            self.assertEqual(reqs[0].req_id, "R1")
            self.assertEqual(reqs[1].req_id, "R2")
            self.assertEqual(reqs[1].text, "The UI shall render in less than 1 second.")
        finally:
            Path(temp_path).unlink(missing_ok=True)
