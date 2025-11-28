"""
Tests for Phase 3 Evaluation Metrics.
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from evaluation.metrics import (
    normalize_answer,
    get_tokens,
    compute_exact_match,
    compute_f1_score,
    compute_recall_at_k,
    compute_precision_at_k,
    compute_dcg,
    compute_ndcg,
    compute_mrr,
    EvaluationMetrics,
    evaluate_answer
)


class TestNormalization:
    """Tests for answer normalization."""
    
    def test_lowercase(self):
        """Test lowercase conversion."""
        assert normalize_answer("HELLO") == "hello"
    
    def test_remove_punctuation(self):
        """Test punctuation removal."""
        assert normalize_answer("hello, world!") == "hello world"
    
    def test_remove_articles(self):
        """Test article removal."""
        assert normalize_answer("the quick brown fox") == "quick brown fox"
        assert normalize_answer("a cat and an apple") == "cat and apple"
    
    def test_whitespace(self):
        """Test whitespace normalization."""
        assert normalize_answer("hello   world") == "hello world"


class TestExactMatch:
    """Tests for Exact Match metric."""
    
    def test_exact_match_identical(self):
        """Test EM with identical answers."""
        assert compute_exact_match("hello world", "hello world") == 1.0
    
    def test_exact_match_case_insensitive(self):
        """Test EM is case insensitive."""
        assert compute_exact_match("Hello World", "hello world") == 1.0
    
    def test_exact_match_different(self):
        """Test EM with different answers."""
        assert compute_exact_match("hello", "world") == 0.0
    
    def test_exact_match_with_articles(self):
        """Test EM ignores articles."""
        assert compute_exact_match("the answer", "answer") == 1.0


class TestF1Score:
    """Tests for F1 Score metric."""
    
    def test_f1_identical(self):
        """Test F1 with identical answers."""
        assert compute_f1_score("hello world", "hello world") == 1.0
    
    def test_f1_partial_overlap(self):
        """Test F1 with partial overlap."""
        f1 = compute_f1_score("hello world foo", "hello world bar")
        assert 0.5 < f1 < 1.0
    
    def test_f1_no_overlap(self):
        """Test F1 with no overlap."""
        assert compute_f1_score("hello", "world") == 0.0
    
    def test_f1_empty(self):
        """Test F1 with empty answers."""
        assert compute_f1_score("", "") == 1.0  # Both empty = match
        assert compute_f1_score("hello", "") == 0.0


class TestRecallAtK:
    """Tests for Recall@K metric."""
    
    def test_recall_all_relevant(self):
        """Test recall when all relevant items retrieved."""
        retrieved = ["a", "b", "c"]
        relevant = {"a", "b"}
        assert compute_recall_at_k(retrieved, relevant, k=3) == 1.0
    
    def test_recall_partial(self):
        """Test recall with partial retrieval."""
        retrieved = ["a", "b", "c"]
        relevant = {"a", "b", "d"}
        assert compute_recall_at_k(retrieved, relevant, k=3) == 2/3
    
    def test_recall_none_relevant(self):
        """Test recall when no relevant items retrieved."""
        retrieved = ["x", "y", "z"]
        relevant = {"a", "b"}
        assert compute_recall_at_k(retrieved, relevant, k=3) == 0.0
    
    def test_recall_k_limits(self):
        """Test recall respects K limit."""
        retrieved = ["a", "b", "c", "d"]
        relevant = {"c", "d"}
        # At k=2, neither c nor d is retrieved
        assert compute_recall_at_k(retrieved, relevant, k=2) == 0.0
        # At k=4, both are retrieved
        assert compute_recall_at_k(retrieved, relevant, k=4) == 1.0


class TestPrecisionAtK:
    """Tests for Precision@K metric."""
    
    def test_precision_all_relevant(self):
        """Test precision when all retrieved are relevant."""
        retrieved = ["a", "b"]
        relevant = {"a", "b", "c"}
        assert compute_precision_at_k(retrieved, relevant, k=2) == 1.0
    
    def test_precision_partial(self):
        """Test precision with partial relevance."""
        retrieved = ["a", "b", "c"]
        relevant = {"a", "c"}
        assert compute_precision_at_k(retrieved, relevant, k=3) == 2/3
    
    def test_precision_none_relevant(self):
        """Test precision when none relevant."""
        retrieved = ["x", "y"]
        relevant = {"a", "b"}
        assert compute_precision_at_k(retrieved, relevant, k=2) == 0.0


class TestNDCG:
    """Tests for nDCG metric."""
    
    def test_ndcg_perfect_ranking(self):
        """Test nDCG with perfect ranking."""
        retrieved = ["a", "b", "c"]
        relevance = {"a": 3.0, "b": 2.0, "c": 1.0}
        assert compute_ndcg(retrieved, relevance, k=3) == 1.0
    
    def test_ndcg_reversed_ranking(self):
        """Test nDCG with reversed ranking."""
        retrieved = ["c", "b", "a"]
        relevance = {"a": 3.0, "b": 2.0, "c": 1.0}
        ndcg = compute_ndcg(retrieved, relevance, k=3)
        assert 0.0 < ndcg < 1.0
    
    def test_ndcg_no_relevance(self):
        """Test nDCG with no relevant items."""
        retrieved = ["x", "y", "z"]
        relevance = {"a": 1.0}
        assert compute_ndcg(retrieved, relevance, k=3) == 0.0


class TestMRR:
    """Tests for Mean Reciprocal Rank metric."""
    
    def test_mrr_first_position(self):
        """Test MRR when relevant item is first."""
        retrieved = ["a", "b", "c"]
        relevant = {"a"}
        assert compute_mrr(retrieved, relevant) == 1.0
    
    def test_mrr_second_position(self):
        """Test MRR when relevant item is second."""
        retrieved = ["b", "a", "c"]
        relevant = {"a"}
        assert compute_mrr(retrieved, relevant) == 0.5
    
    def test_mrr_third_position(self):
        """Test MRR when relevant item is third."""
        retrieved = ["b", "c", "a"]
        relevant = {"a"}
        assert compute_mrr(retrieved, relevant) == 1/3
    
    def test_mrr_not_found(self):
        """Test MRR when relevant item not found."""
        retrieved = ["x", "y", "z"]
        relevant = {"a"}
        assert compute_mrr(retrieved, relevant) == 0.0


class TestEvaluationMetrics:
    """Tests for EvaluationMetrics dataclass."""
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        metrics = EvaluationMetrics(
            exact_match=1.0,
            f1_score=0.8,
            recall_at_5=0.6
        )
        d = metrics.to_dict()
        assert d["exact_match"] == 1.0
        assert d["f1_score"] == 0.8
        assert d["recall_at_5"] == 0.6
    
    def test_average(self):
        """Test averaging multiple metrics."""
        metrics_list = [
            EvaluationMetrics(exact_match=1.0, f1_score=0.8),
            EvaluationMetrics(exact_match=0.0, f1_score=0.6),
        ]
        avg = EvaluationMetrics.average(metrics_list)
        assert avg.exact_match == 0.5
        assert avg.f1_score == 0.7


class TestEvaluateAnswer:
    """Tests for full answer evaluation."""
    
    def test_evaluate_answer_perfect(self):
        """Test evaluation with perfect answer."""
        metrics = evaluate_answer(
            prediction="the answer is 42",
            ground_truth="the answer is 42",
            retrieved_ids=["chunk_1"],
            relevant_ids={"chunk_1"},
            confidence_score=0.9,
            answer_type="generative"
        )
        
        assert metrics.exact_match == 1.0
        assert metrics.f1_score == 1.0
        assert metrics.recall_at_5 == 1.0
        assert metrics.confidence_score == 0.9
        assert metrics.answer_type == "generative"
    
    def test_evaluate_answer_partial(self):
        """Test evaluation with partial match."""
        metrics = evaluate_answer(
            prediction="answer is 42",
            ground_truth="the answer is 43",
            retrieved_ids=["chunk_1", "chunk_2"],
            relevant_ids={"chunk_2", "chunk_3"},
            confidence_score=0.5
        )
        
        assert 0.0 < metrics.f1_score < 1.0
        assert metrics.recall_at_5 == 0.5  # 1 of 2 relevant


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


