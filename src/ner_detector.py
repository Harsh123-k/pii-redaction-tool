"""Named Entity Recognition (NER) detector using spaCy for unstructured PII."""

import logging
import re
from typing import Any, Dict, List, Optional, Set

try:
    import spacy
    from spacy.language import Language
except ImportError:
    spacy = None
    Language = None

from src.config import DEFAULT_CONFIDENCE, NER_IGNORE_WORDS, SPACY_MODEL
from src.pii_patterns import is_ticketing_identifier

logger = logging.getLogger(__name__)


class NERDetector:
    """Detects unstructured PII (PERSON, COMPANY, ADDRESS) using spaCy NER with false-positive filtering."""

    def __init__(self, model_name: str = SPACY_MODEL) -> None:
        """Initialize the NER detector with the specified spaCy model.

        Args:
            model_name: The name of the spaCy model package to load.
        """
        self.model_name = model_name
        self.nlp: Optional[Language] = None
        self._load_model()

    def _load_model(self) -> None:
        """Load the spaCy language model, falling back gracefully if unavailable."""
        if spacy is None:
            logger.warning("spaCy library is not installed. NER detection will be disabled.")
            return

        try:
            self.nlp = spacy.load(self.model_name)
            logger.info("Successfully loaded spaCy model '%s'", self.model_name)
        except Exception as e:
            logger.warning(
                "Could not load spaCy model '%s': %s. Attempting blank 'en' fallback.",
                self.model_name,
                e,
            )
            try:
                self.nlp = spacy.blank("en")
            except Exception as e2:
                logger.error("Failed to initialize blank spaCy pipeline: %s", e2)
                self.nlp = None

    def is_available(self) -> bool:
        """Return True if the NER model is loaded and ready."""
        return self.nlp is not None and "ner" in self.nlp.pipe_names

    def _is_valid_person(self, text: str) -> bool:
        """Check if an entity text is a plausible person name and not a false positive."""
        clean = text.strip()
        clean_lower = clean.lower()

        # Reject single character or empty
        if len(clean) < 2:
            return False

        # Reject words in ignore list
        if clean_lower in NER_IGNORE_WORDS:
            return False

        # Reject pure numbers or ticketing IDs
        if clean.isdigit() or is_ticketing_identifier(clean):
            return False

        # Reject if contains ticket/order keywords or identifiers
        words = clean_lower.split()
        if any(w in NER_IGNORE_WORDS for w in words):
            return False
        if any(is_ticketing_identifier(w) for w in words):
            return False

        # Must have alphabetic characters
        if not any(c.isalpha() for c in clean):
            return False

        return True

    def _is_valid_company(self, text: str) -> bool:
        """Check if an entity text is a plausible company/organization name."""
        clean = text.strip()
        clean_lower = clean.lower()

        if len(clean) < 2:
            return False

        if clean_lower in NER_IGNORE_WORDS:
            return False

        if clean.isdigit() or is_ticketing_identifier(clean):
            return False

        # Reject if contains ticketing identifiers or digits
        words = clean_lower.split()
        if any(w in NER_IGNORE_WORDS for w in words):
            return False
        if any(is_ticketing_identifier(w) for w in words):
            return False
        if re.search(r"\d", clean):
            return False

        return True

    def detect(self, text: str) -> List[Dict[str, Any]]:
        """Run NER on text and return candidate entities.

        Args:
            text: Input string to analyze.

        Returns:
            List of detected entity dictionaries with keys:
            type, text, start, end, confidence, detector.
        """
        if not text or not self.is_available():
            return []

        doc = self.nlp(text)
        entities: List[Dict[str, Any]] = []

        for ent in doc.ents:
            ent_text = ent.text
            start = ent.start_char
            end = ent.end_char

            # If the entity span crosses a newline, truncate to the first line
            # Support tickets often format fields line-by-line without trailing periods
            if "\n" in ent_text:
                first_line = ent_text.split("\n")[0]
                ent_text = first_line
                end = start + len(first_line)

            ent_text = ent_text.strip()

            # Clean trailing punctuation from entity span
            while ent_text and ent_text[-1] in ",;:!?)]}\"'":
                ent_text = ent_text[:-1]
                end -= 1
            if ent_text and ent_text[-1] == "." and not ent_text.endswith(("Ltd.", "Inc.", "Corp.", "Co.")):
                ent_text = ent_text[:-1]
                end -= 1
            # Trim leading punctuation
            while ent_text and ent_text[0] in "([{\"'":
                ent_text = ent_text[1:]
                start += 1

            if not ent_text or len(ent_text) < 2:
                continue

            clean_lower = ent_text.lower()
            if clean_lower in NER_IGNORE_WORDS or is_ticketing_identifier(ent_text):
                continue

            entity_type: Optional[str] = None
            confidence: float = 0.80

            if ent.label_ == "PERSON":
                # Strip leading role/title prefixes like "Customer ", "Client ", "Requester "
                for prefix_word in ["customer ", "client ", "requester ", "user ", "agent ", "employee "]:
                    if clean_lower.startswith(prefix_word):
                        prefix_len = len(prefix_word)
                        start += prefix_len
                        ent_text = ent_text[prefix_len:].strip()
                        clean_lower = ent_text.lower()
                        break

                if self._is_valid_person(ent_text):
                    entity_type = "PERSON"
                    confidence = DEFAULT_CONFIDENCE.get("PERSON", 0.85)

            elif ent.label_ == "ORG":
                if self._is_valid_company(ent_text):
                    entity_type = "COMPANY"
                    confidence = DEFAULT_CONFIDENCE.get("COMPANY", 0.80)

            elif ent.label_ in {"GPE", "LOC", "FAC"}:
                # If it's a known location entity, verify it is not in ignore list
                if len(ent_text) > 2 and clean_lower not in NER_IGNORE_WORDS and not is_ticketing_identifier(ent_text):
                    prefix = text[max(0, start - 20) : start].lower()
                    if any(k in prefix for k in ["address", "loc:", "street", "city", "residing"]):
                        entity_type = "ADDRESS"
                        confidence = 0.88
                    else:
                        entity_type = "ADDRESS"
                        confidence = 0.75

            if entity_type:
                entities.append(
                    {
                        "type": entity_type,
                        "text": ent_text,
                        "start": start,
                        "end": start + len(ent_text),
                        "confidence": confidence,
                        "detector": "ner",
                    }
                )

        return entities
