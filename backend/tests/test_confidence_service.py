"""
Tests for Phase 3 Confidence Scoring Service.
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.confidence_service import ConfidenceScorer
from models import Citation


class TestConfidenceScorer:
    """Test suite for ConfidenceScorer."""
    
    @pytest.fixture
    def scorer(self):
        """Create a ConfidenceScorer instance."""
        return ConfidenceScorer()
    
    # ROUGE-L Tests
    
    def test_rouge_l_identical_text(self, scorer):
        """Test ROUGE-L with identical texts."""
        text = "The quick brown fox jumps over the lazy dog."
        score = scorer.compute_rouge_l(text, text)
        assert score == 1.0
    
    def test_rouge_l_similar_text(self, scorer):
        """Test ROUGE-L with similar texts."""
        candidate = "The quick brown fox jumps over the lazy dog."
        reference = "A quick brown fox jumped over the lazy dog."
        score = scorer.compute_rouge_l(candidate, reference)
        assert 0.5 < score < 1.0  # Should be high but not perfect
    
    def test_rouge_l_different_text(self, scorer):
        """Test ROUGE-L with completely different texts."""
        candidate = "Hello world!"
        reference = "Goodbye universe!"
        score = scorer.compute_rouge_l(candidate, reference)
        assert score < 0.3  # Should be very low
    
    def test_rouge_l_empty_text(self, scorer):
        """Test ROUGE-L with empty text."""
        score = scorer.compute_rouge_l("", "some text")
        assert score == 0.0
        
        score = scorer.compute_rouge_l("some text", "")
        assert score == 0.0
    
    # Token Overlap Tests
    
    def test_token_overlap_identical(self, scorer):
        """Test token overlap with identical texts."""
        text = "The quick brown fox"
        score = scorer.compute_token_overlap(text, text)
        assert score == 1.0
    
    def test_token_overlap_partial(self, scorer):
        """Test token overlap with partial match."""
        candidate = "quick brown fox"
        reference = "the quick brown lazy dog"
        score = scorer.compute_token_overlap(candidate, reference)
        assert 0.5 < score < 1.0
    
    def test_token_overlap_no_match(self, scorer):
        """Test token overlap with no common tokens."""
        candidate = "apple banana cherry"
        reference = "dog cat elephant"
        score = scorer.compute_token_overlap(candidate, reference)
        assert score == 0.0
    
    # Confidence Score Tests
    
    def test_confidence_score_with_citations(self, scorer):
        """Test confidence score with citations."""
        answer = "The revenue grew by 25% in Q4."
        citations = [
            Citation(
                chunk_id="chunk_1",
                text="In Q4, the company's revenue grew by 25%.",
                page=1,
                doc_name="report.pdf",
                block_type="paragraph"
            )
        ]
        
        score = scorer.compute_confidence_score(answer, citations)
        assert 0.0 <= score <= 1.0
        assert score > 0.3  # Should have reasonable confidence
    
    def test_confidence_score_no_citations(self, scorer):
        """Test confidence score with no citations."""
        score = scorer.compute_confidence_score("Some answer", [])
        assert score == 0.0
    
    def test_confidence_score_no_answer(self, scorer):
        """Test confidence score with empty answer."""
        citations = [
            Citation(
                chunk_id="chunk_1",
                text="Some text",
                page=1,
                doc_name="doc.pdf",
                block_type="paragraph"
            )
        ]
        score = scorer.compute_confidence_score("", citations)
        assert score == 0.0
    
    # Confidence Level Tests
    
    def test_confidence_level_high(self, scorer):
        """Test high confidence level."""
        level = scorer.get_confidence_level(0.8)
        assert level == "high"
        
        level = scorer.get_confidence_level(0.7)
        assert level == "high"
    
    def test_confidence_level_medium(self, scorer):
        """Test medium confidence level."""
        level = scorer.get_confidence_level(0.5)
        assert level == "medium"
        
        level = scorer.get_confidence_level(0.4)
        assert level == "medium"
    
    def test_confidence_level_low(self, scorer):
        """Test low confidence level."""
        level = scorer.get_confidence_level(0.3)
        assert level == "low"
        
        level = scorer.get_confidence_level(0.0)
        assert level == "low"
    
    # Citation Marker Removal Tests
    
    def test_remove_citation_markers(self, scorer):
        """Test citation marker removal."""
        text = "The answer is 42 [chunk_1] and also 43 [chunk_2]."
        clean = scorer._remove_citation_markers(text)
        assert "[chunk_" not in clean
        assert "42" in clean
        assert "43" in clean
    
    # Sentence Splitting Tests
    
    def test_split_sentences(self, scorer):
        """Test sentence splitting."""
        text = "First sentence. Second sentence! Third sentence?"
        sentences = scorer._split_sentences(text)
        assert len(sentences) == 3
    
    # Tokenization Tests
    
    def test_tokenize_removes_stopwords(self, scorer):
        """Test that tokenization removes stop words."""
        text = "The quick brown fox"
        tokens = scorer._tokenize(text)
        assert "the" not in tokens
        assert "quick" in tokens
        assert "brown" in tokens
        assert "fox" in tokens


class TestLCSAlgorithm:
    """Test suite for LCS algorithm."""
    
    @pytest.fixture
    def scorer(self):
        return ConfidenceScorer()
    
    def test_lcs_identical_sequences(self, scorer):
        """Test LCS with identical sequences."""
        seq = ["a", "b", "c", "d"]
        length = scorer._lcs_length(seq, seq)
        assert length == 4
    
    def test_lcs_partial_match(self, scorer):
        """Test LCS with partial match."""
        seq1 = ["a", "b", "c", "d"]
        seq2 = ["a", "x", "c", "y"]
        length = scorer._lcs_length(seq1, seq2)
        assert length == 2  # "a" and "c"
    
    def test_lcs_no_match(self, scorer):
        """Test LCS with no common elements."""
        seq1 = ["a", "b", "c"]
        seq2 = ["x", "y", "z"]
        length = scorer._lcs_length(seq1, seq2)
        assert length == 0
    
    def test_lcs_empty_sequence(self, scorer):
        """Test LCS with empty sequence."""
        length = scorer._lcs_length([], ["a", "b"])
        assert length == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


