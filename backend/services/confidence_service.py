"""
Confidence scoring service using ROUGE-L for citation validation.

Phase 3: Validates that generated answers are supported by cited chunks.
"""

import re
from typing import List, Dict, Tuple, Optional
from collections import Counter
from models import ChunkMetadata, Citation
from utils import app_logger


class ConfidenceScorer:
    """
    Computes confidence scores for generated answers based on citation overlap.
    
    Uses ROUGE-L (Longest Common Subsequence) to measure how well the answer
    text is supported by the cited chunk text.
    """
    
    def __init__(self):
        self.logger = app_logger
    
    def compute_confidence_score(
        self,
        answer: str,
        citations: List[Citation]
    ) -> float:
        """
        Compute overall confidence score for an answer.
        
        Args:
            answer: Generated answer text
            citations: List of citations used in the answer
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        if not answer or not citations:
            self.logger.warning("No answer or citations provided for confidence scoring")
            return 0.0
        
        # Extract cited text from all citations
        cited_text = " ".join([c.text for c in citations])
        
        # Remove citation markers from answer for cleaner comparison
        clean_answer = self._remove_citation_markers(answer)
        
        # Compute ROUGE-L score
        rouge_l = self.compute_rouge_l(clean_answer, cited_text)
        
        # Compute token overlap as secondary signal
        token_overlap = self.compute_token_overlap(clean_answer, cited_text)
        
        # Weighted combination (ROUGE-L is primary)
        confidence = 0.7 * rouge_l + 0.3 * token_overlap
        
        self.logger.info(
            f"Confidence score: {confidence:.3f} "
            f"(ROUGE-L: {rouge_l:.3f}, Token overlap: {token_overlap:.3f})"
        )
        
        return round(confidence, 3)
    
    def compute_rouge_l(self, candidate: str, reference: str) -> float:
        """
        Compute ROUGE-L (Longest Common Subsequence) F1 score.
        
        Args:
            candidate: The generated text (answer)
            reference: The reference text (cited chunks)
            
        Returns:
            ROUGE-L F1 score between 0.0 and 1.0
        """
        # Tokenize
        candidate_tokens = self._tokenize(candidate)
        reference_tokens = self._tokenize(reference)
        
        if not candidate_tokens or not reference_tokens:
            return 0.0
        
        # Compute LCS length
        lcs_length = self._lcs_length(candidate_tokens, reference_tokens)
        
        # Compute precision and recall
        precision = lcs_length / len(candidate_tokens) if candidate_tokens else 0.0
        recall = lcs_length / len(reference_tokens) if reference_tokens else 0.0
        
        # Compute F1 score
        if precision + recall == 0:
            return 0.0
        
        f1 = 2 * precision * recall / (precision + recall)
        
        return f1
    
    def compute_token_overlap(self, candidate: str, reference: str) -> float:
        """
        Compute simple token overlap ratio.
        
        Args:
            candidate: The generated text
            reference: The reference text
            
        Returns:
            Overlap ratio between 0.0 and 1.0
        """
        candidate_tokens = set(self._tokenize(candidate.lower()))
        reference_tokens = set(self._tokenize(reference.lower()))
        
        if not candidate_tokens:
            return 0.0
        
        overlap = candidate_tokens.intersection(reference_tokens)
        
        return len(overlap) / len(candidate_tokens)
    
    def compute_sentence_level_confidence(
        self,
        answer: str,
        citations: List[Citation]
    ) -> List[Dict[str, float]]:
        """
        Compute confidence for each sentence in the answer.
        
        Args:
            answer: Generated answer text
            citations: List of citations
            
        Returns:
            List of dicts with sentence and confidence score
        """
        sentences = self._split_sentences(answer)
        cited_text = " ".join([c.text for c in citations])
        
        results = []
        for sentence in sentences:
            clean_sentence = self._remove_citation_markers(sentence)
            if clean_sentence.strip():
                score = self.compute_rouge_l(clean_sentence, cited_text)
                results.append({
                    "sentence": sentence,
                    "confidence": round(score, 3)
                })
        
        return results
    
    def _tokenize(self, text: str) -> List[str]:
        """
        Simple word tokenization.
        
        Args:
            text: Input text
            
        Returns:
            List of tokens
        """
        if not text:
            return []
        
        # Remove punctuation and split on whitespace
        text = re.sub(r'[^\w\s]', ' ', text.lower())
        tokens = text.split()
        
        # Remove common stop words for better signal
        stop_words = {
            'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
            'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
            'would', 'could', 'should', 'may', 'might', 'must', 'shall',
            'can', 'need', 'dare', 'ought', 'used', 'to', 'of', 'in',
            'for', 'on', 'with', 'at', 'by', 'from', 'as', 'into',
            'through', 'during', 'before', 'after', 'above', 'below',
            'between', 'under', 'again', 'further', 'then', 'once',
            'and', 'but', 'or', 'nor', 'so', 'yet', 'both', 'either',
            'neither', 'not', 'only', 'own', 'same', 'than', 'too',
            'very', 'just', 'also', 'now', 'here', 'there', 'when',
            'where', 'why', 'how', 'all', 'each', 'every', 'both',
            'few', 'more', 'most', 'other', 'some', 'such', 'no',
            'any', 'this', 'that', 'these', 'those', 'it', 'its'
        }
        
        return [t for t in tokens if t not in stop_words and len(t) > 1]
    
    def _lcs_length(self, seq1: List[str], seq2: List[str]) -> int:
        """
        Compute length of Longest Common Subsequence.
        
        Uses dynamic programming for O(m*n) time complexity.
        
        Args:
            seq1: First sequence
            seq2: Second sequence
            
        Returns:
            Length of LCS
        """
        m, n = len(seq1), len(seq2)
        
        # Optimize for memory: only keep two rows
        if m < n:
            seq1, seq2 = seq2, seq1
            m, n = n, m
        
        # dp[j] represents LCS length ending at seq2[j]
        prev = [0] * (n + 1)
        curr = [0] * (n + 1)
        
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if seq1[i - 1] == seq2[j - 1]:
                    curr[j] = prev[j - 1] + 1
                else:
                    curr[j] = max(prev[j], curr[j - 1])
            prev, curr = curr, prev
        
        return prev[n]
    
    def _remove_citation_markers(self, text: str) -> str:
        """
        Remove [chunk_X] citation markers from text.
        
        Args:
            text: Text with citation markers
            
        Returns:
            Clean text without markers
        """
        return re.sub(r'\[chunk_\d+\]', '', text)
    
    def _split_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences.
        
        Args:
            text: Input text
            
        Returns:
            List of sentences
        """
        # Simple sentence splitting on common delimiters
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def get_confidence_level(self, score: float) -> str:
        """
        Get human-readable confidence level.
        
        Args:
            score: Confidence score (0-1)
            
        Returns:
            Confidence level string
        """
        if score >= 0.7:
            return "high"
        elif score >= 0.4:
            return "medium"
        else:
            return "low"


