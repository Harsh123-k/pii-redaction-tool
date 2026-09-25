"""Automated test cases for all 9 required PII types:
1. PERSON
2. EMAIL
3. PHONE
4. COMPANY
5. ADDRESS
6. SSN
7. CREDIT_CARD
8. DOB
9. IP_ADDRESS
"""

import pytest
from src.pii_detector import PIIDetector


class TestPIIDetectorEntities:
    """Validate detection accuracy for each of the 9 required PII entity types."""

    def test_detect_emails(self, detector: PIIDetector):
        """Test detection of various valid email formats."""
        text = (
            "Contact user at john.doe@example.com or support-team_01@sub.domain.org. "
            "Also alert ADMIN@CORPORATION.NET."
        )
        entities = detector.detect(text)
        email_entities = [e for e in entities if e["type"] == "EMAIL"]
        email_texts = [e["text"] for e in email_entities]

        assert "john.doe@example.com" in email_texts
        assert "support-team_01@sub.domain.org" in email_texts
        assert "ADMIN@CORPORATION.NET" in email_texts

    def test_detect_ssns(self, detector: PIIDetector):
        """Test detection of US Social Security Numbers and exclusion of invalid area codes."""
        text = "Taxpayer SSN is 123-45-6789 and secondary is 456-78-1234. Non-SSN 000-12-3456 and 666-12-3456."
        entities = detector.detect(text)
        ssn_entities = [e for e in entities if e["type"] == "SSN"]
        ssn_texts = [e["text"] for e in ssn_entities]

        assert "123-45-6789" in ssn_texts
        assert "456-78-1234" in ssn_texts
        assert "000-12-3456" not in ssn_texts
        assert "666-12-3456" not in ssn_texts

    def test_detect_credit_cards(self, detector: PIIDetector):
        """Test detection of valid credit card formats (Visa/Mastercard, Amex)."""
        text = (
            "Client card is 4111 1111 1111 1111. "
            "Corporate Amex: 3782 8224 6310 005. "
            "Active Card: 5555 4444 3333 2222."
        )
        entities = detector.detect(text)
        cc_entities = [e for e in entities if e["type"] == "CREDIT_CARD"]
        cc_texts = [e["text"] for e in cc_entities]

        assert "4111 1111 1111 1111" in cc_texts
        assert "3782 8224 6310 005" in cc_texts
        assert "5555 4444 3333 2222" in cc_texts

    def test_detect_ips(self, detector: PIIDetector):
        """Test detection of valid client and server IPv4 addresses."""
        text = "Host 192.168.1.10 and server 10.0.4.15 and public gateway 172.16.254.1 connected."
        entities = detector.detect(text)
        ip_entities = [e for e in entities if e["type"] == "IP_ADDRESS"]
        ip_texts = [e["text"] for e in ip_entities]

        assert "192.168.1.10" in ip_texts
        assert "10.0.4.15" in ip_texts
        assert "172.16.254.1" in ip_texts

    def test_detect_phones(self, detector: PIIDetector):
        """Test detection of Indian and North American phone number formats."""
        text = (
            "Indian mobile: +91 9876543210 or 9876543210. "
            "US direct line: +1 (555) 019-2831 and office: (555) 123-4567."
        )
        entities = detector.detect(text)
        phone_entities = [e for e in entities if e["type"] == "PHONE"]
        phone_texts = [e["text"] for e in phone_entities]

        assert any("+91 9876543210" in p or "9876543210" in p for p in phone_texts)
        assert any("+1 (555) 019-2831" in p for p in phone_texts)
        assert any("(555) 123-4567" in p for p in phone_texts)

    def test_detect_dobs(self, detector: PIIDetector):
        """Test context-aware detection of Dates of Birth in various formatting styles."""
        text = (
            "Customer DOB: 12/05/1990. "
            "Date of Birth: 1985-08-22. "
            "User Born on: 15/08/2002."
        )
        entities = detector.detect(text)
        dob_entities = [e for e in entities if e["type"] == "DOB"]
        dob_texts = [e["text"] for e in dob_entities]

        assert "12/05/1990" in dob_texts
        assert "1985-08-22" in dob_texts
        assert "15/08/2002" in dob_texts

    def test_detect_addresses(self, detector: PIIDetector):
        """Test detection of structured physical addresses in both US and international layouts."""
        text = (
            "Mailing Address: 123 Main Street, Suite 400, Seattle, WA 98101.\n"
            "Branch: 42 Park Avenue, Mumbai, Maharashtra 400001.\n"
            "Office Address: 15 Maple Street, Apt 4B, Seattle, WA 98101."
        )
        entities = detector.detect(text)
        addr_entities = [e for e in entities if e["type"] == "ADDRESS"]
        addr_texts = [e["text"] for e in addr_entities]

        assert "123 Main Street, Suite 400, Seattle, WA 98101" in addr_texts
        assert "42 Park Avenue, Mumbai, Maharashtra 400001" in addr_texts
        assert "15 Maple Street, Apt 4B, Seattle, WA 98101" in addr_texts

    def test_detect_companies(self, detector: PIIDetector):
        """Test detection of company and organization names."""
        text = (
            "Company: Acme Corporation.\n"
            "Organization: Global Technologies Ltd.\n"
            "Employer: Microsoft Corporation."
        )
        entities = detector.detect(text)
        comp_entities = [e for e in entities if e["type"] == "COMPANY"]
        comp_texts = [e["text"] for e in comp_entities]

        assert "Acme Corporation" in comp_texts
        assert "Global Technologies Ltd." in comp_texts
        assert "Microsoft Corporation" in comp_texts

    def test_detect_persons(self, detector: PIIDetector):
        """Test detection of person names with role prefix stripping."""
        text = (
            "Customer Name: John Doe submitted the ticket. "
            "Client: Rashmi Patil verified identity. "
            "Requester: Alex Mercer requested firewall change."
        )
        entities = detector.detect(text)
        person_entities = [e for e in entities if e["type"] == "PERSON"]
        person_texts = [e["text"] for e in person_entities]

        assert "John Doe" in person_texts
        assert "Rashmi Patil" in person_texts
        assert "Alex Mercer" in person_texts
