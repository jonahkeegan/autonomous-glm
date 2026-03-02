#!/usr/bin/env python3
"""
Autonomous-GLM Health Check Script.

Comprehensive startup validation that verifies all foundation components
are correctly initialized and operational.

Usage:
    python scripts/health_check.py
    
Exit codes:
    0 - All checks passed (healthy)
    1 - One or more checks failed (unhealthy)
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import NamedTuple

# Add project root to path for src module imports
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))


class CheckResult(NamedTuple):
    """Result of a single health check."""
    category: str
    passed: bool
    message: str
    details: list[str] = []


class HealthChecker:
    """Runs all health checks and generates reports."""
    
    def __init__(self):
        self.results: list[CheckResult] = []
        self.project_root = self._find_project_root()
    
    def _find_project_root(self) -> Path:
        """Find the project root directory."""
        current = Path(__file__).resolve()
        while current.parent != current:
            if (current / "config").exists() and (current / "src").exists():
                return current
            current = current.parent
        raise RuntimeError("Could not find project root")
    
    def run_all_checks(self) -> bool:
        """Run all health checks and return overall status."""
        print("\nAutonomous GLM Health Check")
        print("=" * 40)
        print()
        
        # Run each category of checks
        self._check_schemas()
        self._check_database()
        self._check_configuration()
        self._check_directories()
        self._check_design_system()
        self._check_memory_bank()
        
        # Print results
        all_passed = self._print_results()
        
        # Generate report
        self._generate_report()
        
        return all_passed
    
    def _check_schemas(self):
        """Validate all JSON schemas."""
        interfaces_dir = self.project_root / "interfaces"
        
        if not interfaces_dir.exists():
            self.results.append(CheckResult(
                category="Schema Validation",
                passed=False,
                message="Interfaces directory not found"
            ))
            return
        
        schema_files = list(interfaces_dir.glob("*.schema.json"))
        expected_schemas = [
            "audit-complete.schema.json",
            "design-proposal.schema.json",
            "dispute.schema.json",
            "human-required.schema.json",
        ]
        
        found = [s.name for s in schema_files]
        missing = [s for s in expected_schemas if s not in found]
        
        if missing:
            self.results.append(CheckResult(
                category="Schema Validation",
                passed=False,
                message=f"Missing schemas: {missing}",
                details=[f"Missing: {m}" for m in missing]
            ))
            return
        
        # Validate each schema is valid JSON
        invalid = []
        for schema_file in schema_files:
            try:
                with open(schema_file) as f:
                    json.load(f)
            except json.JSONDecodeError as e:
                invalid.append(f"{schema_file.name}: {e}")
        
        if invalid:
            self.results.append(CheckResult(
                category="Schema Validation",
                passed=False,
                message=f"Invalid JSON in schemas",
                details=invalid
            ))
        else:
            self.results.append(CheckResult(
                category="Schema Validation",
                passed=True,
                message=f"{len(schema_files)}/4 schemas valid"
            ))
    
    def _check_database(self):
        """Validate database initialization."""
        try:
            from src.db import is_database_initialized, get_table_names
            
            # Check default database location
            db_path = self.project_root / "data" / "autonomous_glm.db"
            
            if db_path.exists():
                tables = get_table_names(db_path)
                self.results.append(CheckResult(
                    category="Database",
                    passed=True,
                    message=f"Connected, {len(tables)} tables",
                    details=[f"Tables: {', '.join(tables[:5])}..."]
                ))
            else:
                # Database not yet created - this is OK for fresh installs
                self.results.append(CheckResult(
                    category="Database",
                    passed=True,
                    message="Not initialized (fresh install)",
                    details=["Run init_database() to create"]
                ))
        except ImportError as e:
            self.results.append(CheckResult(
                category="Database",
                passed=False,
                message=f"Import error: {e}"
            ))
        except Exception as e:
            self.results.append(CheckResult(
                category="Database",
                passed=False,
                message=f"Error: {e}"
            ))
    
    def _check_configuration(self):
        """Validate configuration loading."""
        try:
            from src.config import load_config, clear_config
            
            clear_config()
            config = load_config()
            
            env = config.app.environment.value
            self.results.append(CheckResult(
                category="Configuration",
                passed=True,
                message=f"Loaded ({env})",
                details=[f"App: {config.app.name} v{config.app.version}"]
            ))
        except Exception as e:
            self.results.append(CheckResult(
                category="Configuration",
                passed=False,
                message=f"Error: {e}"
            ))
    
    def _check_directories(self):
        """Validate directory structure."""
        required_dirs = [
            "config",
            "data",
            "data/artifacts",
            "data/artifacts/screenshots",
            "data/artifacts/videos",
            "data/artifacts/context",
            "design_system",
            "memory-bank",
            "interfaces",
            "output",
            "output/reports",
            "logs",
            "src",
            "src/db",
            "src/config",
            "tests",
            "tests/unit",
        ]
        
        missing = []
        for dir_path in required_dirs:
            full_path = self.project_root / dir_path
            if not full_path.exists():
                missing.append(dir_path)
        
        if missing:
            self.results.append(CheckResult(
                category="Directories",
                passed=False,
                message=f"Missing: {len(missing)} directories",
                details=missing
            ))
        else:
            self.results.append(CheckResult(
                category="Directories",
                passed=True,
                message=f"{len(required_dirs)}/{len(required_dirs)} directories ready"
            ))
    
    def _check_design_system(self):
        """Validate design system files."""
        design_system_dir = self.project_root / "design_system"
        
        required_files = ["tokens.md", "components.md", "standards.md"]
        
        missing = []
        empty = []
        
        for file_name in required_files:
            file_path = design_system_dir / file_name
            if not file_path.exists():
                missing.append(file_name)
            elif len(file_path.read_text().strip()) < 50:
                empty.append(file_name)
        
        if missing:
            self.results.append(CheckResult(
                category="Design System",
                passed=False,
                message=f"Missing: {missing}",
                details=[f"Missing: {m}" for m in missing]
            ))
        elif empty:
            self.results.append(CheckResult(
                category="Design System",
                passed=True,
                message=f"{len(required_files)}/{len(required_files)} files (some empty)"
            ))
        else:
            self.results.append(CheckResult(
                category="Design System",
                passed=True,
                message=f"{len(required_files)}/{len(required_files)} files parseable"
            ))
    
    def _check_memory_bank(self):
        """Validate memory bank files."""
        memory_bank_dir = self.project_root / "memory-bank"
        
        required_files = [
            "active-context.md",
            "skill-matrix.json",
            "audit-patterns.md",
            "mistakes.md",
            "agent-feedback.md",
            "consolidated-learnings.md",
            "README.md",
        ]
        
        missing = []
        invalid_json = []
        
        for file_name in required_files:
            file_path = memory_bank_dir / file_name
            if not file_path.exists():
                missing.append(file_name)
            elif file_name.endswith(".json"):
                try:
                    with open(file_path) as f:
                        json.load(f)
                except json.JSONDecodeError:
                    invalid_json.append(file_name)
        
        if missing:
            self.results.append(CheckResult(
                category="Memory Bank",
                passed=False,
                message=f"Missing: {missing}",
                details=[f"Missing: {m}" for m in missing]
            ))
        elif invalid_json:
            self.results.append(CheckResult(
                category="Memory Bank",
                passed=False,
                message=f"Invalid JSON: {invalid_json}"
            ))
        else:
            self.results.append(CheckResult(
                category="Memory Bank",
                passed=True,
                message=f"{len(required_files)}/{len(required_files)} files valid"
            ))
    
    def _print_results(self) -> bool:
        """Print results to terminal with status indicators."""
        all_passed = True
        
        for result in self.results:
            status = "✓" if result.passed else "✗"
            color = "\033[92m" if result.passed else "\033[91m"
            reset = "\033[0m"
            
            print(f"[{color}{status}{reset}] {result.category:<24} {result.message}")
            
            if not result.passed:
                all_passed = False
                for detail in result.details:
                    print(f"    - {detail}")
        
        print()
        
        if all_passed:
            print(f"\033[92mStatus: HEALTHY\033[0m")
        else:
            print(f"\033[91mStatus: UNHEALTHY\033[0m")
        
        return all_passed
    
    def _generate_report(self):
        """Generate Markdown health check report."""
        output_dir = self.project_root / "output" / "reports"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        report_path = output_dir / "health_check.md"
        
        lines = [
            "# Autonomous GLM Health Check Report",
            "",
            f"**Generated:** {datetime.now().isoformat()}",
            f"**Project Root:** {self.project_root}",
            "",
            "## Summary",
            "",
        ]
        
        passed = sum(1 for r in self.results if r.passed)
        total = len(self.results)
        
        lines.append(f"- **Checks Passed:** {passed}/{total}")
        lines.append(f"- **Status:** {'HEALTHY' if passed == total else 'UNHEALTHY'}")
        lines.append("")
        
        lines.append("## Details")
        lines.append("")
        
        for result in self.results:
            status = "✅" if result.passed else "❌"
            lines.append(f"### {status} {result.category}")
            lines.append("")
            lines.append(f"**Message:** {result.message}")
            lines.append("")
            
            if result.details:
                lines.append("**Details:**")
                lines.append("")
                for detail in result.details:
                    lines.append(f"- {detail}")
                lines.append("")
        
        # Add environment section
        lines.append("## Environment")
        lines.append("")
        lines.append(f"- **Python Version:** {sys.version.split()[0]}")
        lines.append(f"- **Platform:** {sys.platform}")
        lines.append("")
        
        # Add next steps if unhealthy
        if passed < total:
            lines.append("## Next Steps")
            lines.append("")
            lines.append("1. Review failed checks above")
            lines.append("2. Run `python -m pytest tests/unit/ -v` for detailed test output")
            lines.append("3. Check configuration files in `config/`")
            lines.append("")
        
        report_path.write_text("\n".join(lines))
        print(f"\nReport saved to: {report_path}")


def main():
    """Main entry point."""
    try:
        checker = HealthChecker()
        all_passed = checker.run_all_checks()
        sys.exit(0 if all_passed else 1)
    except Exception as e:
        print(f"\033[91mError: {e}\033[0m")
        sys.exit(1)


if __name__ == "__main__":
    main()