"""
Benchmarking framework for the Document Q&A system.

Phase 3: Provides automated evaluation on QA datasets
with support for ablation studies.
"""

import json
import time
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from pathlib import Path
import logging

from .metrics import EvaluationMetrics, evaluate_answer

logger = logging.getLogger(__name__)


@dataclass
class QAExample:
    """A single QA example for evaluation."""
    
    id: str
    question: str
    ground_truth_answer: str
    context: Optional[str] = None
    relevant_chunk_ids: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BenchmarkResult:
    """Results from a benchmark run."""
    
    name: str
    timestamp: str
    num_examples: int
    avg_metrics: EvaluationMetrics
    per_example_metrics: List[Dict[str, Any]]
    config: Dict[str, Any]
    runtime_seconds: float
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "timestamp": self.timestamp,
            "num_examples": self.num_examples,
            "avg_metrics": self.avg_metrics.to_dict(),
            "per_example_metrics": self.per_example_metrics,
            "config": self.config,
            "runtime_seconds": self.runtime_seconds
        }
    
    def save(self, path: str) -> None:
        """Save results to JSON file."""
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
        logger.info(f"Saved benchmark results to {path}")
    
    @classmethod
    def load(cls, path: str) -> 'BenchmarkResult':
        """Load results from JSON file."""
        with open(path, 'r') as f:
            data = json.load(f)
        
        return cls(
            name=data["name"],
            timestamp=data["timestamp"],
            num_examples=data["num_examples"],
            avg_metrics=EvaluationMetrics(**data["avg_metrics"]),
            per_example_metrics=data["per_example_metrics"],
            config=data["config"],
            runtime_seconds=data["runtime_seconds"]
        )


class Benchmark:
    """
    Benchmark runner for QA system evaluation.
    
    Supports:
    - Running evaluation on QA datasets
    - Computing standard metrics (EM, F1, Recall@K, nDCG)
    - Ablation studies with different configurations
    """
    
    def __init__(
        self,
        name: str = "default",
        query_function: Optional[Callable] = None
    ):
        """
        Initialize benchmark.
        
        Args:
            name: Name for this benchmark run
            query_function: Function to query the system (takes question, returns prediction)
        """
        self.name = name
        self.query_function = query_function
        self.results: List[BenchmarkResult] = []
    
    def load_examples_from_json(self, path: str) -> List[QAExample]:
        """
        Load QA examples from JSON file.
        
        Expected format:
        [
            {
                "id": "1",
                "question": "What is...?",
                "answer": "The answer is...",
                "relevant_chunks": ["chunk_1", "chunk_2"]
            },
            ...
        ]
        
        Args:
            path: Path to JSON file
            
        Returns:
            List of QAExample objects
        """
        with open(path, 'r') as f:
            data = json.load(f)
        
        examples = []
        for item in data:
            examples.append(QAExample(
                id=item.get("id", str(len(examples))),
                question=item["question"],
                ground_truth_answer=item["answer"],
                context=item.get("context"),
                relevant_chunk_ids=item.get("relevant_chunks", []),
                metadata=item.get("metadata", {})
            ))
        
        logger.info(f"Loaded {len(examples)} examples from {path}")
        return examples
    
    def create_sample_dataset(self) -> List[QAExample]:
        """
        Create a sample dataset for testing.
        
        Returns:
            List of sample QA examples
        """
        return [
            QAExample(
                id="sample_1",
                question="What is the main topic of this document?",
                ground_truth_answer="The main topic is document question answering.",
                relevant_chunk_ids=["chunk_1"]
            ),
            QAExample(
                id="sample_2",
                question="What technology is used for embeddings?",
                ground_truth_answer="OpenAI text-embedding-3-large is used for embeddings.",
                relevant_chunk_ids=["chunk_2", "chunk_3"]
            ),
            QAExample(
                id="sample_3",
                question="How does the confidence scoring work?",
                ground_truth_answer="Confidence scoring uses ROUGE-L to measure citation overlap.",
                relevant_chunk_ids=["chunk_4"]
            ),
        ]
    
    async def run(
        self,
        examples: List[QAExample],
        config: Optional[Dict[str, Any]] = None
    ) -> BenchmarkResult:
        """
        Run benchmark on a list of examples.
        
        Args:
            examples: List of QA examples to evaluate
            config: Configuration for this run (for ablation studies)
            
        Returns:
            BenchmarkResult with metrics
        """
        config = config or {}
        start_time = time.time()
        
        all_metrics = []
        per_example = []
        
        for i, example in enumerate(examples):
            logger.info(f"Processing example {i+1}/{len(examples)}: {example.id}")
            
            try:
                # Query the system
                result = await self._query_system(example.question, config)
                
                prediction = result.get("answer", "")
                retrieved_ids = result.get("retrieved_ids", [])
                confidence = result.get("confidence_score", 0.0)
                answer_type = result.get("answer_type", "generative")
                
                # Compute metrics
                metrics = evaluate_answer(
                    prediction=prediction,
                    ground_truth=example.ground_truth_answer,
                    retrieved_ids=retrieved_ids,
                    relevant_ids=set(example.relevant_chunk_ids),
                    confidence_score=confidence,
                    answer_type=answer_type
                )
                
                all_metrics.append(metrics)
                per_example.append({
                    "id": example.id,
                    "question": example.question,
                    "ground_truth": example.ground_truth_answer,
                    "prediction": prediction,
                    "metrics": metrics.to_dict()
                })
                
            except Exception as e:
                logger.error(f"Error processing example {example.id}: {e}")
                # Add zero metrics for failed examples
                all_metrics.append(EvaluationMetrics())
                per_example.append({
                    "id": example.id,
                    "error": str(e)
                })
        
        runtime = time.time() - start_time
        
        # Compute average metrics
        avg_metrics = EvaluationMetrics.average(all_metrics)
        
        result = BenchmarkResult(
            name=self.name,
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            num_examples=len(examples),
            avg_metrics=avg_metrics,
            per_example_metrics=per_example,
            config=config,
            runtime_seconds=runtime
        )
        
        self.results.append(result)
        
        logger.info(f"Benchmark complete: {len(examples)} examples in {runtime:.2f}s")
        logger.info(f"Average metrics: EM={avg_metrics.exact_match:.3f}, F1={avg_metrics.f1_score:.3f}")
        
        return result
    
    async def _query_system(
        self,
        question: str,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Query the QA system.
        
        Args:
            question: The question to ask
            config: Configuration for the query
            
        Returns:
            Dict with answer, retrieved_ids, confidence_score, answer_type
        """
        if self.query_function is not None:
            return await self.query_function(question, config)
        
        # Default: return empty result
        return {
            "answer": "",
            "retrieved_ids": [],
            "confidence_score": 0.0,
            "answer_type": "generative"
        }
    
    def compare_results(
        self,
        result1: BenchmarkResult,
        result2: BenchmarkResult
    ) -> Dict[str, float]:
        """
        Compare two benchmark results.
        
        Args:
            result1: First benchmark result
            result2: Second benchmark result
            
        Returns:
            Dict with metric differences (result2 - result1)
        """
        m1 = result1.avg_metrics.to_dict()
        m2 = result2.avg_metrics.to_dict()
        
        diffs = {}
        for key in m1:
            if isinstance(m1[key], (int, float)) and isinstance(m2[key], (int, float)):
                diffs[key] = m2[key] - m1[key]
        
        return diffs
    
    def generate_ablation_report(self) -> str:
        """
        Generate ablation study report from all results.
        
        Returns:
            Formatted report string
        """
        if not self.results:
            return "No results available."
        
        lines = [
            "=" * 60,
            "ABLATION STUDY REPORT",
            "=" * 60,
            ""
        ]
        
        for result in self.results:
            lines.append(f"Configuration: {result.name}")
            lines.append(f"  Config: {result.config}")
            lines.append(f"  Examples: {result.num_examples}")
            lines.append(f"  Runtime: {result.runtime_seconds:.2f}s")
            lines.append("")
            lines.append("  Metrics:")
            
            m = result.avg_metrics.to_dict()
            for key, value in m.items():
                if isinstance(value, float):
                    lines.append(f"    {key}: {value:.4f}")
                else:
                    lines.append(f"    {key}: {value}")
            
            lines.append("-" * 40)
        
        return "\n".join(lines)


