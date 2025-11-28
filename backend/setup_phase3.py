"""
Phase 3 Setup Script

Verifies all Phase 3 dependencies and configurations are properly installed.

Usage:
    python setup_phase3.py
"""

import sys
import os
from pathlib import Path


def check_python_version():
    """Check Python version (3.10+ required)."""
    version = sys.version_info
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 10):
        print("⚠️  Warning: Python 3.10+ recommended (you have {}.{})".format(
            version.major, version.minor
        ))
        return False
    
    print("✅ Python version OK")
    return True


def check_dependencies():
    """Check that all Phase 3 dependencies are installed."""
    print("\nChecking Phase 3 dependencies...")
    
    dependencies = [
        ("rouge_score", "rouge-score"),
        ("transformers", "transformers"),
        ("torch", "torch"),
        ("datasets", "datasets (optional, for evaluation)"),
    ]
    
    all_ok = True
    
    for module_name, display_name in dependencies:
        try:
            __import__(module_name)
            print(f"  ✅ {display_name}")
        except ImportError:
            # datasets is optional
            if module_name == "datasets":
                print(f"  ⚠️  {display_name} - optional, skip if not evaluating")
            else:
                print(f"  ❌ {display_name} - not installed")
                all_ok = False
    
    return all_ok


def check_models():
    """Check that required models can be loaded."""
    print("\nChecking models...")
    
    # Check DistilBERT for extractive QA
    print("  Loading DistilBERT for extractive QA...")
    try:
        from transformers import AutoModelForQuestionAnswering, AutoTokenizer
        
        model_name = "distilbert-base-uncased-distilled-squad"
        
        # This will download the model if not cached
        print(f"    Model: {model_name}")
        print("    (This may take a moment on first run...)")
        
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForQuestionAnswering.from_pretrained(model_name)
        
        print("  ✅ DistilBERT loaded successfully")
        
        # Clean up
        del model
        del tokenizer
        
        return True
        
    except Exception as e:
        print(f"  ❌ Failed to load DistilBERT: {e}")
        return False


def check_config():
    """Check Phase 3 configuration variables."""
    print("\nChecking configuration...")
    
    # Add parent to path
    sys.path.insert(0, str(Path(__file__).parent))
    
    try:
        from utils.config import config
        
        phase3_vars = [
            ("CONFIDENCE_THRESHOLD", config.CONFIDENCE_THRESHOLD),
            ("ENABLE_EXTRACTIVE_FALLBACK", config.ENABLE_EXTRACTIVE_FALLBACK),
            ("EXTRACTIVE_MODEL", config.EXTRACTIVE_MODEL),
            ("MAX_REGENERATION_ATTEMPTS", config.MAX_REGENERATION_ATTEMPTS),
        ]
        
        for name, value in phase3_vars:
            print(f"  {name}: {value}")
        
        print("  ✅ Phase 3 configuration loaded")
        return True
        
    except Exception as e:
        print(f"  ❌ Configuration error: {e}")
        return False


def check_services():
    """Check that Phase 3 services can be imported."""
    print("\nChecking services...")
    
    services = [
        ("services.confidence_service", "ConfidenceScorer"),
        ("services.extractive_qa_service", "ExtractiveQAService"),
    ]
    
    all_ok = True
    
    for module_name, class_name in services:
        try:
            module = __import__(module_name, fromlist=[class_name])
            cls = getattr(module, class_name)
            print(f"  ✅ {class_name}")
        except Exception as e:
            print(f"  ❌ {class_name}: {e}")
            all_ok = False
    
    return all_ok


def check_evaluation():
    """Check that evaluation module can be imported."""
    print("\nChecking evaluation module...")
    
    try:
        from evaluation import (
            compute_exact_match,
            compute_f1_score,
            compute_recall_at_k,
            compute_ndcg,
            EvaluationMetrics,
            Benchmark
        )
        
        # Quick test of metrics
        em = compute_exact_match("hello world", "hello world")
        f1 = compute_f1_score("hello world", "hello there world")
        
        print(f"  Test EM score: {em}")
        print(f"  Test F1 score: {f1:.4f}")
        print("  ✅ Evaluation module OK")
        return True
        
    except Exception as e:
        print(f"  ❌ Evaluation module error: {e}")
        return False


def run_quick_test():
    """Run a quick confidence scoring test."""
    print("\nRunning quick confidence test...")
    
    try:
        from services.confidence_service import ConfidenceScorer
        
        scorer = ConfidenceScorer()
        
        # Test ROUGE-L
        candidate = "The quick brown fox jumps over the lazy dog."
        reference = "A quick brown fox jumped over the lazy dog."
        
        rouge_l = scorer.compute_rouge_l(candidate, reference)
        print(f"  ROUGE-L score: {rouge_l:.4f}")
        
        # Test confidence level
        level = scorer.get_confidence_level(rouge_l)
        print(f"  Confidence level: {level}")
        
        print("  ✅ Confidence scoring working")
        return True
        
    except Exception as e:
        print(f"  ❌ Confidence test failed: {e}")
        return False


def main():
    print("=" * 60)
    print("PHASE 3 SETUP VERIFICATION")
    print("=" * 60)
    print()
    
    results = []
    
    # Run all checks
    results.append(("Python version", check_python_version()))
    results.append(("Dependencies", check_dependencies()))
    results.append(("Configuration", check_config()))
    results.append(("Services", check_services()))
    results.append(("Evaluation module", check_evaluation()))
    results.append(("Quick test", run_quick_test()))
    
    # Check models last (slow)
    print("\nDo you want to download/verify the DistilBERT model? (y/N): ", end="")
    try:
        response = input().strip().lower()
        if response == 'y':
            results.append(("Models", check_models()))
        else:
            print("Skipping model check...")
    except:
        print("Skipping model check (non-interactive mode)...")
    
    # Summary
    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {name}: {status}")
        if not passed:
            all_passed = False
    
    print()
    if all_passed:
        print("✅ Phase 3 setup complete! All checks passed.")
        print()
        print("Next steps:")
        print("  1. Start the backend: uvicorn index:app --reload --port 8000")
        print("  2. Start the frontend: cd ../frontend && npm run dev")
        print("  3. Upload a document and test confidence scoring")
        print("  4. Run evaluation: python evaluate_phase3.py --dataset sample")
    else:
        print("⚠️  Some checks failed. Please resolve the issues above.")
        print()
        print("To install missing dependencies:")
        print("  pip install rouge-score transformers datasets")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())


