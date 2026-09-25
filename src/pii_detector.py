"""Hybrid PII Detector combining deterministic regex rules, validation, and spaCy NER."""

import logging
import re
from typing import Any, Dict, List, Optional

from src.config import (
    DEFAULT_CONFIDENCE,
    ENTITY_PRIORITY,
    SUPPORTED_PII_TYPES,
)
from src.ner_detector import NERDetector
from src.pii_patterns import (
    COMPANY_REGEX,
    CREDIT_CARD_REGEX,
    DATE_PATTERNS,
    DOB_KEYWORD_REGEX,
    EMAIL_REGEX,
    IPV4_REGEX,
    PHONE_PATTERNS,
    PHYSICAL_ADDRESS_REGEX,
    SSN_REGEX,
    is_network_infrastructure_ip,
    is_ticketing_identifier,
    luhn_checksum,
)

logger = logging.getLogger(__name__)


class PIIDetector:
    """Master PII Detector employing hybrid detection (Regex + NER) with overlap resolution."""

    def __init__(self, ner_detector: Optional[NERDetector] = None) -> None:
        """Initialize detector with an optional pre-configured NERDetector instance."""
        self.ner_detector = ner_detector or NERDetector()

    def detect_emails(self, text: str) -> List[Dict[str, Any]]:
        """Detect email addresses via regex."""
        results: List[Dict[str, Any]] = []
        for match in EMAIL_REGEX.finditer(text):
            val = match.group(0).strip(".,;:!?")
            start = match.start()
            end = start + len(val)
            results.append(
                {
                    "type": "EMAIL",
                    "text": val,
                    "start": start,
                    "end": end,
                    "confidence": DEFAULT_CONFIDENCE["EMAIL"],
                    "detector": "regex",
                }
            )
        return results

    def detect_ssns(self, text: str) -> List[Dict[str, Any]]:
        """Detect US Social Security Numbers with area and group code validation."""
        results: List[Dict[str, Any]] = []
        for match in SSN_REGEX.finditer(text):
            val = match.group(0)
            start, end = match.span()
            results.append(
                {
                    "type": "SSN",
                    "text": val,
                    "start": start,
                    "end": end,
                    "confidence": DEFAULT_CONFIDENCE["SSN"],
                    "detector": "regex",
                }
            )
        return results

    def detect_credit_cards(self, text: str) -> List[Dict[str, Any]]:
        """Detect credit card numbers verified via Luhn algorithm or contextual indicators."""
        results: List[Dict[str, Any]] = []
        for match in CREDIT_CARD_REGEX.finditer(text):
            candidate = match.group(0).strip()
            start, end = match.span()
            prefix = text[max(0, start - 30) : start].lower()

            # Ignore if explicitly indicated as invalid, dummy, or test card
            if any(neg in prefix for neg in ["invalid", "fake", "test", "dummy"]):
                continue

            is_luhn = luhn_checksum(candidate)
            is_card_kw = any(kw in prefix for kw in ["card", "credit", "cc"])

            if is_luhn or is_card_kw:
                # Verify candidate is not surrounded by ticket identifier prefixes
                if any(k in prefix[-5:] for k in ["tkt", "ord", "inv", "emp", "inc"]):
                    continue
                results.append(
                    {
                        "type": "CREDIT_CARD",
                        "text": candidate,
                        "start": start,
                        "end": end,
                        "confidence": DEFAULT_CONFIDENCE["CREDIT_CARD"],
                        "detector": "regex_card",
                    }
                )
        return results

    def detect_companies(self, text: str) -> List[Dict[str, Any]]:
        """Detect corporate names with legal suffixes via regex."""
        results: List[Dict[str, Any]] = []
        for match in COMPANY_REGEX.finditer(text):
            val = match.group(0).rstrip(",;:!? ")
            if not val.endswith(("Ltd.", "Inc.", "Corp.", "Co.")):
                val = val.rstrip(".,;:!? ")
            start = match.start()
            end = start + len(val)
            results.append(
                {
                    "type": "COMPANY",
                    "text": val,
                    "start": start,
                    "end": end,
                    "confidence": DEFAULT_CONFIDENCE["COMPANY"],
                    "detector": "regex_company",
                }
            )
        return results

    def detect_ips(self, text: str) -> List[Dict[str, Any]]:
        """Detect valid IPv4 addresses excluding non-sensitive subnet masks."""
        results: List[Dict[str, Any]] = []
        for match in IPV4_REGEX.finditer(text):
            ip_str = match.group(0)
            start, end = match.span()

            # Ignore version numbers like "version 1.2.3.4" or "v2.1.0.4"
            prefix = text[max(0, start - 8) : start].lower()
            if "version" in prefix or prefix.endswith("v") or prefix.endswith("v."):
                continue

            # Ignore standard infrastructure / netmask IPs
            if is_network_infrastructure_ip(ip_str):
                continue

            results.append(
                {
                    "type": "IP_ADDRESS",
                    "text": ip_str,
                    "start": start,
                    "end": end,
                    "confidence": DEFAULT_CONFIDENCE["IP_ADDRESS"],
                    "detector": "regex",
                }
            )
        return results

    def detect_phones(self, text: str) -> List[Dict[str, Any]]:
        """Detect Indian and international phone numbers, filtering out ticket IDs."""
        results: List[Dict[str, Any]] = []
        seen_spans = set()

        for pattern in PHONE_PATTERNS:
            for match in pattern.finditer(text):
                val = match.group(0).strip(".,;:!? ")
                start = match.start()
                end = start + len(val)

                # Skip if already captured
                if (start, end) in seen_spans:
                    continue

                # Ensure minimum digits
                digits = re.sub(r"\D", "", val)
                if len(digits) < 10 or len(digits) > 15:
                    continue

                # Ensure it's not a ticketing/order ID (e.g. ORD-9876543210)
                prefix = text[max(0, start - 5) : start]
                if any(k in prefix for k in ["TKT", "ORD", "INV", "EMP", "INC", "CASE"]):
                    continue

                seen_spans.add((start, end))
                results.append(
                    {
                        "type": "PHONE",
                        "text": val,
                        "start": start,
                        "end": end,
                        "confidence": DEFAULT_CONFIDENCE["PHONE"],
                        "detector": "regex",
                    }
                )
        return results

    def detect_dobs(self, text: str) -> List[Dict[str, Any]]:
        """Detect Dates of Birth using context-aware inspection.

        Ordinary dates (e.g. ticket creation, invoice dates) are ignored unless
        accompanied by birth-related keywords.
        """
        results: List[Dict[str, Any]] = []
        seen_spans = set()

        for pattern in DATE_PATTERNS:
            for match in pattern.finditer(text):
                date_val = match.group(0).strip(".,;:!?")
                start = match.start()
                end = start + len(date_val)

                if (start, end) in seen_spans:
                    continue

                # Look for birth context in preceding 40 characters or following 20 characters
                preceding = text[max(0, start - 40) : start].lower()
                following = text[end : min(len(text), end + 20)].lower()

                has_dob_context = bool(
                    DOB_KEYWORD_REGEX.search(preceding) or DOB_KEYWORD_REGEX.search(following)
                )

                if has_dob_context:
                    seen_spans.add((start, end))
                    results.append(
                        {
                            "type": "DOB",
                            "text": date_val,
                            "start": start,
                            "end": end,
                            "confidence": DEFAULT_CONFIDENCE["DOB"],
                            "detector": "regex_contextual",
                        }
                    )
        return results

    def detect_physical_addresses(self, text: str) -> List[Dict[str, Any]]:
        """Detect structured physical addresses matching street patterns."""
        results: List[Dict[str, Any]] = []
        for match in PHYSICAL_ADDRESS_REGEX.finditer(text):
            val = match.group(0).strip(".,;:!? ")
            start = match.start()
            end = start + len(val)
            results.append(
                {
                    "type": "ADDRESS",
                    "text": val,
                    "start": start,
                    "end": end,
                    "confidence": DEFAULT_CONFIDENCE["ADDRESS"],
                    "detector": "regex_address",
                }
            )
        return results

    def detect_all_raw(self, text: str) -> List[Dict[str, Any]]:
        """Run all rule-based and NER detectors without conflict resolution."""
        raw_detections: List[Dict[str, Any]] = []

        # 1. Rule-based structured detections
        raw_detections.extend(self.detect_emails(text))
        raw_detections.extend(self.detect_ssns(text))
        raw_detections.extend(self.detect_credit_cards(text))
        raw_detections.extend(self.detect_ips(text))
        raw_detections.extend(self.detect_phones(text))
        raw_detections.extend(self.detect_dobs(text))
        raw_detections.extend(self.detect_physical_addresses(text))
        raw_detections.extend(self.detect_companies(text))

        # 2. NER unstructured detections
        if self.ner_detector and self.ner_detector.is_available():
            ner_entities = self.ner_detector.detect(text)
            raw_detections.extend(ner_entities)

        return raw_detections

    def resolve_conflicts(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Resolve overlapping detection spans deterministically.

        Higher priority entity types (e.g. CREDIT_CARD, SSN, EMAIL, PHONE, ADDRESS) take
        precedence over broad NER spans (e.g. PERSON, COMPANY). If priorities
        match, higher confidence and longer span length win.

        Args:
            entities: Raw list of detected entity dictionaries.

        Returns:
            Sorted, non-overlapping list of entities.
        """
        if not entities:
            return []

        # Sort entities by start asc, priority desc, confidence desc, span length desc
        sorted_entities = sorted(
            entities,
            key=lambda e: (
                e["start"],
                -ENTITY_PRIORITY.get(e["type"], 0),
                -e.get("confidence", 0.0),
                -(e["end"] - e["start"]),
            ),
        )

        resolved: List[Dict[str, Any]] = []

        for candidate in sorted_entities:
            c_start = candidate["start"]
            c_end = candidate["end"]
            c_type = candidate["type"]
            c_prio = ENTITY_PRIORITY.get(c_type, 0)
            c_conf = candidate.get("confidence", 0.0)

            # Check overlap against already chosen entities
            overlap = False
            for i, prev in enumerate(resolved):
                p_start = prev["start"]
                p_end = prev["end"]
                p_type = prev["type"]
                p_prio = ENTITY_PRIORITY.get(p_type, 0)
                p_conf = prev.get("confidence", 0.0)

                # Overlap condition
                if not (c_end <= p_start or c_start >= p_end):
                    overlap = True
                    # If candidate has strictly higher priority, replace prev
                    if c_prio > p_prio:
                        resolved[i] = candidate
                        break
                    elif c_prio == p_prio and c_conf > p_conf:
                        resolved[i] = candidate
                        break
                    elif c_prio == p_prio and c_conf == p_conf and (c_end - c_start) > (p_end - p_start):
                        resolved[i] = candidate
                        break
                    else:
                        # Existing item retains priority; skip current candidate
                        break

            if not overlap and candidate not in resolved:
                resolved.append(candidate)

        # Final sort by start position
        resolved.sort(key=lambda e: e["start"])
        return resolved

    def detect(self, text: str) -> List[Dict[str, Any]]:
        """Run the full hybrid detection pipeline and return resolved PII entities.

        Args:
            text: Input text string.

        Returns:
            List of non-overlapping, high-confidence PII entities.
        """
        if not text or not text.strip():
            return []

        raw = self.detect_all_raw(text)
        return self.resolve_conflicts(raw)
