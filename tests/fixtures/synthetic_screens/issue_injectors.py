"""Issue injectors for synthetic screenshot generation.

Provides functions to inject specific UI issues into templates for testing audit dimensions.
"""

from enum import Enum
from typing import Optional, Callable, Any

from PIL import Image, ImageDraw

from .templates import (
    UITemplate,
    Component,
    ComponentType,
    TemplateResult,
)


class IssueType(Enum):
    """Types of UI issues that can be injected."""
    # Hierarchy issues
    NO_FOCAL_POINT = "no_focal_point"
    COMPETING_ELEMENTS = "competing_elements"
    POOR_VISUAL_WEIGHT = "poor_visual_weight"
    
    # Spacing issues
    CRAMPED_MARGINS = "cramped_margins"
    INCONSISTENT_RHYTHM = "inconsistent_rhythm"
    GRID_VIOLATIONS = "grid_violations"
    
    # Typography issues
    FONT_SIZE_TOO_SMALL = "font_size_too_small"
    TYPOGRAPHY_HIERARCHY_BREAK = "typography_hierarchy_break"
    FONT_WEIGHT_INCONSISTENCY = "font_weight_inconsistency"
    
    # Color issues
    LOW_CONTRAST = "low_contrast"
    INSUFFICIENT_DISTINCT_COLORS = "insufficient_distinct_colors"
    COLOR_ACCESSIBILITY = "color_accessibility"
    
    # Alignment issues
    OFF_GRID_ELEMENTS = "off_grid_elements"
    MISALIGNMENT = "misalignment"
    CENTERING_ISSUES = "centering_issues"
    
    # Component issues
    SIZE_INCONSISTENCY = "size_inconsistency"
    STYLE_PROLIFERATION = "style_proliferation"
    VARIANT_CHAOS = "variant_chaos"
    
    # State issues
    MISSING_EMPTY_STATE = "missing_empty_state"
    MISSING_ERROR_STATE = "missing_error_state"
    MISSING_LOADING_STATE = "missing_loading_state"
    
    # Density issues
    TOO_DENSE = "too_dense"
    TOO_SPARSE = "too_sparse"


class IssueInjector:
    """Injects specific UI issues into templates."""
    
    # Issue colors for testing
    LOW_CONTRAST_TEXT = "#9CA3AF"  # Gray on white (fails WCAG)
    LOW_CONTRAST_BG = "#F3F4F6"  # Light gray
    VERY_SMALL_FONT = 8
    SMALL_FONT = 10
    
    def __init__(self, template: UITemplate):
        self.template = template
        self.injected_issues: list[IssueType] = []
    
    def inject_hierarchy_no_focal_point(
        self, draw: ImageDraw.ImageDraw, width: int, height: int
    ) -> list[Component]:
        """Inject a layout with no clear focal point - all elements same size/weight."""
        components = []
        
        # Create multiple equally-sized cards that compete for attention
        card_width = (width - 64) // 3
        card_height = 100
        
        for i in range(3):
            x = 16 + i * (card_width + 16)
            card = Component(
                type=ComponentType.CARD,
                bbox=(x, 80, card_width, card_height),
                is_issue=True,
                issue_type=IssueType.NO_FOCAL_POINT.value,
            )
            components.append(card)
            
            # All titles same size - no hierarchy
            title = Component(
                type=ComponentType.TEXT,
                bbox=(x + 8, 90, card_width - 16, 20),
                label=f"Section {i+1}",
                font_size=14,  # All same size - issue
                is_issue=True,
                issue_type=IssueType.NO_FOCAL_POINT.value,
            )
            components.append(title)
        
        self.injected_issues.append(IssueType.NO_FOCAL_POINT)
        return components
    
    def inject_hierarchy_competing_elements(
        self, draw: ImageDraw.ImageDraw, width: int, height: int
    ) -> list[Component]:
        """Inject competing visual elements - multiple CTAs of same prominence."""
        components = []
        
        # Multiple primary buttons of same size
        button_width = (width - 64) // 3
        button_height = 44
        
        for i, label in enumerate(["Buy Now", "Learn More", "Subscribe"]):
            x = 16 + i * (button_width + 16)
            button = Component(
                type=ComponentType.BUTTON,
                bbox=(x, 80, button_width, button_height),
                label=label,
                color=self.template.PRIMARY_COLOR,  # All primary color - competing
                is_issue=True,
                issue_type=IssueType.COMPETING_ELEMENTS.value,
            )
            components.append(button)
        
        self.injected_issues.append(IssueType.COMPETING_ELEMENTS)
        return components
    
    def inject_spacing_cramped_margins(
        self, draw: ImageDraw.ImageDraw, width: int, height: int
    ) -> list[Component]:
        """Inject cramped margins - elements too close to edges."""
        components = []
        
        # Content with no margins
        card = Component(
            type=ComponentType.CARD,
            bbox=(2, 2, width - 4, height - 4),  # Only 2px margin
            is_issue=True,
            issue_type=IssueType.CRAMPED_MARGINS.value,
        )
        components.append(card)
        
        # Text with no padding
        text = Component(
            type=ComponentType.TEXT,
            bbox=(4, 4, width - 8, 20),
            label="Content with no margins",
            is_issue=True,
            issue_type=IssueType.CRAMPED_MARGINS.value,
        )
        components.append(text)
        
        self.injected_issues.append(IssueType.CRAMPED_MARGINS)
        return components
    
    def inject_spacing_inconsistent_rhythm(
        self, draw: ImageDraw.ImageDraw, width: int, height: int
    ) -> list[Component]:
        """Inject inconsistent spacing rhythm - irregular gaps."""
        components = []
        
        # Cards with inconsistent vertical spacing
        card_height = 60
        y_positions = [80, 155, 210, 295]  # Inconsistent gaps: 75, 55, 85
        
        for i, y in enumerate(y_positions):
            card = Component(
                type=ComponentType.CARD,
                bbox=(16, y, width - 32, card_height),
                is_issue=True,
                issue_type=IssueType.INCONSISTENT_RHYTHM.value,
            )
            components.append(card)
        
        self.injected_issues.append(IssueType.INCONSISTENT_RHYTHM)
        return components
    
    def inject_typography_small_font(
        self, draw: ImageDraw.ImageDraw, width: int, height: int
    ) -> list[Component]:
        """Inject font size that's too small (< 12px)."""
        components = []
        
        # Text with very small font
        small_text = Component(
            type=ComponentType.TEXT,
            bbox=(16, 80, width - 32, 12),
            label="This text is too small to read comfortably",
            font_size=self.VERY_SMALL_FONT,  # 8px - too small
            is_issue=True,
            issue_type=IssueType.FONT_SIZE_TOO_SMALL.value,
        )
        components.append(small_text)
        
        # Another small text
        small_text2 = Component(
            type=ComponentType.TEXT,
            bbox=(16, 100, width - 32, 12),
            label="Another line of tiny text",
            font_size=self.SMALL_FONT,  # 10px - still too small
            is_issue=True,
            issue_type=IssueType.FONT_SIZE_TOO_SMALL.value,
        )
        components.append(small_text2)
        
        self.injected_issues.append(IssueType.FONT_SIZE_TOO_SMALL)
        return components
    
    def inject_typography_hierarchy_break(
        self, draw: ImageDraw.ImageDraw, width: int, height: int
    ) -> list[Component]:
        """Inject typography hierarchy issues - smaller headings than body."""
        components = []
        
        # Small heading
        heading = Component(
            type=ComponentType.TEXT,
            bbox=(16, 80, width - 32, 14),
            label="Section Heading",
            font_size=12,  # Too small for heading
            is_issue=True,
            issue_type=IssueType.TYPOGRAPHY_HIERARCHY_BREAK.value,
        )
        components.append(heading)
        
        # Larger body text (breaks hierarchy)
        body = Component(
            type=ComponentType.TEXT,
            bbox=(16, 110, width - 32, 18),
            label="This body text is larger than the heading above it.",
            font_size=16,  # Larger than heading - issue
            is_issue=True,
            issue_type=IssueType.TYPOGRAPHY_HIERARCHY_BREAK.value,
        )
        components.append(body)
        
        self.injected_issues.append(IssueType.TYPOGRAPHY_HIERARCHY_BREAK)
        return components
    
    def inject_color_low_contrast(
        self, draw: ImageDraw.ImageDraw, width: int, height: int
    ) -> list[Component]:
        """Inject low contrast text - fails WCAG AA."""
        components = []
        
        # Draw light gray background
        draw.rectangle([16, 80, width - 16, 140], fill=self.LOW_CONTRAST_BG)
        
        # Low contrast text
        text = Component(
            type=ComponentType.TEXT,
            bbox=(24, 100, width - 48, 20),
            label="Low contrast text hard to read",
            text_color=self.LOW_CONTRAST_TEXT,  # Gray on light gray
            font_size=14,
            is_issue=True,
            issue_type=IssueType.LOW_CONTRAST.value,
        )
        components.append(text)
        
        self.injected_issues.append(IssueType.LOW_CONTRAST)
        return components
    
    def inject_color_accessibility(
        self, draw: ImageDraw.ImageDraw, width: int, height: int
    ) -> list[Component]:
        """Inject color that fails accessibility (color-only indication)."""
        components = []
        
        # Status indicators using only color
        statuses = [
            ("Success", "#10B981"),
            ("Warning", "#F59E0B"),
            ("Error", "#EF4444"),
        ]
        
        y = 80
        for label, color in statuses:
            # Colored dot indicator (no text label for status)
            draw.ellipse([20, y + 4, 32, y + 16], fill=color)
            
            text = Component(
                type=ComponentType.TEXT,
                bbox=(40, y, 100, 20),
                label=label,
                font_size=14,
                is_issue=True,
                issue_type=IssueType.COLOR_ACCESSIBILITY.value,
            )
            components.append(text)
            y += 30
        
        self.injected_issues.append(IssueType.COLOR_ACCESSIBILITY)
        return components
    
    def inject_alignment_off_grid(
        self, draw: ImageDraw.ImageDraw, width: int, height: int
    ) -> list[Component]:
        """Inject elements that don't align to grid."""
        components = []
        
        # Cards at irregular positions (not on 8px grid)
        positions = [
            (13, 83),   # Off by 3-5 pixels
            (19, 177),  # Off by 3 pixels
            (11, 271),  # Off by 3-5 pixels
        ]
        
        card_width = width - 32
        card_height = 80
        
        for x, y in positions:
            card = Component(
                type=ComponentType.CARD,
                bbox=(x, y, card_width, card_height),
                is_issue=True,
                issue_type=IssueType.OFF_GRID_ELEMENTS.value,
            )
            components.append(card)
        
        self.injected_issues.append(IssueType.OFF_GRID_ELEMENTS)
        return components
    
    def inject_alignment_misalignment(
        self, draw: ImageDraw.ImageDraw, width: int, height: int
    ) -> list[Component]:
        """Inject visually misaligned elements."""
        components = []
        
        # Labels and inputs not aligned
        label1 = Component(
            type=ComponentType.TEXT,
            bbox=(16, 80, 80, 16),
            label="Email:",
            font_size=14,
            is_issue=True,
            issue_type=IssueType.MISALIGNMENT.value,
        )
        components.append(label1)
        
        input1 = Component(
            type=ComponentType.INPUT,
            bbox=(110, 82, width - 110 - 16, 40),  # 2px off vertically
            is_issue=True,
            issue_type=IssueType.MISALIGNMENT.value,
        )
        components.append(input1)
        
        label2 = Component(
            type=ComponentType.TEXT,
            bbox=(16, 140, 80, 16),
            label="Name:",
            font_size=14,
            is_issue=True,
            issue_type=IssueType.MISALIGNMENT.value,
        )
        components.append(label2)
        
        input2 = Component(
            type=ComponentType.INPUT,
            bbox=(108, 138, width - 108 - 16, 40),  # Different offset
            is_issue=True,
            issue_type=IssueType.MISALIGNMENT.value,
        )
        components.append(input2)
        
        self.injected_issues.append(IssueType.MISALIGNMENT)
        return components
    
    def inject_components_size_inconsistency(
        self, draw: ImageDraw.ImageDraw, width: int, height: int
    ) -> list[Component]:
        """Inject buttons with inconsistent sizes."""
        components = []
        
        # Same button type with different sizes
        button_sizes = [
            (100, 36),
            (140, 52),
            (80, 40),
        ]
        
        x = 16
        for btn_width, btn_height in button_sizes:
            button = Component(
                type=ComponentType.BUTTON,
                bbox=(x, 80, btn_width, btn_height),
                label="Action",
                is_issue=True,
                issue_type=IssueType.SIZE_INCONSISTENCY.value,
            )
            components.append(button)
            x += btn_width + 16
        
        self.injected_issues.append(IssueType.SIZE_INCONSISTENCY)
        return components
    
    def inject_components_style_proliferation(
        self, draw: ImageDraw.ImageDraw, width: int, height: int
    ) -> list[Component]:
        """Inject too many button variants/styles."""
        components = []
        
        # Many different button styles
        button_styles = [
            ("#3B82F6", "#FFFFFF", "Primary"),
            ("#10B981", "#FFFFFF", "Success"),
            ("#EF4444", "#FFFFFF", "Danger"),
            ("#F59E0B", "#FFFFFF", "Warning"),
            ("#8B5CF6", "#FFFFFF", "Purple"),
            ("#EC4899", "#FFFFFF", "Pink"),
        ]
        
        y = 80
        for bg_color, text_color, label in button_styles:
            button = Component(
                type=ComponentType.BUTTON,
                bbox=(16, y, width - 32, 40),
                label=label,
                color=bg_color,
                text_color=text_color,
                is_issue=True,
                issue_type=IssueType.STYLE_PROLIFERATION.value,
            )
            components.append(button)
            y += 50
        
        self.injected_issues.append(IssueType.STYLE_PROLIFERATION)
        return components
    
    def inject_states_missing_empty(
        self, draw: ImageDraw.ImageDraw, width: int, height: int
    ) -> list[Component]:
        """Inject a list/table without empty state design."""
        components = []
        
        # Just an empty container - no empty state design
        card = Component(
            type=ComponentType.CARD,
            bbox=(16, 80, width - 32, 400),
            is_issue=True,
            issue_type=IssueType.MISSING_EMPTY_STATE.value,
        )
        components.append(card)
        
        # Header exists but no empty state content
        header = Component(
            type=ComponentType.TEXT,
            bbox=(24, 90, 100, 20),
            label="Items List",
            font_size=16,
            is_issue=True,
            issue_type=IssueType.MISSING_EMPTY_STATE.value,
        )
        components.append(header)
        
        self.injected_issues.append(IssueType.MISSING_EMPTY_STATE)
        return components
    
    def inject_states_missing_error(
        self, draw: ImageDraw.ImageDraw, width: int, height: int
    ) -> list[Component]:
        """Inject a form without proper error state design."""
        components = []
        
        # Input with red border (error) but no error message
        input_error = Component(
            type=ComponentType.INPUT,
            bbox=(16, 80, width - 32, 44),
            label="invalid@email",
            is_issue=True,
            issue_type=IssueType.MISSING_ERROR_STATE.value,
        )
        components.append(input_error)
        
        # No error message explaining what's wrong
        
        self.injected_issues.append(IssueType.MISSING_ERROR_STATE)
        return components
    
    def inject_density_too_dense(
        self, draw: ImageDraw.ImageDraw, width: int, height: int
    ) -> list[Component]:
        """Inject a layout that's too dense - elements too close together."""
        components = []
        
        # Many small elements packed tightly
        y = 80
        for i in range(10):
            card = Component(
                type=ComponentType.CARD,
                bbox=(16, y, width - 32, 40),  # Only 40px height
                is_issue=True,
                issue_type=IssueType.TOO_DENSE.value,
            )
            components.append(card)
            
            text = Component(
                type=ComponentType.TEXT,
                bbox=(24, y + 12, width - 48, 16),
                label=f"Item {i+1}",
                font_size=12,
                is_issue=True,
                issue_type=IssueType.TOO_DENSE.value,
            )
            components.append(text)
            
            y += 44  # Very tight spacing
        
        self.injected_issues.append(IssueType.TOO_DENSE)
        return components
    
    def inject_density_too_sparse(
        self, draw: ImageDraw.ImageDraw, width: int, height: int
    ) -> list[Component]:
        """Inject a layout that's too sparse - wasted space."""
        components = []
        
        # Single small element in large space
        card = Component(
            type=ComponentType.CARD,
            bbox=(16, 80, width - 32, 60),
            is_issue=True,
            issue_type=IssueType.TOO_SPARSE.value,
        )
        components.append(card)
        
        text = Component(
            type=ComponentType.TEXT,
            bbox=(24, 100, width - 48, 20),
            label="Only content",
            font_size=14,
            is_issue=True,
            issue_type=IssueType.TOO_SPARSE.value,
        )
        components.append(text)
        
        # Lots of empty space below
        
        self.injected_issues.append(IssueType.TOO_SPARSE)
        return components


# Mapping of issue types to injector methods
INJECTOR_MAP: dict[IssueType, Callable] = {
    IssueType.NO_FOCAL_POINT: IssueInjector.inject_hierarchy_no_focal_point,
    IssueType.COMPETING_ELEMENTS: IssueInjector.inject_hierarchy_competing_elements,
    IssueType.CRAMPED_MARGINS: IssueInjector.inject_spacing_cramped_margins,
    IssueType.INCONSISTENT_RHYTHM: IssueInjector.inject_spacing_inconsistent_rhythm,
    IssueType.FONT_SIZE_TOO_SMALL: IssueInjector.inject_typography_small_font,
    IssueType.TYPOGRAPHY_HIERARCHY_BREAK: IssueInjector.inject_typography_hierarchy_break,
    IssueType.LOW_CONTRAST: IssueInjector.inject_color_low_contrast,
    IssueType.COLOR_ACCESSIBILITY: IssueInjector.inject_color_accessibility,
    IssueType.OFF_GRID_ELEMENTS: IssueInjector.inject_alignment_off_grid,
    IssueType.MISALIGNMENT: IssueInjector.inject_alignment_misalignment,
    IssueType.SIZE_INCONSISTENCY: IssueInjector.inject_components_size_inconsistency,
    IssueType.STYLE_PROLIFERATION: IssueInjector.inject_components_style_proliferation,
    IssueType.MISSING_EMPTY_STATE: IssueInjector.inject_states_missing_empty,
    IssueType.MISSING_ERROR_STATE: IssueInjector.inject_states_missing_error,
    IssueType.TOO_DENSE: IssueInjector.inject_density_too_dense,
    IssueType.TOO_SPARSE: IssueInjector.inject_density_too_sparse,
}


def get_issue_dimension(issue_type: IssueType) -> str:
    """Map issue type to audit dimension."""
    dimension_map = {
        # Hierarchy
        IssueType.NO_FOCAL_POINT: "visual_hierarchy",
        IssueType.COMPETING_ELEMENTS: "visual_hierarchy",
        IssueType.POOR_VISUAL_WEIGHT: "visual_hierarchy",
        
        # Spacing
        IssueType.CRAMPED_MARGINS: "spacing_rhythm",
        IssueType.INCONSISTENT_RHYTHM: "spacing_rhythm",
        IssueType.GRID_VIOLATIONS: "spacing_rhythm",
        
        # Typography
        IssueType.FONT_SIZE_TOO_SMALL: "typography",
        IssueType.TYPOGRAPHY_HIERARCHY_BREAK: "typography",
        IssueType.FONT_WEIGHT_INCONSISTENCY: "typography",
        
        # Color
        IssueType.LOW_CONTRAST: "color",
        IssueType.INSUFFICIENT_DISTINCT_COLORS: "color",
        IssueType.COLOR_ACCESSIBILITY: "accessibility",
        
        # Alignment
        IssueType.OFF_GRID_ELEMENTS: "alignment_grid",
        IssueType.MISALIGNMENT: "alignment_grid",
        IssueType.CENTERING_ISSUES: "alignment_grid",
        
        # Components
        IssueType.SIZE_INCONSISTENCY: "components",
        IssueType.STYLE_PROLIFERATION: "components",
        IssueType.VARIANT_CHAOS: "components",
        
        # States
        IssueType.MISSING_EMPTY_STATE: "empty_states",
        IssueType.MISSING_ERROR_STATE: "error_states",
        IssueType.MISSING_LOADING_STATE: "loading_states",
        
        # Density
        IssueType.TOO_DENSE: "density",
        IssueType.TOO_SPARSE: "density",
    }
    return dimension_map.get(issue_type, "unknown")


def get_issue_severity(issue_type: IssueType) -> str:
    """Map issue type to expected severity."""
    severity_map = {
        # Critical - accessibility/usability blocking
        IssueType.FONT_SIZE_TOO_SMALL: "high",
        IssueType.LOW_CONTRAST: "high",
        IssueType.COLOR_ACCESSIBILITY: "high",
        IssueType.MISSING_ERROR_STATE: "medium",
        
        # High - significant UX impact
        IssueType.NO_FOCAL_POINT: "medium",
        IssueType.COMPETING_ELEMENTS: "medium",
        IssueType.CRAMPED_MARGINS: "medium",
        IssueType.TOO_DENSE: "medium",
        
        # Medium - noticeable but not blocking
        IssueType.INCONSISTENT_RHYTHM: "medium",
        IssueType.TYPOGRAPHY_HIERARCHY_BREAK: "medium",
        IssueType.OFF_GRID_ELEMENTS: "low",
        IssueType.MISALIGNMENT: "medium",
        
        # Low - polish level
        IssueType.SIZE_INCONSISTENCY: "low",
        IssueType.STYLE_PROLIFERATION: "low",
        IssueType.MISSING_EMPTY_STATE: "low",
        IssueType.TOO_SPARSE: "low",
    }
    return severity_map.get(issue_type, "medium")