#!/usr/bin/env python3
"""CI Quality Gates for Autonomous-GLM.

Runs quality checks for CI pipeline:
- Coverage threshold enforcement
- Lint check status
- Test pass rate validation

Usage:
    python scripts/ci_gates.py
    python scripts/ci_gates.py --gate coverage
    python scripts/ci_gates.py --gate lint
    python scripts/ci_gates.py --gate tests
"""
import argparse
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional


# Configuration
COVERAGE_THRESHOLD = 80.0  # Pragmatic threshold
PROJECT_ROOT = Path(__file__).parent.parent


def run_command(cmd: list[str], capture: bool = True) -> tuple[int, str, str]:
    """Run a command and return exit code, stdout, stderr."""
    result = subprocess.run(
        cmd,
        cwd=PROJECT_ROOT,
        capture_output=capture,
        text=True,
    )
    return result.returncode, result.stdout, result.stderr


def check_coverage() -> bool:
    """Check if coverage meets threshold."""
    print("🔍 Checking coverage threshold...")
    
    coverage_file = PROJECT_ROOT / "coverage.xml"
    
    if not coverage_file.exists():
        print("❌ Coverage file not found. Run tests with --cov first.")
        return False
    
    try:
        tree = ET.parse(coverage_file)
        root = tree.getroot()
        
        line_rate = float(root.attrib.get("line-rate", 0))
        coverage_pct = line_rate * 100
        
        print(f"   Coverage: {coverage_pct:.2f}%")
        print(f"   Threshold: {COVERAGE_THRESHOLD}%")
        
        if coverage_pct >= COVERAGE_THRESHOLD:
            print(f"✅ Coverage gate passed ({coverage_pct:.2f}% >= {COVERAGE_THRESHOLD}%)")
            return True
        else:
            print(f"❌ Coverage gate failed ({coverage_pct:.2f}% < {COVERAGE_THRESHOLD}%)")
            return False
            
    except Exception as e:
        print(f"❌ Error parsing coverage file: {e}")
        return False


def check_lint() -> bool:
    """Check if linting passes."""
    print("🔍 Running lint check...")
    
    # Check if ruff is available
    exit_code, stdout, stderr = run_command(["ruff", "--version"])
    if exit_code != 0:
        print("❌ ruff not installed. Run: pip install ruff")
        return False
    
    # Run ruff check
    exit_code, stdout, stderr = run_command([
        "ruff", "check", "src/", "tests/", "--output-format=concise"
    ])
    
    if exit_code == 0:
        print("✅ Lint check passed")
        return True
    else:
        print(f"❌ Lint check failed:\n{stdout}\n{stderr}")
        return False


def check_tests() -> bool:
    """Check if all tests pass."""
    print("🔍 Running test suite...")
    
    # Run pytest
    exit_code, stdout, stderr = run_command([
        "pytest", 
        "tests/unit/", 
        "tests/integration/",
        "-v", 
        "--tb=short",
        "-q"
    ])
    
    if exit_code == 0:
        print("✅ All tests passed")
        return True
    else:
        print(f"❌ Tests failed:\n{stdout[-2000:]}\n{stderr[-500:]}")
        return False


def check_all() -> bool:
    """Run all quality gates."""
    print("=" * 60)
    print("🚀 Running CI Quality Gates")
    print("=" * 60)
    
    results = {
        "lint": check_lint(),
        "tests": check_tests(),
        "coverage": check_coverage(),
    }
    
    print("\n" + "=" * 60)
    print("📊 Quality Gate Summary")
    print("=" * 60)
    
    for gate, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {gate}: {status}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n🎉 All quality gates passed!")
        return True
    else:
        print("\n❌ One or more quality gates failed")
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description="CI Quality Gates")
    parser.add_argument(
        "--gate",
        choices=["coverage", "lint", "tests", "all"],
        default="all",
        help="Specific gate to run (default: all)",
    )
    
    args = parser.parse_args()
    
    if args.gate == "coverage":
        success = check_coverage()
    elif args.gate == "lint":
        success = check_lint()
    elif args.gate == "tests":
        success = check_tests()
    else:
        success = check_all()
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())