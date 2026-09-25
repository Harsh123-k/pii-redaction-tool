"""Automated test cases for false-positive prevention:
- Ticket IDs, Order IDs, and Invoice IDs
- Infrastructure subnet masks and loopback IPs
- Software versions
- Non-DOB operational timestamps and event dates
- Support system keywords and labels
"""

import pytest
from src.pii_detector import PIIDetector


class TestFalsePositives:
    """Ensure non-PII operational identifiers and system keywords are never flagged as PII."""

    def test_ticketing_identifiers_not_detected(self, detector: PIIDetector):
        """Ticket IDs, order IDs, invoice IDs, and employee IDs must not be detected as PII."""
        text = (
            "Ticket ID: TKT-1023 | Priority: High | Queue: Enterprise Billing\n"
            "Reference Order ID ORD-123456 with Invoice INV-2026-1001.\n"
            "Actioned by Employee EMP12345 for incident INC-99104 and Case CASE-4421."
        )
        entities = detector.detect(text)
        detected_texts = [e["text"] for e in entities]

        forbidden = [
            "TKT-1023",
            "ORD-123456",
            "INV-2026-1001",
            "EMP12345",
            "INC-99104",
            "CASE-4421",
        ]
        for term in forbidden:
            assert not any(term in d for d in detected_texts), f"False positive: '{term}' detected as PII"

    def test_infrastructure_ips_ignored(self, detector: PIIDetector):
        """Standard network infrastructure IPs (loopback, subnet masks, wildcards) must be ignored."""
        text = "Subnet mask 255.255.255.0, loopback 127.0.0.1, and broadcast 255.255.255.255."
        entities = detector.detect(text)
        ip_entities = [e for e in entities if e["type"] == "IP_ADDRESS"]
        assert len(ip_entities) == 0, f"Infrastructure IPs wrongly detected: {ip_entities}"

    def test_version_numbers_ignored(self, detector: PIIDetector):
        """Software release versions formatted like IPv4 should not be detected as IPs."""
        text = "Application updated to version 1.2.3.4 and patch v2.1.0.4 installed."
        entities = detector.detect(text)
        ip_entities = [e for e in entities if e["type"] == "IP_ADDRESS"]
        assert len(ip_entities) == 0, f"Version numbers wrongly detected as IPs: {ip_entities}"

    def test_non_dob_dates_ignored(self, detector: PIIDetector):
        """Ordinary operational dates (ticket creation, review, invoice dates) must not be flagged as DOB."""
        text = (
            "Ticket created on 14/03/2026. "
            "Invoice dated 2026-05-12. "
            "Next review scheduled for 01/09/2026. "
            "System Release Date: 12 May 2024."
        )
        entities = detector.detect(text)
        dob_entities = [e for e in entities if e["type"] == "DOB"]
        assert len(dob_entities) == 0, f"Operational dates wrongly flagged as DOB: {dob_entities}"

    def test_invalid_credit_cards_ignored(self, detector: PIIDetector):
        """Invalid card numbers or dummy values marked as invalid must not be flagged as CREDIT_CARD."""
        text = "Non-PII test IP 999.300.1.2 and invalid card 4111 1111 1111 1112 were ignored."
        entities = detector.detect(text)
        cc_entities = [e for e in entities if e["type"] == "CREDIT_CARD"]
        assert len(cc_entities) == 0, f"Invalid card wrongly detected: {cc_entities}"

    def test_support_keywords_not_flagged_as_companies(self, detector: PIIDetector):
        """Common support, department, and infrastructure terms must not be detected as COMPANY."""
        text = "Priority: Critical | Status: Escalated | Department: Customer Support | Queue: Billing."
        entities = detector.detect(text)
        company_entities = [e for e in entities if e["type"] == "COMPANY"]
        assert len(company_entities) == 0, f"Keywords wrongly detected as COMPANY: {company_entities}"
