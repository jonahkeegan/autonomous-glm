"""Accuracy reporter for golden dataset validation results."""

import json
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from .detection_validator import DetectionValidationResult
from .audit_validator import AuditValidationResult


@dataclass
class ScreenshotAccuracy:
    """Accuracy metrics for a single screenshot."""
    name: str
    detection_passed: bool
    audit_passed: bool
    detection_iou: float
    detection_matched: int
    detection_total: int
    audit_matched: int
    audit_total: int
    overall_passed: bool


@dataclass
class DimensionAccuracy:
    """Accuracy metrics for an audit dimension."""
    dimension: str
    screenshots_tested: int
    passed: int
    failed: int
    accuracy_rate: float


@dataclass
class AccuracyReport:
    """Complete accuracy report for golden dataset validation."""
    timestamp: str
    total_screenshots: int
    detection_passes: int
    detection_failures: int
    detection_accuracy: float
    mean_iou: float
    audit_passes: int
    audit_failures: int
    audit_accuracy: float
    overall_accuracy: float
    screenshots: list[ScreenshotAccuracy]
    dimensions: list[DimensionAccuracy]
    passed: bool
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "timestamp": self.timestamp,
            "total_screenshots": self.total_screenshots,
            "detection_passes": self.detection_passes,
            "detection_failures": self.detection_failures,
            "detection_accuracy": self.detection_accuracy,
            "mean_iou": self.mean_iou,
            "audit_passes": self.audit_passes,
            "audit_failures": self.audit_failures,
            "audit_accuracy": self.audit_accuracy,
            "overall_accuracy": self.overall_accuracy,
            "screenshots": [asdict(s) for s in self.screenshots],
            "dimensions": [asdict(d) for d in self.dimensions],
            "passed": self.passed,
        }


class AccuracyReporter:
    """Generates accuracy reports from validation results."""
    
    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or Path("tests/golden-dataset")
    
    def generate_report(
        self,
        detection_results: list[DetectionValidationResult],
        audit_results: list[AuditValidationResult],
        dimension_mapping: Optional[dict[str, str]] = None,
    ) -> AccuracyReport:
        """Generate accuracy report from validation results.
        
        Args:
            detection_results: List of detection validation results
            audit_results: List of audit validation results
            dimension_mapping: Optional mapping of screenshot names to dimensions
            
        Returns:
            AccuracyReport with comprehensive metrics
        """
        timestamp = datetime.now().isoformat()
        
        # Build screenshot accuracy metrics
        screenshot_accuracy = []
        detection_iou_sum = 0.0
        detection_passes = 0
        audit_passes = 0
        
        # Create lookup for audit results
        audit_lookup = {r.screenshot_name: r for r in audit_results}
        
        for det_result in detection_results:
            name = det_result.screenshot_name
            audit_result = audit_lookup.get(name)
            
            det_passed = det_result.passed
            audit_passed = audit_result.passed if audit_result else False
            overall_passed = det_passed and audit_passed
            
            screenshot_accuracy.append(ScreenshotAccuracy(
                name=name,
                detection_passed=det_passed,
                audit_passed=audit_passed,
                detection_iou=det_result.mean_iou,
                detection_matched=det_result.matched_count,
                detection_total=det_result.total_expected,
                audit_matched=audit_result.matched_count if audit_result else 0,
                audit_total=audit_result.total_expected if audit_result else 0,
                overall_passed=overall_passed,
            ))
            
            detection_iou_sum += det_result.mean_iou
            if det_passed:
                detection_passes += 1
            if audit_passed:
                audit_passes += 1
        
        total_screenshots = len(detection_results)
        
        # Calculate overall metrics
        detection_accuracy = detection_passes / total_screenshots if total_screenshots > 0 else 0.0
        audit_accuracy = audit_passes / total_screenshots if total_screenshots > 0 else 0.0
        mean_iou = detection_iou_sum / total_screenshots if total_screenshots > 0 else 0.0
        
        # Calculate per-dimension accuracy
        dimension_accuracy = []
        if dimension_mapping:
            dimension_stats: dict[str, dict] = {}
            
            for sa in screenshot_accuracy:
                dim = dimension_mapping.get(sa.name, "unknown")
                if dim not in dimension_stats:
                    dimension_stats[dim] = {"tested": 0, "passed": 0}
                dimension_stats[dim]["tested"] += 1
                if sa.overall_passed:
                    dimension_stats[dim]["passed"] += 1
            
            for dim, stats in dimension_stats.items():
                accuracy_rate = stats["passed"] / stats["tested"] if stats["tested"] > 0 else 0.0
                dimension_accuracy.append(DimensionAccuracy(
                    dimension=dim,
                    screenshots_tested=stats["tested"],
                    passed=stats["passed"],
                    failed=stats["tested"] - stats["passed"],
                    accuracy_rate=accuracy_rate,
                ))
        
        # Overall pass requires >95% accuracy on both detection and audit
        overall_accuracy = (detection_accuracy + audit_accuracy) / 2
        passed = detection_accuracy >= 0.95 and audit_accuracy >= 0.95
        
        return AccuracyReport(
            timestamp=timestamp,
            total_screenshots=total_screenshots,
            detection_passes=detection_passes,
            detection_failures=total_screenshots - detection_passes,
            detection_accuracy=detection_accuracy,
            mean_iou=mean_iou,
            audit_passes=audit_passes,
            audit_failures=total_screenshots - audit_passes,
            audit_accuracy=audit_accuracy,
            overall_accuracy=overall_accuracy,
            screenshots=screenshot_accuracy,
            dimensions=dimension_accuracy,
            passed=passed,
        )
    
    def save_report(
        self,
        report: AccuracyReport,
        filename: str = "accuracy_report.json",
    ) -> Path:
        """Save accuracy report to JSON file.
        
        Args:
            report: AccuracyReport to save
            filename: Output filename
            
        Returns:
            Path to saved report
        """
        output_path = self.output_dir / filename
        with open(output_path, "w") as f:
            json.dump(report.to_dict(), f, indent=2)
        return output_path


def generate_accuracy_report(
    detection_results: list[DetectionValidationResult],
    audit_results: list[AuditValidationResult],
    dimension_mapping: Optional[dict[str, str]] = None,
    output_dir: Optional[Path] = None,
) -> AccuracyReport:
    """Convenience function to generate and save accuracy report."""
    reporter = AccuracyReporter(output_dir)
    report = reporter.generate_report(detection_results, audit_results, dimension_mapping)
    reporter.save_report(report)
    return report