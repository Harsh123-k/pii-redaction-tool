"""Configuration and constants for the PII Redaction Tool."""

from pathlib import Path
from typing import Dict, List, Set

# Base paths
BASE_DIR: Path = Path(__file__).resolve().parent.parent
UPLOAD_DIR: Path = BASE_DIR / "uploads"
OUTPUT_DIR: Path = BASE_DIR / "output"
SAMPLE_DIR: Path = BASE_DIR / "data" / "sample"

# Ensure directories exist
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
SAMPLE_DIR.mkdir(parents=True, exist_ok=True)

# File upload restrictions
MAX_FILE_SIZE_BYTES: int = 15 * 1024 * 1024  # 15 MB
ALLOWED_EXTENSIONS: Set[str] = {".docx", ".txt"}

# Supported PII entity types
SUPPORTED_PII_TYPES: List[str] = [
    "PERSON",
    "EMAIL",
    "PHONE",
    "COMPANY",
    "ADDRESS",
    "SSN",
    "CREDIT_CARD",
    "DOB",
    "IP_ADDRESS",
]

# Priority ordering for resolving overlapping entity spans.
# Highly specific structured entities take precedence over broad NER entities.
ENTITY_PRIORITY: Dict[str, int] = {
    "CREDIT_CARD": 100,
    "SSN": 95,
    "EMAIL": 90,
    "IP_ADDRESS": 85,
    "PHONE": 80,
    "DOB": 75,
    "ADDRESS": 60,
    "COMPANY": 50,
    "PERSON": 40,
}

# NLP configuration
SPACY_MODEL: str = "en_core_web_sm"

# Base detector confidence ratings
DEFAULT_CONFIDENCE: Dict[str, float] = {
    "EMAIL": 0.99,
    "SSN": 0.98,
    "CREDIT_CARD": 0.98,
    "IP_ADDRESS": 0.95,
    "ADDRESS": 0.95,
    "PHONE": 0.92,
    "DOB": 0.90,
    "COMPANY": 0.90,
    "PERSON": 0.85,
}

# Non-PII dictionary & ticketing domain terms to prevent false positives in NER
NER_IGNORE_WORDS: Set[str] = {
    # Ticketing & support terms
    "ticket", "tickets", "order", "orders", "invoice", "invoices", "support",
    "department", "dept", "status", "resolution", "priority", "urgent",
    "high", "low", "medium", "critical", "incident", "request", "issue",
    "bug", "feature", "summary", "description", "details", "comments",
    "agent", "customer", "client", "user", "admin", "administrator",
    "helpdesk", "queue", "assigned", "unassigned", "closed", "open",
    "pending", "resolved", "reopened", "escalated", "tier", "sla",
    "requester", "employer", "notes", "contact", "organization", "office",
    # System & infrastructure terms
    "server", "system", "database", "network", "firewall", "windows",
    "linux", "macos", "android", "ios", "chrome", "firefox", "edge",
    "safari", "production", "staging", "development", "test", "testing",
    "version", "update", "patch", "build", "api", "rest", "json", "xml",
    # PII labels and meta indicators
    "ssn", "dob", "card", "credit card", "active card", "corporate card",
    "national id", "taxpayer", "ip", "client ip", "session ip", "non-pii",
    # General false positives
    "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
    "january", "february", "march", "april", "may", "june", "july",
    "august", "september", "october", "november", "december",
    "today", "yesterday", "tomorrow", "morning", "afternoon", "evening",
    "internal", "external", "public", "private", "confidential",
    "id", "identifier", "code", "ref", "reference", "item", "qty", "amount"
}
