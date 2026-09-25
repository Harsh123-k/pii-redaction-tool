"""Pattern definitions, regex matchers, and validation functions for structured PII."""

import re
from typing import Any, Dict, List, Optional, Pattern, Tuple


def luhn_checksum(candidate: str) -> bool:
    """Validate a candidate credit card number using the Luhn mod 10 algorithm.

    Args:
        candidate: String containing digits and optional spaces/dashes.

    Returns:
        True if the candidate has 13-19 digits, passes Luhn, and is not all the same digit.
    """
    clean_digits = re.sub(r"[ -]", "", candidate)
    if not clean_digits.isdigit():
        return False
    if len(clean_digits) < 13 or len(clean_digits) > 19:
        return False
    # Avoid numbers where every digit is identical (e.g. 0000 0000 0000 0000)
    if len(set(clean_digits)) == 1:
        return False

    digits = [int(c) for c in clean_digits]
    checksum = 0
    reverse_digits = digits[::-1]
    for i, digit in enumerate(reverse_digits):
        if i % 2 == 1:
            doubled = digit * 2
            checksum += doubled - 9 if doubled > 9 else doubled
        else:
            checksum += digit

    return checksum % 10 == 0


# Compiled regex patterns

# Email: RFC 5322 simplified pattern
EMAIL_REGEX: Pattern = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
    re.IGNORECASE,
)

# Social Security Number (US standard):
# Format: XXX-XX-XXXX, excluding known invalid area codes (000, 666, 900-999)
SSN_REGEX: Pattern = re.compile(
    r"(?<!\d)(?!000|666|9\d{2})(\d{3})-(?!00)(\d{2})-(?!0000)(\d{4})(?!\d)"
)

# IPv4 Address: strict 0-255 octets
IPV4_REGEX: Pattern = re.compile(
    r"(?<![A-Za-z0-9\.])(?:(?:25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])\.){3}"
    r"(?:25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])(?![A-Za-z0-9]|(?:\.\d))"
)

# Phone Numbers:
# Support:
# - Indian mobile: +91 9876543210, +91-98765-43210, 9876543210, 09876543210
# - North American: +1 (555) 123-4567, 555-123-4567, (555) 123-4567
# - Generic international: +44 20 7946 0958, +49 30 123456
PHONE_PATTERNS: List[Pattern] = [
    # Indian formats with or without country code (+91, 91, 0)
    re.compile(
        r"(?<![A-Za-z0-9_-])(?:\+?91[\s.-]?|0)?[6-9]\d{4}[\s.-]?\d{5}(?![A-Za-z0-9_-])"
    ),
    # US / North American formatted numbers: (123) 456-7890, 123-456-7890, +1 123-456-7890
    re.compile(
        r"(?<![A-Za-z0-9_-])(?:\+?1[\s.-]?)?(?:\(\d{3}\)|\d{3})[\s.-]\d{3}[\s.-]\d{4}(?![A-Za-z0-9_-])"
    ),
    # International formats with explicit '+' and spaces/dashes
    re.compile(
        r"(?<![A-Za-z0-9_-])\+\d{1,3}[\s.-](?:\(?\d{1,4}\)?[\s.-])?\d{2,4}[\s.-]\d{3,4}(?![A-Za-z0-9_-])"
    ),
]

# Credit Card Candidates:
# 13 to 19 digits with standard chunking (4-4-4-4, 4-4-4-3, 4-6-5) or continuous
CREDIT_CARD_REGEX: Pattern = re.compile(
    r"(?<![A-Za-z0-9_-])(?:\d{4}[ -]\d{4}[ -]\d{4}[ -](?:\d{4}|\d{3})|\d{4}[ -]\d{6}[ -]\d{5}|\d{13,19})(?![A-Za-z0-9_-])"
)

# Contextual Date of Birth keywords (look for these within preceding/following window)
DOB_KEYWORD_REGEX: Pattern = re.compile(
    r"\b(?:dob|d\.o\.b\.?|date\s+of\s+birth|birth\s*date|born\s+on|born)\b",
    re.IGNORECASE,
)

# Date formats:
# 12/05/2001, 12-05-2001, 2001-05-12, 12 May 2001, May 12, 2001, etc.
DATE_PATTERNS: List[Pattern] = [
    # DD/MM/YYYY, MM/DD/YYYY, DD-MM-YYYY, YYYY-MM-DD, YYYY/MM/DD
    re.compile(r"\b(?:\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}[-/]\d{1,2}[-/]\d{2,4})\b"),
    # 12 May 2001, 12th August 1995, May 12, 2001
    re.compile(
        r"\b(?:\d{1,2}(?:st|nd|rd|th)?\s+(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)[,\s]+\d{2,4}|"
        r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{1,2}(?:st|nd|rd|th)?[,\s]+\d{2,4})\b",
        re.IGNORECASE,
    ),
]

# Physical Address regex patterns:
# Matches street numbers followed by name and standard road suffix, with optional suite/apt/city/state/pin
STREET_SUFFIXES = (
    r"(?:Street|St|Road|Rd|Avenue|Ave|Boulevard|Blvd|Lane|Ln|Drive|Dr|Court|Ct|Circle|Way|"
    r"Nagar|Marg|Sector|Colony|Cross|Layout|Enclave|Apartments|Tower|Block|Phase|Extension|Gali)"
)

_ADDR_BASE = (
    rf"\b\d{{1,5}}[\s,]+(?:[A-Za-z0-9\.\'\-]+[\s,]+){{1,4}}{STREET_SUFFIXES}\b"
    r"(?:[\s,]+(?:Apt|Suite|Unit|Flat|Floor|Room|#)\s*[\w\-]+)?"
    r"(?:[\s,]+[A-Za-z]+)*"
)
_ADDR_WITH_ZIP = rf"{_ADDR_BASE}[\s,]+(?:[A-Z]{{2}}\s+)?\d{{5,6}}\b"
_ADDR_WITHOUT_ZIP = rf"{_ADDR_BASE}(?:[\s,]+[A-Z]{{2}}\b)?"

PHYSICAL_ADDRESS_REGEX: Pattern = re.compile(
    rf"(?:{_ADDR_WITH_ZIP}|{_ADDR_WITHOUT_ZIP})",
    re.IGNORECASE,
)

# Company regex pattern: corporate entities ending with standard legal suffixes
COMPANY_REGEX: Pattern = re.compile(
    r"\b(?:[A-Z][A-Za-z0-9&.-]*\s+)+(?:Ltd\.?|Inc\.?|Corp\.?|Corporation|LLC|LLP|GmbH|Pvt\.?\s*Ltd\.?)\b(?:\.)?"
)

# Common ticketing/order identifiers to ignore (e.g. TKT-1023, ORD-123456, INV-2026-1001, EMP12345)
IDENTIFIER_REGEX: Pattern = re.compile(
    r"\b(?:TKT|ORD|INV|EMP|REQ|INC|CASE|REF|BUG|PR|SR|PO)[-_]?\d{3,10}\b",
    re.IGNORECASE,
)


def is_ticketing_identifier(text: str) -> bool:
    """Return True if the candidate matches standard non-PII ticketing/order/invoice IDs."""
    return bool(IDENTIFIER_REGEX.fullmatch(text.strip()))


def is_network_infrastructure_ip(ip_str: str) -> bool:
    """Filter out non-sensitive infrastructure IPs (like 0.0.0.0, 255.255.255.255, 255.255.255.0)."""
    clean_ip = ip_str.strip()
    return clean_ip in {"0.0.0.0", "255.255.255.255", "255.255.255.0", "127.0.0.1"}
