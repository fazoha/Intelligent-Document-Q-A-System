"""
Evaluation metrics for Question Answering systems.

Phase 3: Implements standard QA evaluation metrics including
Exact Match, F1 Score, Recall@K, and nDCG.
"""

import re
import string
from typing import List, Set, Tuple, Optional
from dataclasses import dataclass
from collections import Counter
import math


def normalize_answer(text: str) -> str:
    """
    Normalize text for comparison.
    
    - Lowercase
    - Remove punctuation
    - Remove articles (a, an, the)
    - Remove extra whitespace
    
    Args:
        text: Input text
        
    Returns:
        Normalized text
    """
    # Lowercase
    text = text.lower()
    
    # Remove punctuation
    text = ''.join(ch for ch in text if ch not in string.punctuation)
    
    # Remove articles
    articles = {'a', 'an', 'the'}
    words = text.split()
    words = [w for w in words if w not in articles]
    
    # Remove extra whitespace
    return ' '.join(words)


def get_tokens(text: str) -> List[str]:
    """
    Tokenize normalized text.
    
    Args:
        text: Input text
        
    Returns:
        List of tokens
    """
    return normalize_answer(text).split()


def compute_exact_match(prediction: str, ground_truth: str) -> float:
    """
    Compute Exact Match (EM) score.
    
    Args:
        prediction: Predicted answer
        ground_truth: Ground truth answer
        
    Returns:
        1.0 if exact match, 0.0 otherwise
    """
    return float(normalize_answer(prediction) == normalize_answer(ground_truth))


def compute_f1_score(prediction: str, ground_truth: str) -> float:
    """
    Compute token-level F1 score.
    
    F1 = 2 * (precision * recall) / (precision + recall)
    
    Args:
        prediction: Predicted answer
        ground_truth: Ground truth answer
        
    Returns:
        F1 score between 0.0 and 1.0
    """
    pred_tokens = get_tokens(prediction)
    gold_tokens = get_tokens(ground_truth)
    
    if not pred_tokens or not gold_tokens:
        return float(pred_tokens == gold_tokens)
    
    # Count common tokens
    common = Counter(pred_tokens) & Counter(gold_tokens)
    num_common = sum(common.values())
    
    if num_common == 0:
        return 0.0
    
    precision = num_common / len(pred_tokens)
    recall = num_common / len(gold_tokens)
    
    f1 = 2 * precision * recall / (precision + recall)
    
    return f1


def compute_recall_at_k(
    retrieved_ids: List[str],
    relevant_ids: Set[str],
    k: int = 5
) -> float:
    """
    Compute Recall@K for retrieval evaluation.
    
    Recall@K = |retrieved@K ∩ relevant| / |relevant|
    
    Args:
        retrieved_ids: List of retrieved document/chunk IDs (ranked)
        relevant_ids: Set of relevant document/chunk IDs
        k: Number of top results to consider
        
    Returns:
        Recall@K score between 0.0 and 1.0
    """
    if not relevant_ids:
        return 0.0
    
    retrieved_at_k = set(retrieved_ids[:k])
    hits = len(retrieved_at_k.intersection(relevant_ids))
    
    return hits / len(relevant_ids)


def compute_precision_at_k(
    retrieved_ids: List[str],
    relevant_ids: Set[str],
    k: int = 5
) -> float:
    """
    Compute Precision@K for retrieval evaluation.
    
    Precision@K = |retrieved@K ∩ relevant| / K
    
    Args:
        retrieved_ids: List of retrieved document/chunk IDs (ranked)
        relevant_ids: Set of relevant document/chunk IDs
        k: Number of top results to consider
        
    Returns:
        Precision@K score between 0.0 and 1.0
    """
    if k == 0:
        return 0.0
    
    retrieved_at_k = set(retrieved_ids[:k])
    hits = len(retrieved_at_k.intersection(relevant_ids))
    
    return hits / k


def compute_dcg(relevances: List[float], k: int = 10) -> float:
    """
    Compute Discounted Cumulative Gain (DCG).
    
    DCG@K = Σ (rel_i / log2(i + 1)) for i = 1 to K
    
    Args:
        relevances: List of relevance scores (higher = more relevant)
        k: Number of results to consider
        
    Returns:
        DCG score
    """
    dcg = 0.0
    
    for i, rel in enumerate(relevances[:k]):
        # Use 1-indexed position for log
        dcg += rel / math.log2(i + 2)
    
    return dcg


def compute_ndcg(
    retrieved_ids: List[str],
    relevance_scores: dict,
    k: int = 10
) -> float:
    """
    Compute Normalized Discounted Cumulative Gain (nDCG@K).
    
    nDCG@K = DCG@K / IDCG@K
    
    Args:
        retrieved_ids: List of retrieved document/chunk IDs (ranked)
        relevance_scores: Dict mapping ID -> relevance score
        k: Number of results to consider
        
    Returns:
        nDCG score between 0.0 and 1.0
    """
    # Get relevances for retrieved items
    retrieved_relevances = [
        relevance_scores.get(doc_id, 0.0)
        for doc_id in retrieved_ids[:k]
    ]
    
    # Compute DCG
    dcg = compute_dcg(retrieved_relevances, k)
    
    # Compute ideal DCG (sorted by relevance)
    ideal_relevances = sorted(relevance_scores.values(), reverse=True)[:k]
    idcg = compute_dcg(ideal_relevances, k)
    
    if idcg == 0:
        return 0.0
    
    return dcg / idcg


def compute_mrr(
    retrieved_ids: List[str],
    relevant_ids: Set[str]
) -> float:
    """
    Compute Mean Reciprocal Rank (MRR).
    
    MRR = 1 / rank_of_first_relevant
    
    Args:
        retrieved_ids: List of retrieved document/chunk IDs (ranked)
        relevant_ids: Set of relevant document/chunk IDs
        
    Returns:
        MRR score between 0.0 and 1.0
    """
    for i, doc_id in enumerate(retrieved_ids):
        if doc_id in relevant_ids:
            return 1.0 / (i + 1)
    
    return 0.0


@dataclass
class EvaluationMetrics:
    """Container for evaluation metrics."""
    
    exact_match: float = 0.0
    f1_score: float = 0.0
    recall_at_5: float = 0.0
    recall_at_10: float = 0.0
    precision_at_5: float = 0.0
    ndcg_at_10: float = 0.0
    mrr: float = 0.0
    confidence_score: float = 0.0
    answer_type: str = "generative"
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "exact_match": self.exact_match,
            "f1_score": self.f1_score,
            "recall_at_5": self.recall_at_5,
            "recall_at_10": self.recall_at_10,
            "precision_at_5": self.precision_at_5,
            "ndcg_at_10": self.ndcg_at_10,
            "mrr": self.mrr,
            "confidence_score": self.confidence_score,
            "answer_type": self.answer_type,
        }
    
    @classmethod
    def average(cls, metrics_list: List['EvaluationMetrics']) -> 'EvaluationMetrics':
        """Compute average metrics across a list."""
        if not metrics_list:
            return cls()
        
        n = len(metrics_list)
        
        return cls(
            exact_match=sum(m.exact_match for m in metrics_list) / n,
            f1_score=sum(m.f1_score for m in metrics_list) / n,
            recall_at_5=sum(m.recall_at_5 for m in metrics_list) / n,
            recall_at_10=sum(m.recall_at_10 for m in metrics_list) / n,
            precision_at_5=sum(m.precision_at_5 for m in metrics_list) / n,
            ndcg_at_10=sum(m.ndcg_at_10 for m in metrics_list) / n,
            mrr=sum(m.mrr for m in metrics_list) / n,
            confidence_score=sum(m.confidence_score for m in metrics_list) / n,
        )


def evaluate_answer(
    prediction: str,
    ground_truth: str,
    retrieved_ids: List[str],
    relevant_ids: Set[str],
    relevance_scores: Optional[dict] = None,
    confidence_score: float = 0.0,
    answer_type: str = "generative"
) -> EvaluationMetrics:
    """
    Compute all evaluation metrics for a single QA example.
    
    Args:
        prediction: Predicted answer text
        ground_truth: Ground truth answer text
        retrieved_ids: List of retrieved chunk IDs (ranked)
        relevant_ids: Set of relevant chunk IDs
        relevance_scores: Dict mapping chunk ID -> relevance score (for nDCG)
        confidence_score: Confidence score from the system
        answer_type: Type of answer (generative/extractive)
        
    Returns:
        EvaluationMetrics object with all computed metrics
    """
    # Default relevance scores if not provided
    if relevance_scores is None:
        relevance_scores = {doc_id: 1.0 for doc_id in relevant_ids}
    
    return EvaluationMetrics(
        exact_match=compute_exact_match(prediction, ground_truth),
        f1_score=compute_f1_score(prediction, ground_truth),
        recall_at_5=compute_recall_at_k(retrieved_ids, relevant_ids, k=5),
        recall_at_10=compute_recall_at_k(retrieved_ids, relevant_ids, k=10),
        precision_at_5=compute_precision_at_k(retrieved_ids, relevant_ids, k=5),
        ndcg_at_10=compute_ndcg(retrieved_ids, relevance_scores, k=10),
        mrr=compute_mrr(retrieved_ids, relevant_ids),
        confidence_score=confidence_score,
        answer_type=answer_type
    )


