"""Evaluation: sentence boundary precision/recall/F1 against gold annotations.

Gold format: JSON file per book with structure:
{
  "slug": "...",
  "chapters": [
    {
      "number": 1,
      "expected_chapter_label": "...",
      "sentence_boundaries": [0, 45, 120, ...]  // char offsets of sentence starts
    }
  ]
}
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass


@dataclass
class EvalMetrics:
    """Evaluation metrics for sentence boundary detection."""
    precision: float
    recall: float
    f1: float
    true_positives: int
    false_positives: int
    false_negatives: int
    total_predicted: int
    total_gold: int


def evaluate_boundaries(
    predicted_starts: list[int],
    gold_starts: list[int],
    tolerance: int = 3,
) -> EvalMetrics:
    """Evaluate predicted sentence boundaries against gold standard.

    A predicted boundary is a true positive if it's within `tolerance`
    characters of a gold boundary.

    Args:
        predicted_starts: List of predicted sentence start offsets.
        gold_starts: List of gold sentence start offsets.
        tolerance: Character tolerance for boundary matching.

    Returns:
        EvalMetrics with precision, recall, F1.
    """
    pred_set = set(predicted_starts)
    gold_set = set(gold_starts)

    tp = 0
    matched_gold = set()

    for p in sorted(pred_set):
        for g in sorted(gold_set):
            if g in matched_gold:
                continue
            if abs(p - g) <= tolerance:
                tp += 1
                matched_gold.add(g)
                break

    fp = len(pred_set) - tp
    fn = len(gold_set) - len(matched_gold)

    precision = tp / len(pred_set) if pred_set else 0.0
    recall = tp / len(gold_set) if gold_set else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

    return EvalMetrics(
        precision=precision,
        recall=recall,
        f1=f1,
        true_positives=tp,
        false_positives=fp,
        false_negatives=fn,
        total_predicted=len(pred_set),
        total_gold=len(gold_set),
    )


def load_gold(gold_path: str) -> dict:
    """Load gold annotation file."""
    with open(gold_path, "r", encoding="utf-8") as f:
        return json.load(f)


def evaluate_book(
    predicted_spans: dict[int, list[tuple[int, int]]],
    gold_data: dict,
    tolerance: int = 3,
) -> dict:
    """Evaluate a full book against gold annotations.

    Args:
        predicted_spans: Mapping of chapter number -> list of (start, end) spans.
        gold_data: Gold annotation data.
        tolerance: Character tolerance.

    Returns:
        Dict with per-chapter and aggregate metrics.
    """
    chapter_metrics = {}
    all_pred = []
    all_gold = []

    for gold_ch in gold_data.get("chapters", []):
        ch_num = gold_ch["number"]
        gold_starts = gold_ch.get("sentence_boundaries", [])
        pred_starts = [s for s, e in predicted_spans.get(ch_num, [])]

        metrics = evaluate_boundaries(pred_starts, gold_starts, tolerance)
        chapter_metrics[ch_num] = metrics

        all_pred.extend(pred_starts)
        all_gold.extend(gold_starts)

    aggregate = evaluate_boundaries(all_pred, all_gold, tolerance)

    return {
        "aggregate": aggregate,
        "per_chapter": chapter_metrics,
        "chapter_count_expected": gold_data.get("expected_chapter_count"),
    }
