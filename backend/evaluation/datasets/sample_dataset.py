"""
Sample dataset for testing the evaluation harness.

Phase 3: Provides a simple test dataset that can be used
without external dependencies.
"""

from typing import List
from evaluation.benchmark import QAExample


class SampleDataset:
    """
    Sample QA dataset for testing.
    
    Contains hand-crafted examples for validating the evaluation pipeline.
    """
    
    @staticmethod
    def get_examples() -> List[QAExample]:
        """
        Get sample QA examples.
        
        Returns:
            List of QAExample objects
        """
        return [
            # Factoid questions
            QAExample(
                id="factoid_1",
                question="What is the capital of France?",
                ground_truth_answer="Paris",
                relevant_chunk_ids=["chunk_1"],
                metadata={"category": "factoid", "difficulty": "easy"}
            ),
            QAExample(
                id="factoid_2",
                question="What year was Python created?",
                ground_truth_answer="1991",
                relevant_chunk_ids=["chunk_2"],
                metadata={"category": "factoid", "difficulty": "medium"}
            ),
            
            # Definition questions
            QAExample(
                id="definition_1",
                question="What is machine learning?",
                ground_truth_answer="Machine learning is a subset of artificial intelligence that enables computers to learn from data without being explicitly programmed.",
                relevant_chunk_ids=["chunk_3", "chunk_4"],
                metadata={"category": "definition", "difficulty": "medium"}
            ),
            
            # Explanation questions
            QAExample(
                id="explanation_1",
                question="How does ROUGE-L scoring work?",
                ground_truth_answer="ROUGE-L uses the longest common subsequence (LCS) between the candidate and reference text to compute precision and recall, then combines them into an F1 score.",
                relevant_chunk_ids=["chunk_5"],
                metadata={"category": "explanation", "difficulty": "hard"}
            ),
            
            # Comparison questions
            QAExample(
                id="comparison_1",
                question="What is the difference between extractive and generative QA?",
                ground_truth_answer="Extractive QA selects spans directly from the source text, while generative QA produces new text that may paraphrase or synthesize information from multiple sources.",
                relevant_chunk_ids=["chunk_6", "chunk_7"],
                metadata={"category": "comparison", "difficulty": "medium"}
            ),
            
            # Multi-hop questions
            QAExample(
                id="multihop_1",
                question="What technology is used for embeddings and what dimension are they?",
                ground_truth_answer="OpenAI text-embedding-3-large is used, producing 1536-dimensional vectors.",
                relevant_chunk_ids=["chunk_8", "chunk_9"],
                metadata={"category": "multi-hop", "difficulty": "hard"}
            ),
            
            # List questions
            QAExample(
                id="list_1",
                question="What are the phases of the project?",
                ground_truth_answer="The project has three phases: Phase 1 (core pipeline), Phase 2 (hybrid retrieval and reranking), and Phase 3 (confidence scoring and evaluation).",
                relevant_chunk_ids=["chunk_10"],
                metadata={"category": "list", "difficulty": "easy"}
            ),
            
            # Yes/No questions
            QAExample(
                id="yesno_1",
                question="Does the system support multi-hop queries?",
                ground_truth_answer="Yes, the system supports multi-hop queries through the query planner which detects complex questions and breaks them into sub-queries.",
                relevant_chunk_ids=["chunk_11"],
                metadata={"category": "yes-no", "difficulty": "easy"}
            ),
            
            # Document-specific questions
            QAExample(
                id="docspec_1",
                question="What is the confidence threshold for extractive fallback?",
                ground_truth_answer="The default confidence threshold is 0.4, below which the system triggers extractive fallback.",
                relevant_chunk_ids=["chunk_12"],
                metadata={"category": "document-specific", "difficulty": "medium"}
            ),
            
            # Complex reasoning
            QAExample(
                id="complex_1",
                question="Why might the system choose extractive over generative answers?",
                ground_truth_answer="The system chooses extractive answers when the generative answer has low confidence (below threshold), indicating poor citation support. Extractive answers provide direct quotes from the source, reducing hallucination risk.",
                relevant_chunk_ids=["chunk_13", "chunk_14", "chunk_15"],
                metadata={"category": "reasoning", "difficulty": "hard"}
            ),
        ]
    
    @staticmethod
    def get_subset(
        category: str = None,
        difficulty: str = None,
        max_examples: int = None
    ) -> List[QAExample]:
        """
        Get a filtered subset of examples.
        
        Args:
            category: Filter by category (factoid, definition, etc.)
            difficulty: Filter by difficulty (easy, medium, hard)
            max_examples: Maximum number of examples to return
            
        Returns:
            Filtered list of QAExample objects
        """
        examples = SampleDataset.get_examples()
        
        if category:
            examples = [e for e in examples if e.metadata.get("category") == category]
        
        if difficulty:
            examples = [e for e in examples if e.metadata.get("difficulty") == difficulty]
        
        if max_examples:
            examples = examples[:max_examples]
        
        return examples


