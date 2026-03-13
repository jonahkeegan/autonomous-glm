"""Unit tests for golden dataset validators."""

import sys
from pathlib import Path

import pytest

# Add golden-dataset to path (hyphen in name makes it non-importable as module)
golden_dataset_path = Path(__file__).parent.parent / "golden-dataset"
sys.path.insert(0, str(golden_dataset_path))

from validators.detection_validator import (
    DetectionValidator,
    validate_detection,
    BBox,
    DetectionMatch,
    DetectionValidationResult,
)
from validators.audit_validator import (
    AuditValidator,
    validate_findings,
    FindingMatch,
    AuditValidationResult,
)
from validators.accuracy_reporter import (
    AccuracyReporter,
    generate_accuracy_report,
    ScreenshotAccuracy,
    DimensionAccuracy,
    AccuracyReport,
)


class TestBBox:
    """Tests for BBox class."""
    
    def test_area(self):
        """Test bounding box area calculation."""
        bbox = BBox(x=0.1, y=0.2, w=0.3, h=0.4)
        assert bbox.area() == pytest.approx(0.12)
    
    def test_intersection_no_overlap(self):
        """Test intersection with no overlap."""
        bbox1 = BBox(x=0.0, y=0.0, w=0.2, h=0.2)
        bbox2 = BBox(x=0.5, y=0.5, w=0.2, h=0.2)
        assert bbox1.intersection(bbox2) == 0.0
    
    def test_intersection_full_overlap(self):
        """Test intersection with full overlap."""
        bbox = BBox(x=0.1, y=0.1, w=0.3, h=0.3)
        assert bbox.intersection(bbox) == pytest.approx(bbox.area())
    
    def test_intersection_partial_overlap(self):
        """Test intersection with partial overlap."""
        bbox1 = BBox(x=0.0, y=0.0, w=0.3, h=0.3)
        bbox2 = BBox(x=0.2, y=0.2, w=0.3, h=0.3)
        # Overlap is 0.1 x 0.1 = 0.01
        assert bbox1.intersection(bbox2) == pytest.approx(0.01)
    
    def test_iou_no_overlap(self):
        """Test IoU with no overlap."""
        bbox1 = BBox(x=0.0, y=0.0, w=0.2, h=0.2)
        bbox2 = BBox(x=0.5, y=0.5, w=0.2, h=0.2)
        assert bbox1.iou(bbox2) == 0.0
    
    def test_iu_full_overlap(self):
        """Test IoU with full overlap."""
        bbox = BBox(x=0.1, y=0.1, w=0.3, h=0.3)
        assert bbox.iou(bbox) == pytest.approx(1.0)
    
    def test_from_dict(self):
        """Test creating BBox from dict."""
        d = {"x": 0.1, "y": 0.2, "w": 0.3, "h": 0.4}
        bbox = BBox.from_dict(d)
        assert bbox.x == 0.1
        assert bbox.y == 0.2
        assert bbox.w == 0.3
        assert bbox.h == 0.4


class TestDetectionValidator:
    """Tests for DetectionValidator."""
    
    def test_validate_perfect_match(self):
        """Test validation with perfect detection match."""
        expected = {
            "name": "test_screenshot",
            "components": [
                {
                    "id": "comp_0",
                    "type": "button",
                    "bounding_box": {"x": 0.1, "y": 0.1, "w": 0.2, "h": 0.1},
                },
                {
                    "id": "comp_1",
                    "type": "text",
                    "bounding_box": {"x": 0.4, "y": 0.3, "w": 0.3, "h": 0.1},
                },
            ],
        }
        
        detected = {
            "components": [
                {
                    "id": "det_0",
                    "type": "button",
                    "bounding_box": {"x": 0.1, "y": 0.1, "w": 0.2, "h": 0.1},
                },
                {
                    "id": "det_1",
                    "type": "text",
                    "bounding_box": {"x": 0.4, "y": 0.3, "w": 0.3, "h": 0.1},
                },
            ],
        }
        
        result = validate_detection(expected, detected)
        
        assert result.passed is True
        assert result.matched_count == 2
        assert result.missed_count == 0
        assert result.extra_count == 0
        assert result.mean_iou == 1.0
    
    def test_validate_partial_match(self):
        """Test validation with partial detection match."""
        expected = {
            "name": "test_screenshot",
            "components": [
                {
                    "id": "comp_0",
                    "type": "button",
                    "bounding_box": {"x": 0.1, "y": 0.1, "w": 0.2, "h": 0.1},
                },
            ],
        }
        
        detected = {
            "components": [
                {
                    "id": "det_0",
                    "type": "button",
                    "bounding_box": {"x": 0.5, "y": 0.5, "w": 0.2, "h": 0.1},  # No overlap
                },
            ],
        }
        
        result = validate_detection(expected, detected, iou_threshold=0.7)
        
        assert result.passed is False
        assert result.matched_count == 0
        assert result.missed_count == 1
        assert result.extra_count == 1
    
    def test_validate_type_mismatch(self):
        """Test validation with type mismatch."""
        expected = {
            "name": "test_screenshot",
            "components": [
                {
                    "id": "comp_0",
                    "type": "button",
                    "bounding_box": {"x": 0.1, "y": 0.1, "w": 0.2, "h": 0.1},
                },
            ],
        }
        
        detected = {
            "components": [
                {
                    "id": "det_0",
                    "type": "text",  # Different type
                    "bounding_box": {"x": 0.1, "y": 0.1, "w": 0.2, "h": 0.1},
                },
            ],
        }
        
        result = validate_detection(expected, detected, iou_threshold=0.7)
        
        # Type strict by default
        assert result.passed is False
        assert len(result.details["type_mismatches"]) == 1


class TestAuditValidator:
    """Tests for AuditValidator."""
    
    def test_validate_perfect_match(self):
        """Test validation with perfect finding match."""
        expected = {
            "name": "test_screenshot",
            "expected_findings": [
                {
                    "dimension": "typography",
                    "issue": "font_size_too_small",
                    "severity": "high",
                    "location": {},
                    "rationale": "Text too small",
                },
            ],
            "tolerance": {"severity_flexibility": False, "max_extra_findings": 0},
        }
        
        detected = {
            "findings": [
                {
                    "dimension": "typography",
                    "issue": "font_size_too_small",
                    "severity": "high",
                },
            ],
        }
        
        result = validate_findings(expected, detected)
        
        assert result.passed is True
        assert result.matched_count == 1
        assert result.missed_count == 0
    
    def test_validate_missed_finding(self):
        """Test validation with missed finding."""
        expected = {
            "name": "test_screenshot",
            "expected_findings": [
                {
                    "dimension": "typography",
                    "issue": "font_size_too_small",
                    "severity": "high",
                    "location": {},
                    "rationale": "Text too small",
                },
            ],
            "tolerance": {"severity_flexibility": False, "max_extra_findings": 0},
        }
        
        detected = {"findings": []}
        
        result = validate_findings(expected, detected)
        
        assert result.passed is False
        assert result.missed_count == 1
    
    def test_validate_severity_flexibility(self):
        """Test validation with severity flexibility."""
        expected = {
            "name": "test_screenshot",
            "expected_findings": [
                {
                    "dimension": "typography",
                    "issue": "font_size_too_small",
                    "severity": "high",
                    "location": {},
                    "rationale": "Text too small",
                },
            ],
            "tolerance": {"severity_flexibility": True, "max_extra_findings": 0},
        }
        
        detected = {
            "findings": [
                {
                    "dimension": "typography",
                    "issue": "font_size_too_small",
                    "severity": "medium",  # Different severity
                },
            ],
        }
        
        result = validate_findings(expected, detected)
        
        assert result.passed is True  # Passes with flexibility
        assert result.severity_mismatches == 1
    
    def test_validate_clean_screenshot(self):
        """Test validation of clean screenshot with no findings."""
        expected = {
            "name": "clean_screenshot",
            "expected_findings": [],
            "tolerance": {},
        }
        
        detected = {"findings": []}
        
        result = validate_findings(expected, detected)
        
        assert result.passed is True


class TestAccuracyReporter:
    """Tests for AccuracyReporter."""
    
    def test_generate_report(self):
        """Test accuracy report generation."""
        detection_results = [
            DetectionValidationResult(
                screenshot_name="test_1",
                total_expected=5,
                total_detected=5,
                matched_count=5,
                missed_count=0,
                extra_count=0,
                mean_iou=0.95,
                iou_threshold=0.7,
                matches=[],
                passed=True,
                details={},
            ),
            DetectionValidationResult(
                screenshot_name="test_2",
                total_expected=3,
                total_detected=2,
                matched_count=2,
                missed_count=1,
                extra_count=0,
                mean_iou=0.8,
                iou_threshold=0.7,
                matches=[],
                passed=False,
                details={},
            ),
        ]
        
        audit_results = [
            AuditValidationResult(
                screenshot_name="test_1",
                total_expected=1,
                total_detected=1,
                matched_count=1,
                missed_count=0,
                extra_count=0,
                severity_mismatches=0,
                tolerance={},
                matches=[],
                passed=True,
                details={},
            ),
            AuditValidationResult(
                screenshot_name="test_2",
                total_expected=1,
                total_detected=0,
                matched_count=0,
                missed_count=1,
                extra_count=0,
                severity_mismatches=0,
                tolerance={},
                matches=[],
                passed=False,
                details={},
            ),
        ]
        
        reporter = AccuracyReporter()
        report = reporter.generate_report(detection_results, audit_results)
        
        assert report.total_screenshots == 2
        assert report.detection_passes == 1
        assert report.detection_accuracy == 0.5
        assert report.audit_passes == 1
        assert report.audit_accuracy == 0.5
        assert len(report.screenshots) == 2
    
    def test_report_passed_threshold(self):
        """Test that report passes when accuracy >= 95%."""
        detection_results = [
            DetectionValidationResult(
                screenshot_name=f"test_{i}",
                total_expected=5,
                total_detected=5,
                matched_count=5,
                missed_count=0,
                extra_count=0,
                mean_iou=0.95,
                iou_threshold=0.7,
                matches=[],
                passed=True,
                details={},
            )
            for i in range(20)  # 20 screenshots all passing
        ]
        
        audit_results = [
            AuditValidationResult(
                screenshot_name=f"test_{i}",
                total_expected=1,
                total_detected=1,
                matched_count=1,
                missed_count=0,
                extra_count=0,
                severity_mismatches=0,
                tolerance={},
                matches=[],
                passed=True,
                details={},
            )
            for i in range(20)
        ]
        
        reporter = AccuracyReporter()
        report = reporter.generate_report(detection_results, audit_results)
        
        assert report.passed is True
        assert report.detection_accuracy == 1.0
        assert report.audit_accuracy == 1.0


class TestScreenshotAccuracy:
    """Tests for ScreenshotAccuracy dataclass."""
    
    def test_overall_passed(self):
        """Test overall_passed calculation."""
        sa = ScreenshotAccuracy(
            name="test",
            detection_passed=True,
            audit_passed=True,
            detection_iou=0.9,
            detection_matched=5,
            detection_total=5,
            audit_matched=2,
            audit_total=2,
            overall_passed=True,
        )
        
        assert sa.overall_passed is True
        assert sa.detection_passed is True
        assert sa.audit_passed is True


class TestGoldenDatasetIntegration:
    """Integration tests using generated golden dataset files."""
    
    @pytest.fixture
    def manifest(self):
        """Load the generated manifest."""
        import json
        from pathlib import Path
        
        manifest_path = Path("tests/golden-dataset/manifest.json")
        if not manifest_path.exists():
            pytest.skip("Golden dataset not generated yet")
        
        with open(manifest_path) as f:
            return json.load(f)
    
    def test_manifest_exists(self, manifest):
        """Test that manifest was created."""
        assert manifest is not None
        assert "total_screenshots" in manifest
        assert manifest["total_screenshots"] >= 20
    
    def test_screenshots_have_detection_json(self, manifest):
        """Test that all screenshots have detection JSON files."""
        from pathlib import Path
        
        for screenshot in manifest["screenshots"]:
            detection_path = Path("tests/golden-dataset/detection") / screenshot["detection"]
            assert detection_path.exists(), f"Missing detection: {detection_path}"
    
    def test_screenshots_have_findings_json(self, manifest):
        """Test that all screenshots have findings JSON files."""
        from pathlib import Path
        
        for screenshot in manifest["screenshots"]:
            findings_path = Path("tests/golden-dataset/findings") / screenshot["findings"]
            assert findings_path.exists(), f"Missing findings: {findings_path}"
    
    def test_detection_schema_valid(self, manifest):
        """Test that detection JSON files match schema."""
        import json
        from pathlib import Path
        
        required_fields = ["screenshot_id", "name", "dimensions", "components", "component_count"]
        
        for screenshot in manifest["screenshots"][:3]:  # Check first 3
            detection_path = Path("tests/golden-dataset/detection") / screenshot["detection"]
            with open(detection_path) as f:
                detection = json.load(f)
            
            for field in required_fields:
                assert field in detection, f"Missing field {field} in {screenshot['name']}"
    
    def test_findings_schema_valid(self, manifest):
        """Test that findings JSON files match schema."""
        import json
        from pathlib import Path
        
        required_fields = ["screenshot_id", "name", "expected_findings", "tolerance"]
        
        for screenshot in manifest["screenshots"][:3]:  # Check first 3
            findings_path = Path("tests/golden-dataset/findings") / screenshot["findings"]
            with open(findings_path) as f:
                findings = json.load(f)
            
            for field in required_fields:
                assert field in findings, f"Missing field {field} in {screenshot['name']}"
    
    def test_dimension_coverage(self, manifest):
        """Test that all expected dimensions are covered."""
        expected_dimensions = {
            "visual_hierarchy",
            "spacing_rhythm",
            "typography",
            "color",
            "alignment_grid",
            "components",
            "empty_states",
            "error_states",
            "density",
            "accessibility",
        }
        
        covered_dimensions = set(manifest["dimensions_covered"])
        
        assert expected_dimensions.issubset(covered_dimensions), \
            f"Missing dimensions: {expected_dimensions - covered_dimensions}"