"""
Spacing analysis utilities for token extraction.

Provides margin/padding inference from component bounding boxes.
"""

from collections import Counter
from typing import Optional

from .models import (
    Margins,
    Padding,
    SpacingPattern,
)


# Standard spacing values in design systems
STANDARD_SPACING_VALUES = [4, 8, 12, 16, 20, 24, 32, 40, 48, 64, 80, 96]

# Default grid base for quantization
DEFAULT_GRID_BASE = 4

# Common grid bases
GRID_BASES = [4, 8]


class SpacingAnalyzer:
    """Analyze spacing patterns from component layouts."""
    
    def __init__(self, grid_base: int = DEFAULT_GRID_BASE):
        """Initialize the spacing analyzer.
        
        Args:
            grid_base: Grid base for quantization (default: 4)
        """
        self.grid_base = grid_base
    
    def infer_margins(
        self,
        component_bbox: tuple[float, float, float, float],
        screen_width: int,
        screen_height: int,
        normalized: bool = True
    ) -> Margins:
        """Infer margins from component position.
        
        Args:
            component_bbox: (x, y, width, height) of component
            screen_width: Screen width in pixels
            screen_height: Screen height in pixels
            normalized: Whether bbox coordinates are normalized (0-1)
        
        Returns:
            Margins object with inferred margin values
        """
        x, y, width, height = component_bbox
        
        if normalized:
            # Convert to absolute pixels
            x = int(x * screen_width)
            y = int(y * screen_height)
            width = int(width * screen_width)
            height = int(height * screen_height)
        
        # Calculate margins from edges
        margin_left = x
        margin_top = y
        margin_right = screen_width - (x + width)
        margin_bottom = screen_height - (y + height)
        
        return Margins(
            top=max(0, margin_top),
            right=max(0, margin_right),
            bottom=max(0, margin_bottom),
            left=max(0, margin_left)
        )
    
    def infer_padding(
        self,
        container_bbox: tuple[float, float, float, float],
        children_bboxes: list[tuple[float, float, float, float]],
        normalized: bool = True
    ) -> Padding:
        """Infer padding from container and its children.
        
        Args:
            container_bbox: (x, y, width, height) of container
            children_bboxes: List of (x, y, width, height) for children
            normalized: Whether coordinates are normalized (0-1)
        
        Returns:
            Padding object with inferred padding values
        """
        if not children_bboxes:
            return Padding()
        
        cx, cy, cw, ch = container_bbox
        
        # Find min/max child positions
        min_x = min(c[0] for c in children_bboxes)
        min_y = min(c[1] for c in children_bboxes)
        max_x = max(c[0] + c[2] for c in children_bboxes)
        max_y = max(c[1] + c[3] for c in children_bboxes)
        
        if normalized:
            # Calculate padding as normalized difference
            padding_left = min_x - cx
            padding_top = min_y - cy
            padding_right = (cx + cw) - max_x
            padding_bottom = (cy + ch) - max_y
            
            # Convert to approximate pixels (assuming 1000px base)
            padding_left = int(padding_left * 1000)
            padding_top = int(padding_top * 1000)
            padding_right = int(padding_right * 1000)
            padding_bottom = int(padding_bottom * 1000)
        else:
            padding_left = min_x - cx
            padding_top = min_y - cy
            padding_right = (cx + cw) - max_x
            padding_bottom = (cy + ch) - max_y
        
        return Padding(
            top=max(0, int(padding_top)),
            right=max(0, int(padding_right)),
            bottom=max(0, int(padding_bottom)),
            left=max(0, int(padding_left))
        )
    
    def detect_spacing_pattern(
        self,
        spacings: list[int],
        min_samples: int = 3
    ) -> SpacingPattern:
        """Detect consistent spacing pattern from list of values.
        
        Args:
            spacings: List of spacing values in pixels
            min_samples: Minimum samples to detect pattern
        
        Returns:
            SpacingPattern with detected pattern info
        """
        if not spacings:
            return SpacingPattern(
                values=[],
                most_common=0,
                grid_base=self.grid_base,
                confidence=0.0
            )
        
        # Quantize all values to grid
        quantized = [quantize_to_grid(s, self.grid_base) for s in spacings]
        
        # Find most common value
        counter = Counter(quantized)
        most_common = counter.most_common(1)[0][0] if counter else 0
        
        # Calculate confidence based on consistency
        if len(spacings) >= min_samples:
            # How many values are at or near the most common?
            tolerance = self.grid_base
            near_common = sum(
                1 for s in spacings 
                if abs(s - most_common) <= tolerance
            )
            confidence = near_common / len(spacings)
        else:
            confidence = 0.5  # Low confidence with few samples
        
        # Try to detect grid base (4 or 8)
        detected_base = self._detect_grid_base(quantized)
        
        return SpacingPattern(
            values=quantized,
            most_common=most_common,
            grid_base=detected_base,
            confidence=confidence
        )
    
    def _detect_grid_base(self, values: list[int]) -> int:
        """Detect whether values align better with 4px or 8px grid.
        
        Args:
            values: List of quantized spacing values
        
        Returns:
            Detected grid base (4 or 8)
        """
        if not values:
            return self.grid_base
        
        # Count how many values are divisible by each base
        count_4 = sum(1 for v in values if v % 4 == 0)
        count_8 = sum(1 for v in values if v % 8 == 0)
        
        # Prefer 8 if most values align with it
        if count_8 > len(values) * 0.7:
            return 8
        return 4


def quantize_to_grid(value: float, grid_base: int = DEFAULT_GRID_BASE) -> int:
    """Quantize a value to the nearest grid multiple.
    
    Args:
        value: Value to quantize
        grid_base: Grid base (e.g., 4 or 8)
    
    Returns:
        Quantized value
    """
    return round(value / grid_base) * grid_base


def quantize_to_standard(value: float) -> int:
    """Quantize a value to the nearest standard spacing value.
    
    Args:
        value: Value to quantize
    
    Returns:
        Nearest standard spacing value
    """
    if value <= 0:
        return 0
    
    # Find nearest standard value
    nearest = min(
        STANDARD_SPACING_VALUES,
        key=lambda std: abs(std - value)
    )
    return nearest


def infer_margins(
    component_bbox: tuple[float, float, float, float],
    screen_width: int,
    screen_height: int,
    normalized: bool = True
) -> Margins:
    """Convenience function to infer margins.
    
    Args:
        component_bbox: (x, y, width, height) of component
        screen_width: Screen width in pixels
        screen_height: Screen height in pixels
        normalized: Whether bbox coordinates are normalized (0-1)
    
    Returns:
        Margins object with inferred margin values
    """
    analyzer = SpacingAnalyzer()
    return analyzer.infer_margins(
        component_bbox, screen_width, screen_height, normalized
    )


def infer_padding(
    container_bbox: tuple[float, float, float, float],
    children_bboxes: list[tuple[float, float, float, float]],
    normalized: bool = True
) -> Padding:
    """Convenience function to infer padding.
    
    Args:
        container_bbox: (x, y, width, height) of container
        children_bboxes: List of (x, y, width, height) for children
        normalized: Whether coordinates are normalized (0-1)
    
    Returns:
        Padding object with inferred padding values
    """
    analyzer = SpacingAnalyzer()
    return analyzer.infer_padding(container_bbox, children_bboxes, normalized)


def detect_spacing_pattern(
    spacings: list[int],
    grid_base: int = DEFAULT_GRID_BASE
) -> SpacingPattern:
    """Convenience function to detect spacing pattern.
    
    Args:
        spacings: List of spacing values in pixels
        grid_base: Grid base for quantization
    
    Returns:
        SpacingPattern with detected pattern info
    """
    analyzer = SpacingAnalyzer(grid_base=grid_base)
    return analyzer.detect_spacing_pattern(spacings)