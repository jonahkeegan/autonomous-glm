"""
Token extraction module for Autonomous-GLM.

Provides color, spacing, and typography extraction from UI components,
with matching to design system tokens.
"""

from .models import (
    # Color models
    RGB,
    HSL,
    LAB,
    HexColor,
    ColorResult,
    ColorCluster,
    # Spacing models
    Margins,
    Padding,
    SpacingPattern,
    # Typography models
    FontWeight,
    FontSizeEstimate,
    FontWeightEstimate,
    TypographyResult,
    # Token matching models
    TokenType,
    TokenMatch,
    TokenMatchResult,
    DesignToken,
    DesignSystemTokens,
)
from .color import (
    ColorExtractor,
    normalize_color,
    extract_colors,
    get_dominant_color,
    cluster_colors,
    DEFAULT_N_CLUSTERS,
    MIN_PIXELS_FOR_EXTRACTION,
    GRADIENT_VARIANCE_THRESHOLD,
)
from .spacing import (
    SpacingAnalyzer,
    quantize_to_grid,
    quantize_to_standard,
    infer_margins,
    infer_padding,
    detect_spacing_pattern,
    STANDARD_SPACING_VALUES,
    DEFAULT_GRID_BASE,
    GRID_BASES,
)
from .typography import (
    TypographyDetector,
    estimate_font_size,
    estimate_font_weight,
    detect_line_height,
    FONT_SIZE_FACTOR,
    DEFAULT_LINE_HEIGHT,
    WEIGHT_DENSITY_THRESHOLDS,
    WEIGHT_NUMERIC,
)
from .matcher import (
    TokenMatcher,
    match_color,
    match_spacing,
    match_typography,
    DEFAULT_COLOR_DISTANCE_THRESHOLD,
    DEFAULT_SPACING_TOLERANCE,
    DEFAULT_TYPOGRAPHY_SIZE_TOLERANCE,
)


__all__ = [
    # Color models
    "RGB",
    "HSL",
    "LAB",
    "HexColor",
    "ColorResult",
    "ColorCluster",
    # Spacing models
    "Margins",
    "Padding",
    "SpacingPattern",
    # Typography models
    "FontWeight",
    "FontSizeEstimate",
    "FontWeightEstimate",
    "TypographyResult",
    # Token matching models
    "TokenType",
    "TokenMatch",
    "TokenMatchResult",
    "DesignToken",
    "DesignSystemTokens",
    # Color extraction
    "ColorExtractor",
    "normalize_color",
    "extract_colors",
    "get_dominant_color",
    "cluster_colors",
    "DEFAULT_N_CLUSTERS",
    "MIN_PIXELS_FOR_EXTRACTION",
    "GRADIENT_VARIANCE_THRESHOLD",
    # Spacing analysis
    "SpacingAnalyzer",
    "quantize_to_grid",
    "quantize_to_standard",
    "infer_margins",
    "infer_padding",
    "detect_spacing_pattern",
    "STANDARD_SPACING_VALUES",
    "DEFAULT_GRID_BASE",
    "GRID_BASES",
    # Typography detection
    "TypographyDetector",
    "estimate_font_size",
    "estimate_font_weight",
    "detect_line_height",
    "FONT_SIZE_FACTOR",
    "DEFAULT_LINE_HEIGHT",
    "WEIGHT_DENSITY_THRESHOLDS",
    "WEIGHT_NUMERIC",
    # Token matching
    "TokenMatcher",
    "match_color",
    "match_spacing",
    "match_typography",
    "DEFAULT_COLOR_DISTANCE_THRESHOLD",
    "DEFAULT_SPACING_TOLERANCE",
    "DEFAULT_TYPOGRAPHY_SIZE_TOLERANCE",
]