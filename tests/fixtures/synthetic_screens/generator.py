"""Screenshot generator for golden dataset creation.

Generates synthetic UI screenshots with controlled issues for testing CV detection
and audit accuracy validation.
"""

import json
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional

from PIL import Image, ImageDraw

from .templates import (
    UITemplate,
    LoginTemplate,
    DashboardTemplate,
    FormTemplate,
    ListTemplate,
    TemplateResult,
    Component,
    ComponentType,
)
from .issue_injectors import (
    IssueType,
    IssueInjector,
    INJECTOR_MAP,
    get_issue_dimension,
    get_issue_severity,
)


@dataclass
class ExpectedDetection:
    """Expected detection result for a screenshot."""
    screenshot_id: str
    name: str
    dimensions: dict[str, int]
    components: list[dict]
    component_count: int
    component_types: list[str]
    created: str


@dataclass
class ExpectedFinding:
    """Expected audit finding for a screenshot."""
    dimension: str
    issue: str
    severity: str
    location: dict
    rationale: str


@dataclass
class ExpectedFindingsResult:
    """Expected findings result for a screenshot."""
    screenshot_id: str
    name: str
    expected_findings: list[dict]
    tolerance: dict
    created: str


class ScreenshotGenerator:
    """Generates synthetic UI screenshots with controlled issues."""
    
    # Output directories
    SCREENSHOTS_DIR = Path("tests/golden-dataset/screenshots")
    DETECTION_DIR = Path("tests/golden-dataset/detection")
    FINDINGS_DIR = Path("tests/golden-dataset/findings")
    
    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or Path("tests/golden-dataset")
        self.screenshots_dir = self.output_dir / "screenshots"
        self.detection_dir = self.output_dir / "detection"
        self.findings_dir = self.output_dir / "findings"
        
        # Ensure directories exist
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)
        self.detection_dir.mkdir(parents=True, exist_ok=True)
        self.findings_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_screenshot(
        self,
        name: str,
        template: UITemplate,
        issues: Optional[list[IssueType]] = None,
        description: str = "",
    ) -> tuple[Path, ExpectedDetection, ExpectedFindingsResult]:
        """Generate a screenshot with optional issues injected.
        
        Args:
            name: Screenshot name (without extension)
            template: UI template to use
            issues: List of issues to inject
            description: Human-readable description
            
        Returns:
            Tuple of (screenshot_path, expected_detection, expected_findings)
        """
        # Render base template
        result = template.render()
        image = result.image
        draw = ImageDraw.Draw(image)
        components = list(result.components)
        
        # Track expected findings
        expected_findings = []
        
        # Inject issues if specified
        if issues:
            injector = IssueInjector(template)
            for issue_type in issues:
                if issue_type in INJECTOR_MAP:
                    inject_method = INJECTOR_MAP[issue_type]
                    issue_components = inject_method(injector, draw, template.width, template.height)
                    components.extend(issue_components)
                    
                    # Add expected finding
                    finding = ExpectedFinding(
                        dimension=get_issue_dimension(issue_type),
                        issue=issue_type.value,
                        severity=get_issue_severity(issue_type),
                        location={"component_ids": [f"comp_{i}" for i in range(len(issue_components))]},
                        rationale=f"Injected issue: {issue_type.value}",
                    )
                    expected_findings.append(asdict(finding))
        
        # Generate screenshot ID
        screenshot_id = str(uuid.uuid4())
        created = datetime.now().isoformat()
        
        # Save screenshot
        screenshot_path = self.screenshots_dir / f"{name}.png"
        image.save(screenshot_path, "PNG")
        
        # Build expected detection result
        component_dicts = []
        component_types = set()
        
        for i, comp in enumerate(components):
            x, y, w, h = comp.bbox
            comp_dict = {
                "id": f"comp_{i}",
                "type": comp.type.value,
                "label": comp.label,
                "bounding_box": {
                    "x": x / template.width,
                    "y": y / template.height,
                    "w": w / template.width,
                    "h": h / template.height,
                },
                "bounding_box_px": {
                    "x": x,
                    "y": y,
                    "width": w,
                    "height": h,
                },
                "confidence": 1.0,  # Known ground truth
                "attributes": {
                    "text": comp.label,
                    "visible": True,
                    "is_issue": comp.is_issue,
                    "issue_type": comp.issue_type,
                },
            }
            component_dicts.append(comp_dict)
            component_types.add(comp.type.value)
        
        expected_detection = ExpectedDetection(
            screenshot_id=screenshot_id,
            name=name,
            dimensions={"width": template.width, "height": template.height},
            components=component_dicts,
            component_count=len(components),
            component_types=sorted(component_types),
            created=created,
        )
        
        # Save expected detection
        detection_path = self.detection_dir / f"{name}.json"
        with open(detection_path, "w") as f:
            json.dump(asdict(expected_detection), f, indent=2)
        
        # Build expected findings result
        expected_findings_result = ExpectedFindingsResult(
            screenshot_id=screenshot_id,
            name=name,
            expected_findings=expected_findings,
            tolerance={
                "severity_flexibility": False,
                "max_extra_findings": 2,
            },
            created=created,
        )
        
        # Save expected findings
        findings_path = self.findings_dir / f"{name}.json"
        with open(findings_path, "w") as f:
            json.dump(asdict(expected_findings_result), f, indent=2)
        
        return screenshot_path, expected_detection, expected_findings_result
    
    def generate_clean_screenshot(
        self,
        name: str,
        template: UITemplate,
        description: str = "",
    ) -> tuple[Path, ExpectedDetection, ExpectedFindingsResult]:
        """Generate a clean screenshot with no issues.
        
        Args:
            name: Screenshot name
            template: UI template to use
            description: Human-readable description
            
        Returns:
            Tuple of (screenshot_path, expected_detection, expected_findings)
        """
        return self.generate_screenshot(name, template, issues=None, description=description)


# Screenshot specifications for golden dataset
SCREENSHOT_SPECS = [
    # Hierarchy dimension (3 screenshots)
    {
        "name": "hierarchy_001_no_focal_point",
        "description": "Dashboard with no clear focal point - all cards same size",
        "template": DashboardTemplate(),
        "issues": [IssueType.NO_FOCAL_POINT],
        "dimension": "visual_hierarchy",
    },
    {
        "name": "hierarchy_002_competing_elements",
        "description": "Multiple competing CTA buttons with same prominence",
        "template": LoginTemplate(),
        "issues": [IssueType.COMPETING_ELEMENTS],
        "dimension": "visual_hierarchy",
    },
    {
        "name": "hierarchy_003_clean",
        "description": "Clean login form with proper visual hierarchy",
        "template": LoginTemplate(),
        "issues": None,
        "dimension": "visual_hierarchy",
    },
    
    # Spacing dimension (3 screenshots)
    {
        "name": "spacing_001_cramped_margins",
        "description": "Content with cramped margins - too close to edges",
        "template": FormTemplate(),
        "issues": [IssueType.CRAMPED_MARGINS],
        "dimension": "spacing_rhythm",
    },
    {
        "name": "spacing_002_inconsistent_rhythm",
        "description": "Cards with inconsistent vertical spacing",
        "template": DashboardTemplate(),
        "issues": [IssueType.INCONSISTENT_RHYTHM],
        "dimension": "spacing_rhythm",
    },
    {
        "name": "spacing_003_clean",
        "description": "Clean dashboard with consistent spacing",
        "template": DashboardTemplate(),
        "issues": None,
        "dimension": "spacing_rhythm",
    },
    
    # Typography dimension (3 screenshots)
    {
        "name": "typography_001_small_font",
        "description": "Text with font size too small to read",
        "template": FormTemplate(),
        "issues": [IssueType.FONT_SIZE_TOO_SMALL],
        "dimension": "typography",
    },
    {
        "name": "typography_002_hierarchy_break",
        "description": "Heading smaller than body text",
        "template": DashboardTemplate(),
        "issues": [IssueType.TYPOGRAPHY_HIERARCHY_BREAK],
        "dimension": "typography",
    },
    {
        "name": "typography_003_clean",
        "description": "Clean typography with proper hierarchy",
        "template": FormTemplate(),
        "issues": None,
        "dimension": "typography",
    },
    
    # Color dimension (3 screenshots)
    {
        "name": "color_001_low_contrast",
        "description": "Low contrast text on light background",
        "template": LoginTemplate(),
        "issues": [IssueType.LOW_CONTRAST],
        "dimension": "color",
    },
    {
        "name": "color_002_accessibility",
        "description": "Color-only status indicators without labels",
        "template": DashboardTemplate(),
        "issues": [IssueType.COLOR_ACCESSIBILITY],
        "dimension": "accessibility",
    },
    {
        "name": "color_003_clean",
        "description": "Clean color scheme with proper contrast",
        "template": DashboardTemplate(),
        "issues": None,
        "dimension": "color",
    },
    
    # Alignment dimension (3 screenshots)
    {
        "name": "alignment_001_off_grid",
        "description": "Elements not aligned to 8px grid",
        "template": FormTemplate(),
        "issues": [IssueType.OFF_GRID_ELEMENTS],
        "dimension": "alignment_grid",
    },
    {
        "name": "alignment_002_misalignment",
        "description": "Labels and inputs visually misaligned",
        "template": FormTemplate(),
        "issues": [IssueType.MISALIGNMENT],
        "dimension": "alignment_grid",
    },
    {
        "name": "alignment_003_clean",
        "description": "Clean alignment with proper grid",
        "template": FormTemplate(),
        "issues": None,
        "dimension": "alignment_grid",
    },
    
    # Components dimension (3 screenshots)
    {
        "name": "components_001_size_inconsistency",
        "description": "Buttons with inconsistent sizes",
        "template": LoginTemplate(),
        "issues": [IssueType.SIZE_INCONSISTENCY],
        "dimension": "components",
    },
    {
        "name": "components_002_style_proliferation",
        "description": "Too many button color variants",
        "template": DashboardTemplate(),
        "issues": [IssueType.STYLE_PROLIFERATION],
        "dimension": "components",
    },
    {
        "name": "components_003_clean",
        "description": "Clean components with consistent styling",
        "template": LoginTemplate(),
        "issues": None,
        "dimension": "components",
    },
    
    # States dimension (2 screenshots)
    {
        "name": "states_001_missing_empty",
        "description": "List without empty state design",
        "template": ListTemplate(),
        "issues": [IssueType.MISSING_EMPTY_STATE],
        "dimension": "empty_states",
    },
    {
        "name": "states_002_missing_error",
        "description": "Form input with error but no error message",
        "template": FormTemplate(),
        "issues": [IssueType.MISSING_ERROR_STATE],
        "dimension": "error_states",
    },
    
    # Density dimension (2 screenshots)
    {
        "name": "density_001_too_dense",
        "description": "Layout with too many elements packed tightly",
        "template": DashboardTemplate(),
        "issues": [IssueType.TOO_DENSE],
        "dimension": "density",
    },
    {
        "name": "density_002_too_sparse",
        "description": "Layout with too much empty space",
        "template": LoginTemplate(),
        "issues": [IssueType.TOO_SPARSE],
        "dimension": "density",
    },
]


def generate_all_screenshots(
    output_dir: Optional[Path] = None,
) -> tuple[list[Path], list[ExpectedDetection], list[ExpectedFindingsResult]]:
    """Generate all screenshots in the golden dataset.
    
    Args:
        output_dir: Base output directory
        
    Returns:
        Tuple of (paths, detections, findings) for all generated screenshots
    """
    generator = ScreenshotGenerator(output_dir)
    
    paths = []
    detections = []
    findings = []
    
    for spec in SCREENSHOT_SPECS:
        # Create fresh template instance for each screenshot
        template_class = spec["template"].__class__
        template = template_class()
        
        path, detection, finding = generator.generate_screenshot(
            name=spec["name"],
            template=template,
            issues=spec["issues"],
            description=spec["description"],
        )
        
        paths.append(path)
        detections.append(detection)
        findings.append(finding)
        
        print(f"Generated: {spec['name']} ({len(detection.components)} components)")
    
    # Generate manifest
    manifest = {
        "description": "Golden dataset for Autonomous-GLM CV/Audit validation",
        "created": datetime.now().isoformat(),
        "total_screenshots": len(paths),
        "dimensions_covered": sorted(set(s["dimension"] for s in SCREENSHOT_SPECS)),
        "screenshots": [
            {
                "name": spec["name"],
                "description": spec["description"],
                "image": f"{spec['name']}.png",
                "detection": f"{spec['name']}.json",
                "findings": f"{spec['name']}.json",
                "dimension": spec["dimension"],
                "has_issues": spec["issues"] is not None,
            }
            for spec in SCREENSHOT_SPECS
        ],
    }
    
    manifest_path = generator.output_dir / "manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    
    print(f"\nGenerated {len(paths)} screenshots")
    print(f"Manifest saved to: {manifest_path}")
    
    return paths, detections, findings


if __name__ == "__main__":
    generate_all_screenshots()