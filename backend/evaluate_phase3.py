"""
Phase 3 Evaluation Script

Runs evaluation benchmarks on the Document Q&A system.

Usage:
    python evaluate_phase3.py --dataset sample
    python evaluate_phase3.py --dataset sample --ablation
    python evaluate_phase3.py --help
"""

import asyncio
import argparse
import json
import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from evaluation.benchmark import Benchmark, QAExample
from evaluation.datasets.sample_dataset import SampleDataset
from evaluation.metrics import EvaluationMetrics


async def query_system(question: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Query the Document Q&A system.
    
    Args:
        question: Question to ask
        config: Configuration options
        
    Returns:
        Dict with answer, retrieved_ids, confidence_score, answer_type
    """
    import httpx
    
    api_url = config.get("api_url", "http://localhost:8000")
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{api_url}/api/query",
                json={"query": question}
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract retrieved chunk IDs from citations
                retrieved_ids = [c["chunk_id"] for c in data.get("citations", [])]
                
                return {
                    "answer": data.get("answer", ""),
                    "retrieved_ids": retrieved_ids,
                    "confidence_score": data.get("confidence_score", 0.0),
                    "answer_type": data.get("answer_type", "generative")
                }
            else:
                print(f"Error querying system: {response.status_code}")
                return {
                    "answer": "",
                    "retrieved_ids": [],
                    "confidence_score": 0.0,
                    "answer_type": "generative"
                }
                
    except Exception as e:
        print(f"Error querying system: {e}")
        return {
            "answer": "",
            "retrieved_ids": [],
            "confidence_score": 0.0,
            "answer_type": "generative"
        }


async def run_evaluation(
    dataset: str = "sample",
    output_path: Optional[str] = None,
    api_url: str = "http://localhost:8000"
):
    """
    Run evaluation on specified dataset.
    
    Args:
        dataset: Dataset to use (sample, custom)
        output_path: Path to save results
        api_url: Backend API URL
    """
    print("=" * 60)
    print("PHASE 3 EVALUATION")
    print("=" * 60)
    print()
    
    # Load examples
    if dataset == "sample":
        examples = SampleDataset.get_examples()
        print(f"Loaded {len(examples)} sample examples")
    else:
        # Try to load from JSON file
        if os.path.exists(dataset):
            with open(dataset, 'r') as f:
                data = json.load(f)
            examples = [
                QAExample(
                    id=item.get("id", str(i)),
                    question=item["question"],
                    ground_truth_answer=item["answer"],
                    relevant_chunk_ids=item.get("relevant_chunks", [])
                )
                for i, item in enumerate(data)
            ]
            print(f"Loaded {len(examples)} examples from {dataset}")
        else:
            print(f"Dataset not found: {dataset}")
            return
    
    # Create benchmark
    benchmark = Benchmark(
        name=f"phase3_{dataset}",
        query_function=query_system
    )
    
    # Run evaluation
    config = {"api_url": api_url}
    
    print()
    print("Running evaluation...")
    print("-" * 40)
    
    result = await benchmark.run(examples, config)
    
    # Print results
    print()
    print("=" * 60)
    print("RESULTS")
    print("=" * 60)
    print()
    print(f"Dataset: {dataset}")
    print(f"Examples: {result.num_examples}")
    print(f"Runtime: {result.runtime_seconds:.2f}s")
    print()
    print("Average Metrics:")
    print("-" * 40)
    
    metrics = result.avg_metrics.to_dict()
    for key, value in metrics.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.4f}")
        else:
            print(f"  {key}: {value}")
    
    # Save results
    if output_path:
        result.save(output_path)
        print()
        print(f"Results saved to: {output_path}")
    
    return result


async def run_ablation(
    api_url: str = "http://localhost:8000",
    output_dir: str = "evaluation_results"
):
    """
    Run ablation study with different configurations.
    
    Args:
        api_url: Backend API URL
        output_dir: Directory to save results
    """
    print("=" * 60)
    print("PHASE 3 ABLATION STUDY")
    print("=" * 60)
    print()
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Load sample dataset
    examples = SampleDataset.get_subset(max_examples=5)
    print(f"Using {len(examples)} examples for ablation")
    
    # Define configurations to test
    configs = [
        {
            "name": "baseline",
            "description": "Default configuration"
        },
        # Note: Additional ablation configs would require
        # modifying the backend to accept config parameters
    ]
    
    benchmark = Benchmark(
        name="ablation_study",
        query_function=query_system
    )
    
    results = []
    
    for config in configs:
        print()
        print(f"Testing configuration: {config['name']}")
        print("-" * 40)
        
        config["api_url"] = api_url
        result = await benchmark.run(examples, config)
        results.append(result)
        
        # Save individual result
        output_path = os.path.join(output_dir, f"ablation_{config['name']}.json")
        result.save(output_path)
    
    # Generate ablation report
    report = benchmark.generate_ablation_report()
    print()
    print(report)
    
    # Save report
    report_path = os.path.join(output_dir, "ablation_report.txt")
    with open(report_path, 'w') as f:
        f.write(report)
    print(f"\nReport saved to: {report_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Phase 3 Evaluation Script for Document Q&A System"
    )
    
    parser.add_argument(
        "--dataset",
        type=str,
        default="sample",
        help="Dataset to evaluate on (sample, or path to JSON file)"
    )
    
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Path to save evaluation results"
    )
    
    parser.add_argument(
        "--api-url",
        type=str,
        default="http://localhost:8000",
        help="Backend API URL"
    )
    
    parser.add_argument(
        "--ablation",
        action="store_true",
        help="Run ablation study"
    )
    
    args = parser.parse_args()
    
    if args.ablation:
        asyncio.run(run_ablation(
            api_url=args.api_url,
            output_dir=args.output or "evaluation_results"
        ))
    else:
        asyncio.run(run_evaluation(
            dataset=args.dataset,
            output_path=args.output,
            api_url=args.api_url
        ))


if __name__ == "__main__":
    main()


