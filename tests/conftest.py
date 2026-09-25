"""Shared pytest fixtures for PII Redaction Tool test suite."""

import pytest
from src.pii_detector import PIIDetector
from src.replacement_generator import ReplacementGenerator
from src.redactor import Redactor
from src.document_handler import DocumentHandler
from src.evaluator import PIIEvaluator


@pytest.fixture(scope="session")
def detector() -> PIIDetector:
    """Session-scoped PIIDetector instance with spaCy model loaded."""
    return PIIDetector()


@pytest.fixture
def generator() -> ReplacementGenerator:
    """Function-scoped ReplacementGenerator with deterministic seed."""
    return ReplacementGenerator(seed=42)


@pytest.fixture
def redactor(detector: PIIDetector, generator: ReplacementGenerator) -> Redactor:
    """Function-scoped Redactor with deterministic generator."""
    return Redactor(detector=detector, generator=generator)


@pytest.fixture
def doc_handler(detector: PIIDetector, generator: ReplacementGenerator) -> DocumentHandler:
    """Function-scoped DocumentHandler instance."""
    return DocumentHandler(detector=detector, generator=generator)


@pytest.fixture(scope="session")
def evaluator(detector: PIIDetector) -> PIIEvaluator:
    """Session-scoped PIIEvaluator instance."""
    return PIIEvaluator(detector=detector)
