"""Deterministic and realistic synthetic PII replacement generator."""

import random
import re
from typing import Dict, Optional, Tuple

try:
    from faker import Faker
except ImportError:
    Faker = None


class ReplacementGenerator:
    """Generates and tracks realistic synthetic PII replacements across a processing session.

    Ensures that identical PII values in an input document are replaced consistently
    with the same synthetic values.
    """

    # Safe synthetic credit card templates (distinct from test dataset)
    SYNTHETIC_CREDIT_CARDS = [
        "4532 9999 8888 7777",
        "4916 0123 4567 8901",
        "4485 1234 5678 9012",
        "4716 9876 5432 1098",
        "4024 0071 2345 6789",
    ]

    SYNTHETIC_COMPANIES = [
        "Apex Horizon Solutions Ltd.",
        "Prism Innovations Corp.",
        "Cobalt Data Dynamics Inc.",
        "Vertex Cloud Systems LLC",
        "Zephyr Enterprise Technologies Ltd.",
        "Helios Analytics Group Inc.",
        "Ironclad Logistics Corp.",
        "Solaria Networks Ltd.",
    ]

    SYNTHETIC_PERSONS = [
        "Casey Bennett",
        "Morgan Lee",
        "Taylor Brooks",
        "Avery Clark",
        "Samira Khan",
        "Devon Ross",
        "Riley Hayes",
        "Quinn Davies",
        "Cameron Scott",
        "Jamie Rivera",
    ]

    SYNTHETIC_ADDRESSES = [
        "900 Cedar Boulevard, Suite 500, Austin, TX 78701",
        "550 Pine Road, Floor 2, Boston, MA 02108",
        "320 Oak Lane, Apt 8C, Denver, CO 80202",
        "12 Elm Court, Unit 12, Chicago, IL 60601",
        "88 Kingfisher Way, Sector 12, Hyderabad, Telangana 500081",
    ]

    def __init__(self, seed: Optional[int] = 42) -> None:
        """Initialize replacement generator with optional random seed for reproducibility."""
        self.seed = seed
        self.rng = random.Random(seed)
        self.faker = Faker() if Faker else None
        if self.faker and seed is not None:
            self.faker.seed_instance(seed)

        # Cache: (entity_type, normalized_original_text) -> synthetic_replacement
        self._cache: Dict[Tuple[str, str], str] = {}
        self._counter: int = 0

    def reset(self) -> None:
        """Clear session cache and reset generator state."""
        self._cache.clear()
        self._counter = 0

    def get_replacement(self, entity_type: str, original_text: str) -> str:
        """Retrieve an existing replacement from cache or generate a new synthetic one.

        Args:
            entity_type: The PII category (e.g. 'PERSON', 'EMAIL', etc.).
            original_text: The detected raw PII value.

        Returns:
            A realistic synthetic replacement string.
        """
        clean_text = original_text.strip()
        cache_key = (entity_type.upper(), clean_text.lower())

        if cache_key in self._cache:
            return self._cache[cache_key]

        synthetic_val = self._generate_synthetic(entity_type, clean_text)
        attempts = 0
        while (
            synthetic_val.strip().lower() == clean_text.lower()
            or (len(clean_text) >= 4 and clean_text.lower() in synthetic_val.lower())
        ) and attempts < 10:
            synthetic_val = self._generate_synthetic(entity_type, clean_text)
            attempts += 1

        self._cache[cache_key] = synthetic_val
        return synthetic_val

    def _generate_synthetic(self, entity_type: str, original: str) -> str:
        """Generate a realistic synthetic value based on entity category and format."""
        self._counter += 1
        t = entity_type.upper()

        if t == "PERSON":
            return self._generate_person()
        elif t == "EMAIL":
            return self._generate_email(original)
        elif t == "PHONE":
            return self._generate_phone(original)
        elif t == "COMPANY":
            return self._generate_company()
        elif t == "ADDRESS":
            return self._generate_address()
        elif t == "SSN":
            return self._generate_ssn()
        elif t == "CREDIT_CARD":
            return self._generate_credit_card(original)
        elif t == "DOB":
            return self._generate_dob(original)
        elif t == "IP_ADDRESS":
            return self._generate_ip()
        else:
            return f"[SYNTHETIC_{t}_{self._counter}]"

    def _generate_person(self) -> str:
        idx = (self._counter - 1) % len(self.SYNTHETIC_PERSONS)
        return self.SYNTHETIC_PERSONS[idx]

    def _generate_email(self, original: str) -> str:
        # Use RFC 2606 safe reserved domain example.com / example.org
        domains = ["example.com", "example.org", "testmail.net"]
        domain = domains[(self._counter - 1) % len(domains)]
        # Derive username from current person or counter
        person = self.SYNTHETIC_PERSONS[(self._counter - 1) % len(self.SYNTHETIC_PERSONS)]
        user = person.lower().replace(" ", ".")
        return f"{user}{self._counter}@{domain}"

    def _generate_phone(self, original: str) -> str:
        # Preserve formatting structure of original phone
        clean = original.strip()
        if clean.startswith("+91"):
            # Synthetic Indian phone format
            suffix = f"{self.rng.randint(9123000000, 9123999999)}"
            if "-" in clean:
                return f"+91-{suffix[:5]}-{suffix[5:]}"
            elif " " in clean:
                return f"+91 {suffix[:5]} {suffix[5:]}"
            else:
                return f"+91{suffix}"
        elif clean.startswith("+1"):
            # 555 prefix is standard fictional prefix in North America
            num = self.rng.randint(1000, 9999)
            return f"+1 (555) 019-{num}"
        elif clean.startswith("+"):
            return f"+44 20 7946 {self.rng.randint(1000, 9999)}"
        else:
            # 10-digit number
            suffix = f"{self.rng.randint(9123400000, 9123499999)}"
            if "-" in clean:
                return f"{suffix[:5]}-{suffix[5:]}"
            elif " " in clean:
                return f"{suffix[:5]} {suffix[5:]}"
            return suffix

    def _generate_company(self) -> str:
        idx = (self._counter - 1) % len(self.SYNTHETIC_COMPANIES)
        return self.SYNTHETIC_COMPANIES[idx]

    def _generate_address(self) -> str:
        idx = (self._counter - 1) % len(self.SYNTHETIC_ADDRESSES)
        return self.SYNTHETIC_ADDRESSES[idx]

    def _generate_ssn(self) -> str:
        # Fictitious SSN (482-71-XXXX)
        serial = self.rng.randint(1000, 9999)
        return f"482-71-{serial}"

    def _generate_credit_card(self, original: str) -> str:
        idx = (self._counter - 1) % len(self.SYNTHETIC_CREDIT_CARDS)
        card = self.SYNTHETIC_CREDIT_CARDS[idx]
        if "-" in original:
            return card.replace(" ", "-")
        elif " " not in original and len(original) >= 15:
            return card.replace(" ", "")
        return card

    def _generate_dob(self, original: str) -> str:
        # Sample synthetic birth dates
        day = self.rng.randint(1, 28)
        month = self.rng.randint(1, 12)
        year = self.rng.randint(1982, 2002)

        # Replicate separator if possible
        if "/" in original:
            return f"{day:02d}/{month:02d}/{year}"
        elif "-" in original:
            return f"{day:02d}-{month:02d}-{year}"
        elif any(
            m in original.lower()
            for m in ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
        ):
            month_names = [
                "January", "February", "March", "April", "May", "June",
                "July", "August", "September", "October", "November", "December",
            ]
            m_name = month_names[month - 1]
            if original[0].isdigit():
                return f"{day} {m_name} {year}"
            else:
                return f"{m_name} {day}, {year}"
        return f"{day:02d}/{month:02d}/{year}"

    def _generate_ip(self) -> str:
        # RFC 5737 documentation test block (198.51.100.0/24 or 203.0.113.0/24)
        octet4 = self.rng.randint(2, 250)
        return f"198.51.100.{octet4}"
