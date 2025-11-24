"""
Phase 2 Setup Script

This script:
1. Verifies all Phase 2 dependencies are installed
2. Downloads required spaCy model
3. Checks Elasticsearch connection
4. Validates configuration
"""

import subprocess
import sys
import os


def run_command(command, description):
    """Run a shell command and report results."""
    print(f"\n{'='*60}")
    print(f"⚙️  {description}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            capture_output=True,
            text=True
        )
        print(f"✅ {description} completed successfully")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed")
        print(f"Error: {e.stderr}")
        return False


def check_python_version():
    """Verify Python version is 3.11+"""
    print("\n🐍 Checking Python version...")
    version = sys.version_info
    
    if version.major == 3 and version.minor >= 11:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} - OK")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} - Need 3.11+")
        return False


def install_dependencies():
    """Install Python dependencies from requirements.txt"""
    return run_command(
        f"{sys.executable} -m pip install -r requirements.txt",
        "Installing Python dependencies"
    )


def download_spacy_model():
    """Download spaCy English model"""
    return run_command(
        f"{sys.executable} -m spacy download en_core_web_sm",
        "Downloading spaCy English model (en_core_web_sm)"
    )


def verify_spacy_model():
    """Verify spaCy model is available"""
    print("\n🔍 Verifying spaCy model...")
    
    try:
        import spacy
        nlp = spacy.load("en_core_web_sm")
        print("✅ spaCy model loaded successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to load spaCy model: {e}")
        return False


def check_elasticsearch():
    """Check if Elasticsearch is accessible"""
    print("\n🔍 Checking Elasticsearch connection...")
    
    try:
        from utils import config
        from elasticsearch import Elasticsearch
        
        es = Elasticsearch([config.ELASTICSEARCH_URL], request_timeout=5)
        
        if es.ping():
            print(f"✅ Elasticsearch is accessible at {config.ELASTICSEARCH_URL}")
            info = es.info()
            print(f"   Version: {info['version']['number']}")
            return True
        else:
            print(f"⚠️  Elasticsearch is not responding at {config.ELASTICSEARCH_URL}")
            print("   Phase 2 will work without it, but BM25 retrieval will be disabled")
            return False
    except Exception as e:
        print(f"⚠️  Could not connect to Elasticsearch: {e}")
        print("   Phase 2 will work without it, but BM25 retrieval will be disabled")
        return False


def verify_env_vars():
    """Verify required environment variables are set"""
    print("\n🔍 Checking environment variables...")
    
    try:
        from utils import config
        
        required_vars = {
            "OPENAI_API_KEY": config.OPENAI_API_KEY,
            "UPSTASH_VECTOR_REST_URL": config.UPSTASH_VECTOR_REST_URL,
            "UPSTASH_VECTOR_REST_TOKEN": config.UPSTASH_VECTOR_REST_TOKEN,
            "UNSTRUCTURED_API_KEY": config.UNSTRUCTURED_API_KEY,
        }
        
        missing = []
        for var_name, var_value in required_vars.items():
            if not var_value:
                missing.append(var_name)
                print(f"❌ {var_name} - Not set")
            else:
                print(f"✅ {var_name} - Set")
        
        if missing:
            print(f"\n⚠️  Missing required variables: {', '.join(missing)}")
            print("   Please check your .env file")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Error checking environment variables: {e}")
        return False


def print_summary(results):
    """Print setup summary"""
    print("\n" + "="*60)
    print("📊 SETUP SUMMARY")
    print("="*60)
    
    for task, success in results.items():
        status = "✅" if success else "❌"
        print(f"{status} {task}")
    
    all_required_success = all([
        results.get("Python Version", False),
        results.get("Dependencies", False),
        results.get("spaCy Model", False),
        results.get("Environment Variables", False)
    ])
    
    if all_required_success:
        print("\n🎉 Phase 2 setup complete! You're ready to go.")
        print("\nTo start the backend:")
        print("  cd backend")
        print("  uvicorn index:app --reload --port 8000")
        
        if not results.get("Elasticsearch", False):
            print("\n⚠️  Note: Elasticsearch is not running. Phase 2 will work with")
            print("   dense retrieval only. To enable BM25 lexical retrieval:")
            print("   1. Install Elasticsearch: https://www.elastic.co/downloads/elasticsearch")
            print("   2. Start Elasticsearch: elasticsearch")
            print("   3. Update ELASTICSEARCH_URL in .env if needed")
    else:
        print("\n❌ Setup incomplete. Please fix the issues above and run again.")
        sys.exit(1)


def main():
    """Main setup routine"""
    print("""
╔════════════════════════════════════════════════════════════╗
║                                                            ║
║     Intelligent Document Q&A System - Phase 2 Setup       ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
""")
    
    results = {}
    
    # Check Python version
    results["Python Version"] = check_python_version()
    
    if not results["Python Version"]:
        print("\n❌ Please upgrade to Python 3.11 or higher")
        sys.exit(1)
    
    # Install dependencies
    results["Dependencies"] = install_dependencies()
    
    # Download and verify spaCy model
    if results["Dependencies"]:
        download_success = download_spacy_model()
        results["spaCy Model"] = verify_spacy_model() if download_success else False
    else:
        results["spaCy Model"] = False
    
    # Check Elasticsearch (optional but recommended)
    results["Elasticsearch"] = check_elasticsearch()
    
    # Verify environment variables
    results["Environment Variables"] = verify_env_vars()
    
    # Print summary
    print_summary(results)


if __name__ == "__main__":
    main()

