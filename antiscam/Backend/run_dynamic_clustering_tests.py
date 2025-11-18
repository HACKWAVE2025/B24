"""
Test runner for dynamic clustering logic
Run this script to test the new report scam button and feedback-based clustering
"""
import subprocess
import sys
import os

def run_tests():
    """Run pytest tests for dynamic clustering"""
    print("=" * 70)
    print("Running Dynamic Clustering Tests")
    print("=" * 70)
    print()
    
    # Change to Backend directory
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(backend_dir)
    
    # Run pytest
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "test_threat_intel_logic.py", "-v", "--tb=short"],
            cwd=backend_dir,
            capture_output=False
        )
        return result.returncode
    except FileNotFoundError:
        print("ERROR: pytest not found. Install it with: pip install pytest")
        return 1
    except Exception as e:
        print(f"ERROR running tests: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(run_tests())

