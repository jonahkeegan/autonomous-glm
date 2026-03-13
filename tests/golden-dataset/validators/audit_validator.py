"""Audit validator for comparing audit findings against expected results."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class FindingMatch:
    """Result of matching a finding to expected."""
    dimension: str
    issue: str
    severity_match: bool
    matched: bool


@dataclass
class AuditValidationResult:
    """Result of audit findings validation."""
    screenshot_name: str
    total_expected: int
    total_detected: int
    matched_count: int
    missed_count: int
    extra_count: int
    severity_mismatches: int
    tolerance: dict
    matches: list[FindingMatch]
    passed: bool
    details: dict


class AuditValidator:
    """Validates audit findings against expected results."""
    
    def __init__(
        self,
        severity_strict: bool = False,
        max_extra_findings: int = 2,
    ):
        """
        Args:
            severity_strict: Whether severity must match exactly
            max_extra_findings: Maximum extra findings allowed
        """
        self.severity_strict = severity_strict
        self.max_extra_findings = max_extra_findings
    
    def validate(
        self,
        expected: dict,
        detected: dict,
    ) -> AuditValidationResult:
        """Validate detected findings against expected.
        
        Args:
            expected: Expected findings result from golden dataset
            detected: Actual audit findings from audit pipeline
            
        Returns:
            AuditValidationResult with match details
        """
        expected_findings = expected.get("expected_findings", [])
        detected_findings = detected.get("findings", [])
        tolerance = expected.get("tolerance", {})
        
        # Apply tolerance settings
        severity_flexibility = tolerance.get("severity_flexibility", not self.severity_strict)
        max_extra = tolerance.get("max_extra_findings", self.max_extra_findings)
        
        # Build expected findings index by (dimension, issue)
        expected_index = {}
        for finding in expected_findings:
            key = (finding["dimension"], finding["issue"])
            expected_index[key] = {
                "severity": finding["severity"],
                "matched": False,
            }
        
        # Match detected findings
        matches = []
        severity_mismatches = 0
        
        for detected in detected_findings:
            key = (detected.get("dimension", ""), detected.get("issue", ""))
            
            if key in expected_index:
                exp = expected_index[key]
                severity_match = detected.get("severity") == exp["severity"]
                
                if not severity_match and severity_flexibility:
                    # Allow severity flexibility - still counts as match
                    matched = True
                    severity_mismatches += 1
                elif not severity_match:
                    matched = False
                    severity_mismatches += 1
                else:
                    matched = True
                
                matches.append(FindingMatch(
                    dimension=key[0],
                    issue=key[1],
                    severity_match=severity_match,
                    matched=matched,
                ))
                
                if matched:
                    expected_index[key]["matched"] = True
            # else: extra finding - counted separately
        
        # Calculate metrics
        matched_count = sum(1 for m in matches if m.matched)
        missed_count = sum(1 for exp in expected_index.values() if not exp["matched"])
        extra_count = len(detected_findings) - len(matches)
        
        # Determine pass/fail
        passed = (
            matched_count == len(expected_findings) and  # All expected found
            missed_count == 0 and  # No missed findings
            extra_count <= max_extra and  # Within extra tolerance
            (severity_flexibility or severity_mismatches == 0)  # Severity match
        )
        
        return AuditValidationResult(
            screenshot_name=expected.get("name", "unknown"),
            total_expected=len(expected_findings),
            total_detected=len(detected_findings),
            matched_count=matched_count,
            missed_count=missed_count,
            extra_count=extra_count,
            severity_mismatches=severity_mismatches,
            tolerance=tolerance,
            matches=matches,
            passed=passed,
            details={
                "severity_flexibility": severity_flexibility,
                "max_extra_allowed": max_extra,
                "missed_issues": [
                    {"dimension": k[0], "issue": k[1]}
                    for k, v in expected_index.items()
                    if not v["matched"]
                ],
            },
        )
    
    def validate_empty_findings(
        self,
        expected: dict,
    ) -> AuditValidationResult:
        """Validate that a screenshot with no expected issues has no findings.
        
        Args:
            expected: Expected findings result (should have empty expected_findings)
            
        Returns:
            AuditValidationResult
        """
        return AuditValidationResult(
            screenshot_name=expected.get("name", "unknown"),
            total_expected=0,
            total_detected=0,
            matched_count=0,
            missed_count=0,
            extra_count=0,
            severity_mismatches=0,
            tolerance=expected.get("tolerance", {}),
            matches=[],
            passed=True,
            details={"note": "Clean screenshot - no issues expected"},
        )


def validate_findings(
    expected: dict,
    detected: dict,
    severity_strict: bool = False,
) -> AuditValidationResult:
    """Convenience function for audit validation."""
    validator = AuditValidator(severity_strict=severity_strict)
    
    # Handle clean screenshots with no expected findings
    if not expected.get("expected_findings"):
        if not detected.get("findings"):
            return validator.validate_empty_findings(expected)
    
    return validator.validate(expected, detected)