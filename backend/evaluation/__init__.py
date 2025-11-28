"""
Evaluation harness for the Document Q&A system.

Phase 3: Provides automated benchmarking, metrics computation,
and ablation study capabilities.
"""

from .metrics import (
    compute_exact_match,
    compute_f1_score,
    compute_recall_at_k,
    compute_ndcg,
    EvaluationMetrics
)
from .benchmark import Benchmark, BenchmarkResult

__all__ = [
    # Metrics
    "compute_exact_match",
    "compute_f1_score",
    "compute_recall_at_k",
    "compute_ndcg",
    "EvaluationMetrics",
    # Benchmark
    "Benchmark",
    "BenchmarkResult",
]


