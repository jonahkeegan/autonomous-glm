"""Detection validator for comparing CV results against expected ground truth."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class BBox:
    """Bounding box representation."""
    x: float
    y: float
    w: float
    h: float
    
    @classmethod
    def from_dict(cls, d: dict) -> "BBox":
        return cls(x=d["x"], y=d["y"], w=d["w"], h=d["h"])
    
    def area(self) -> float:
        return self.w * self.h
    
    def intersection(self, other: "BBox") -> float:
        """Calculate intersection area."""
        x1 = max(self.x, other.x)
        y1 = max(self.y, other.y)
        x2 = min(self.x + self.w, other.x + other.w)
        y2 = min(self.y + self.h, other.y + other.h)
        
        if x2 <= x1 or y2 <= y1:
            return 0.0
        
        return (x2 - x1) * (y2 - y1)
    
    def union(self, other: "BBox") -> float:
        """Calculate union area."""
        return self.area() + other.area() - self.intersection(other)
    
    def iou(self, other: "BBox") -> float:
        """Calculate Intersection over Union."""
        union = self.union(other)
        if union == 0:
            return 0.0
        return self.intersection(other) / union


@dataclass
class DetectionMatch:
    """Result of matching a detected component to expected."""
    detected_id: str
    expected_id: str
    iou: float
    type_match: bool
    passed: bool


@dataclass
class DetectionValidationResult:
    """Result of detection validation."""
    screenshot_name: str
    total_expected: int
    total_detected: int
    matched_count: int
    missed_count: int
    extra_count: int
    mean_iou: float
    iou_threshold: float
    matches: list[DetectionMatch]
    passed: bool
    details: dict


class DetectionValidator:
    """Validates CV detection results against expected ground truth."""
    
    def __init__(self, iou_threshold: float = 0.7, type_strict: bool = True):
        """
        Args:
            iou_threshold: Minimum IoU for a match (default 0.7)
            type_strict: Whether component types must match
        """
        self.iou_threshold = iou_threshold
        self.type_strict = type_strict
    
    def validate(
        self,
        expected: dict,
        detected: dict,
    ) -> DetectionValidationResult:
        """Validate detected components against expected.
        
        Args:
            expected: Expected detection result from golden dataset
            detected: Actual detection result from CV pipeline
            
        Returns:
            DetectionValidationResult with match details
        """
        expected_components = expected.get("components", [])
        detected_components = detected.get("components", [])
        
        # Build expected bboxes
        expected_bboxes = []
        for comp in expected_components:
            bbox = BBox.from_dict(comp["bounding_box"])
            expected_bboxes.append({
                "id": comp["id"],
                "type": comp["type"],
                "bbox": bbox,
                "matched": False,
            })
        
        # Build detected bboxes
        detected_bboxes = []
        for comp in detected_components:
            bbox = BBox.from_dict(comp.get("bounding_box", {}))
            detected_bboxes.append({
                "id": comp.get("id", "unknown"),
                "type": comp.get("type", "unknown"),
                "bbox": bbox,
                "matched": False,
            })
        
        # Find matches using greedy matching (highest IoU first)
        matches = []
        for detected in detected_bboxes:
            best_match = None
            best_iou = 0.0
            
            for exp in expected_bboxes:
                if exp["matched"]:
                    continue
                
                iou = detected["bbox"].iou(exp["bbox"])
                if iou >= self.iou_threshold and iou > best_iou:
                    best_match = exp
                    best_iou = iou
            
            if best_match:
                type_match = detected["type"] == best_match["type"]
                passed = type_match if self.type_strict else True
                
                matches.append(DetectionMatch(
                    detected_id=detected["id"],
                    expected_id=best_match["id"],
                    iou=best_iou,
                    type_match=type_match,
                    passed=passed,
                ))
                
                detected["matched"] = True
                best_match["matched"] = True
        
        # Calculate metrics
        matched_count = len(matches)
        missed_count = sum(1 for e in expected_bboxes if not e["matched"])
        extra_count = sum(1 for d in detected_bboxes if not d["matched"])
        
        mean_iou = (
            sum(m.iou for m in matches) / len(matches)
            if matches else 0.0
        )
        
        # Determine pass/fail
        # Pass if: All expected matched, mean IoU >= threshold, no more than tolerance extras
        passed = (
            missed_count == 0 and
            mean_iou >= self.iou_threshold and
            all(m.passed for m in matches)
        )
        
        return DetectionValidationResult(
            screenshot_name=expected.get("name", "unknown"),
            total_expected=len(expected_components),
            total_detected=len(detected_components),
            matched_count=matched_count,
            missed_count=missed_count,
            extra_count=extra_count,
            mean_iou=mean_iou,
            iou_threshold=self.iou_threshold,
            matches=matches,
            passed=passed,
            details={
                "type_strict": self.type_strict,
                "type_mismatches": [m for m in matches if not m.type_match],
            },
        )


def validate_detection(
    expected: dict,
    detected: dict,
    iou_threshold: float = 0.7,
) -> DetectionValidationResult:
    """Convenience function for detection validation."""
    validator = DetectionValidator(iou_threshold=iou_threshold)
    return validator.validate(expected, detected)