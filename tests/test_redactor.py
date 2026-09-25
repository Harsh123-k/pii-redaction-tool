"""Automated test cases for redaction engine and synthetic substitution."""

import pytest
from src.pii_detector import PIIDetector
from src.redactor import Redactor
from src.replacement_generator import ReplacementGenerator


class TestRedactor:
    """Validate synthetic substitution, consistency, and anti-collision behavior."""

    def test_consistent_replacement(self, redactor: Redactor):
        """Repeated mentions of the same PII must be replaced with the exact same synthetic value."""
        text = "Ticket from John Doe. Later, John Doe confirmed receipt of email john.doe@example.com."
        result = redactor.redact_text(text)

        # There should be only one distinct replacement for "John Doe"
        john_replacements = set()
        for ent in result.entities:
            if ent["text"] == "John Doe":
                val = redactor.generator.get_replacement(ent["type"], ent["text"])
                john_replacements.add(val)

        assert len(john_replacements) == 1
        assert "John Doe" not in result.redacted_text

    def test_anti_collision_guarantee(self, redactor: Redactor):
        """Synthetic replacement must never equal or contain the original sensitive PII value."""
        samples = [
            ("PERSON", "Alice Smith"),
            ("EMAIL", "alice.smith@domain.com"),
            ("PHONE", "+1 555-123-4567"),
            ("COMPANY", "Global Enterprise Ltd."),
            ("SSN", "123-45-6789"),
            ("CREDIT_CARD", "4111 1111 1111 1111"),
        ]

        for pii_type, original_val in samples:
            replacement = redactor.generator.get_replacement(pii_type, original_val)
            assert replacement.strip().lower() != original_val.strip().lower()
            assert original_val.lower() not in replacement.lower()

    def test_redaction_result_metadata(self, redactor: Redactor):
        """Redaction result must provide total count and per-category breakdown."""
        text = "Contact Alice at alice@example.com or phone +1 (555) 123-4567."
        res = redactor.redact_text(text)

        assert res.total_detected >= 2
        assert "EMAIL" in res.breakdown
        assert isinstance(res.redacted_text, str)
        assert "alice@example.com" not in res.redacted_text
