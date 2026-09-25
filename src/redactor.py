"""Text redaction engine applying synthetic replacements to detected PII spans."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from src.pii_detector import PIIDetector
from src.replacement_generator import ReplacementGenerator


@dataclass
class RedactionResult:
    """Encapsulates the result of a redaction operation."""

    redacted_text: str
    total_detected: int
    breakdown: Dict[str, int] = field(default_factory=dict)
    entities: List[Dict[str, Any]] = field(default_factory=list)


class Redactor:
    """Coordinates detection and synthetic substitution on textual content."""

    def __init__(
        self,
        detector: Optional[PIIDetector] = None,
        generator: Optional[ReplacementGenerator] = None,
    ) -> None:
        """Initialize redactor with a PIIDetector and ReplacementGenerator."""
        self.detector = detector or PIIDetector()
        self.generator = generator or ReplacementGenerator()

    def redact_text(
        self,
        text: str,
        entities: Optional[List[Dict[str, Any]]] = None,
    ) -> RedactionResult:
        """Redact detected PII entities within a text string.

        Args:
            text: Original text string.
            entities: Optional pre-detected entities. If None, the detector is run.

        Returns:
            A RedactionResult object containing the redacted text, counts, and breakdown.
        """
        if not text:
            return RedactionResult(redacted_text="", total_detected=0, breakdown={})

        if entities is None:
            entities = self.detector.detect(text)

        # Count breakdown by type
        breakdown: Dict[str, int] = {}
        for ent in entities:
            t = ent["type"]
            breakdown[t] = breakdown.get(t, 0) + 1

        # Sort spans in reverse order of start position so earlier offsets remain valid
        sorted_entities = sorted(entities, key=lambda e: e["start"], reverse=True)

        result_chars = list(text)
        for ent in sorted_entities:
            start = ent["start"]
            end = ent["end"]
            original_val = ent["text"]
            entity_type = ent["type"]

            synthetic_val = self.generator.get_replacement(entity_type, original_val)
            result_chars[start:end] = list(synthetic_val)

        redacted_string = "".join(result_chars)

        return RedactionResult(
            redacted_text=redacted_string,
            total_detected=len(entities),
            breakdown=breakdown,
            entities=entities,
        )
