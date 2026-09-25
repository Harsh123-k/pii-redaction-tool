"""Evaluation system computing Precision, Recall, F1, and Accuracy against ground truth annotations."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from src.config import SUPPORTED_PII_TYPES
from src.pii_detector import PIIDetector


class PIIEvaluator:
    """Evaluates predicted PII entities against ground truth annotations with per-type and overall metrics."""

    def __init__(self, detector: Optional[PIIDetector] = None) -> None:
        """Initialize evaluator with a PIIDetector."""
        self.detector = detector or PIIDetector()

    @staticmethod
    def _is_match(gold: Dict[str, Any], pred: Dict[str, Any], strict_boundary: bool = False) -> bool:
        """Check if a predicted entity matches a ground truth annotation."""
        if gold["type"].upper() != pred["type"].upper():
            return False

        if strict_boundary:
            return gold["start"] == pred["start"] and gold["end"] == pred["end"]
        else:
            # Overlap criterion: gold and pred spans share at least one character
            return not (pred["end"] <= gold["start"] or pred["start"] >= gold["end"])

    def evaluate_spans(
        self,
        gold_entities: List[Dict[str, Any]],
        pred_entities: List[Dict[str, Any]],
        strict_boundary: bool = False,
    ) -> Dict[str, Any]:
        """Compute TP, FP, FN, Precision, Recall, and F1 across all supported PII categories.

        Args:
            gold_entities: Ground truth annotations list.
            pred_entities: Model predicted annotations list.
            strict_boundary: If True, requires exact character boundary matching.

        Returns:
            Dictionary containing overall and per-type statistics and metrics.
        """
        # Group by entity type
        all_types = list(SUPPORTED_PII_TYPES)

        per_type_gold: Dict[str, List[Dict[str, Any]]] = {t: [] for t in all_types}
        per_type_pred: Dict[str, List[Dict[str, Any]]] = {t: [] for t in all_types}

        for g in gold_entities:
            gt = g["type"].upper()
            if gt in per_type_gold:
                per_type_gold[gt].append(g)

        for p in pred_entities:
            pt = p["type"].upper()
            if pt in per_type_pred:
                per_type_pred[pt].append(p)

        per_type_stats: Dict[str, Dict[str, Any]] = {}
        total_tp = 0
        total_fp = 0
        total_fn = 0

        for t in all_types:
            g_list = per_type_gold[t]
            p_list = per_type_pred[t]

            tp = 0
            matched_gold_indices = set()

            for p in p_list:
                for idx, g in enumerate(g_list):
                    if idx not in matched_gold_indices and self._is_match(g, p, strict_boundary):
                        tp += 1
                        matched_gold_indices.add(idx)
                        break

            fn = len(g_list) - tp
            fp = len(p_list) - tp

            precision = tp / (tp + fp) if (tp + fp) > 0 else (1.0 if fn == 0 and len(g_list) == 0 else 0.0)
            recall = tp / (tp + fn) if (tp + fn) > 0 else (1.0 if fp == 0 and len(p_list) == 0 else 0.0)
            f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

            type_acc = tp / (tp + fp + fn) if (tp + fp + fn) > 0 else (1.0 if fn == 0 and len(g_list) == 0 else 0.0)

            per_type_stats[t] = {
                "TP": tp,
                "FP": fp,
                "FN": fn,
                "gold_count": len(g_list),
                "pred_count": len(p_list),
                "accuracy": round(type_acc, 4),
                "precision": round(precision, 4),
                "recall": round(recall, 4),
                "f1": round(f1, 4),
            }

            total_tp += tp
            total_fp += fp
            total_fn += fn

        overall_prec = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0.0
        overall_rec = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0.0
        overall_f1 = (
            (2 * overall_prec * overall_rec) / (overall_prec + overall_rec)
            if (overall_prec + overall_rec) > 0
            else 0.0
        )
        accuracy = (
            total_tp / (total_tp + total_fp + total_fn) if (total_tp + total_fp + total_fn) > 0 else 0.0
        )

        return {
            "overall": {
                "TP": total_tp,
                "FP": total_fp,
                "FN": total_fn,
                "accuracy": round(accuracy, 4),
                "precision": round(overall_prec, 4),
                "recall": round(overall_rec, 4),
                "f1": round(overall_f1, 4),
            },
            "per_type": per_type_stats,
        }

    def evaluate_benchmark_file(self, benchmark_json_path: Path) -> Dict[str, Any]:
        """Load benchmark data, run detector, and return evaluation results.

        Benchmark file format:
        {
            "documents": [
                {
                    "id": "doc1",
                    "text": "...",
                    "ground_truth": [ {"type": "EMAIL", "text": "...", "start": 10, "end": 25}, ... ]
                }
            ]
        }
        """
        with open(benchmark_json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        all_gold: List[Dict[str, Any]] = []
        all_pred: List[Dict[str, Any]] = []

        # Offset tracker if multiple documents are concatenated
        cumulative_offset = 0

        for doc in data.get("documents", []):
            text = doc["text"]
            preds = self.detector.detect(text)

            for g in doc.get("ground_truth", []):
                all_gold.append(
                    {
                        "type": g["type"],
                        "text": g["text"],
                        "start": g["start"] + cumulative_offset,
                        "end": g["end"] + cumulative_offset,
                    }
                )

            for p in preds:
                all_pred.append(
                    {
                        "type": p["type"],
                        "text": p["text"],
                        "start": p["start"] + cumulative_offset,
                        "end": p["end"] + cumulative_offset,
                        "confidence": p.get("confidence", 0.0),
                    }
                )

            cumulative_offset += len(text) + 100

        return self.evaluate_spans(all_gold, all_pred)

    @staticmethod
    def format_markdown_table(eval_result: Dict[str, Any]) -> str:
        """Format evaluation metrics into a clean markdown table matching assignment requirements."""
        lines = [
            "| PII Type | TP | FP | FN | Accuracy | Precision | Recall | F1 |",
            "| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |",
        ]

        per_type = eval_result["per_type"]
        for pii_type, stats in per_type.items():
            lines.append(
                f"| **{pii_type}** | {stats['TP']} | {stats['FP']} | {stats['FN']} | "
                f"{stats.get('accuracy', 0.0):.3f} | {stats['precision']:.3f} | {stats['recall']:.3f} | {stats['f1']:.3f} |"
            )

        overall = eval_result["overall"]
        lines.append(
            f"| **OVERALL (Micro)** | **{overall['TP']}** | **{overall['FP']}** | **{overall['FN']}** | "
            f"**{overall['accuracy']:.3f}** | **{overall['precision']:.3f}** | **{overall['recall']:.3f}** | **{overall['f1']:.3f}** |"
        )

        return "\n".join(lines)
