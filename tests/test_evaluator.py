"""Automated test cases for PIIEvaluator metrics and benchmark evaluation."""

from pathlib import Path
import pytest

from src.config import SAMPLE_DIR
from src.evaluator import PIIEvaluator


class TestPIIEvaluator:
    """Validate calculation of TP, FP, FN, Accuracy, Precision, Recall, and F1."""

    def test_perfect_evaluation_metrics(self, evaluator: PIIEvaluator):
        """When predictions match ground truth exactly, precision, recall, and F1 must be 1.0."""
        gold = [
            {"type": "EMAIL", "text": "test@example.com", "start": 10, "end": 26},
            {"type": "SSN", "text": "123-45-6789", "start": 30, "end": 41},
        ]
        pred = [
            {"type": "EMAIL", "text": "test@example.com", "start": 10, "end": 26, "confidence": 0.99},
            {"type": "SSN", "text": "123-45-6789", "start": 30, "end": 41, "confidence": 0.98},
        ]

        result = evaluator.evaluate_spans(gold, pred)
        overall = result["overall"]

        assert overall["TP"] == 2
        assert overall["FP"] == 0
        assert overall["FN"] == 0
        assert overall["precision"] == 1.0
        assert overall["recall"] == 1.0
        assert overall["f1"] == 1.0
        assert overall["accuracy"] == 1.0

    def test_imperfect_evaluation_metrics(self, evaluator: PIIEvaluator):
        """Test calculation when there are false positives and false negatives."""
        gold = [
            {"type": "EMAIL", "text": "user1@example.com", "start": 0, "end": 17},
            {"type": "EMAIL", "text": "user2@example.com", "start": 30, "end": 47},
        ]
        pred = [
            {"type": "EMAIL", "text": "user1@example.com", "start": 0, "end": 17, "confidence": 0.99},
            {"type": "EMAIL", "text": "spurious@example.com", "start": 50, "end": 70, "confidence": 0.99},
        ]

        result = evaluator.evaluate_spans(gold, pred)
        email_stats = result["per_type"]["EMAIL"]

        assert email_stats["TP"] == 1
        assert email_stats["FP"] == 1
        assert email_stats["FN"] == 1
        assert email_stats["precision"] == 0.5
        assert email_stats["recall"] == 0.5
        assert email_stats["f1"] == 0.5

    def test_benchmark_file_run(self, evaluator: PIIEvaluator):
        """Run benchmark evaluation against real sample ground truth dataset."""
        gt_file = SAMPLE_DIR / "ground_truth.json"
        assert gt_file.exists()

        result = evaluator.evaluate_benchmark_file(gt_file)
        overall = result["overall"]

        assert overall["TP"] > 0
        assert overall["precision"] >= 0.90
        assert overall["recall"] >= 0.90
        assert overall["f1"] >= 0.90

        md_table = PIIEvaluator.format_markdown_table(result)
        assert "| PII Type |" in md_table
        assert "OVERALL (Micro)" in md_table
