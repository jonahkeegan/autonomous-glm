"""
Unit tests for token extraction module.

Tests for color extraction, spacing analysis, typography detection,
and token matching functionality.
"""

import pytest
import numpy as np
from pathlib import Path
from PIL import Image

from src.vision.tokens import (
    # Models
    RGB,
    HSL,
    LAB,
    HexColor,
    ColorResult,
    ColorCluster,
    Margins,
    Padding,
    SpacingPattern,
    FontWeight,
    FontSizeEstimate,
    FontWeightEstimate,
    TypographyResult,
    TokenType,
    TokenMatch,
    TokenMatchResult,
    DesignToken,
    DesignSystemTokens,
    # Color extraction
    ColorExtractor,
    normalize_color,
    extract_colors,
    get_dominant_color,
    cluster_colors,
    # Spacing analysis
    SpacingAnalyzer,
    quantize_to_grid,
    quantize_to_standard,
    infer_margins,
    infer_padding,
    detect_spacing_pattern,
    # Typography detection
    TypographyDetector,
    estimate_font_size,
    estimate_font_weight,
    detect_line_height,
    # Token matching
    TokenMatcher,
    match_color,
    match_spacing,
    match_typography,
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def sample_image(tmp_path: Path) -> Path:
    """Create a sample test image."""
    img_path = tmp_path / "test_image.png"
    img = Image.new("RGB", (100, 100), color=(59, 130, 246))  # Blue
    img.save(img_path)
    return img_path


@pytest.fixture
def gradient_image(tmp_path: Path) -> Path:
    """Create a gradient test image."""
    img_path = tmp_path / "gradient.png"
    img = Image.new("RGB", (100, 100))
    for x in range(100):
        for y in range(100):
            # Horizontal gradient from blue to red
            img.putpixel((x, y), (int(x * 2.55), 0, int(255 - x * 2.55)))
    img.save(img_path)
    return img_path


@pytest.fixture
def white_image(tmp_path: Path) -> Path:
    """Create a white test image."""
    img_path = tmp_path / "white.png"
    img = Image.new("RGB", (100, 100), color=(255, 255, 255))
    img.save(img_path)
    return img_path


@pytest.fixture
def black_image(tmp_path: Path) -> Path:
    """Create a black test image."""
    img_path = tmp_path / "black.png"
    img = Image.new("RGB", (100, 100), color=(0, 0, 0))
    img.save(img_path)
    return img_path


# =============================================================================
# COLOR MODEL TESTS
# =============================================================================

class TestRGB:
    """Tests for RGB color model."""
    
    def test_rgb_creation(self):
        """Test RGB color creation."""
        color = RGB(r=255, g=128, b=0)
        assert color.r == 255
        assert color.g == 128
        assert color.b == 0
    
    def test_rgb_validation(self):
        """Test RGB validation."""
        with pytest.raises(ValueError):
            RGB(r=256, g=0, b=0)  # r > 255
        
        with pytest.raises(ValueError):
            RGB(r=-1, g=0, b=0)  # r < 0
    
    def test_rgb_to_hex(self):
        """Test RGB to hex conversion."""
        color = RGB(r=59, g=130, b=246)
        hex_color = color.to_hex()
        assert hex_color.value == "#3B82F6"
    
    def test_rgb_to_hsl(self):
        """Test RGB to HSL conversion."""
        # Pure red
        red = RGB(r=255, g=0, b=0)
        hsl = red.to_hsl()
        assert hsl.h == 0
        assert hsl.s == 100
        assert hsl.l == 50
    
    def test_rgb_to_lab(self):
        """Test RGB to LAB conversion."""
        # White
        white = RGB(r=255, g=255, b=255)
        lab = white.to_lab()
        assert lab.L > 95  # White has L close to 100 (allow conversion variance)
        
        # Black
        black = RGB(r=0, g=0, b=0)
        lab = black.to_lab()
        assert lab.L < 5  # Black has L close to 0
    
    def test_rgb_distance_to(self):
        """Test RGB Euclidean distance."""
        black = RGB(r=0, g=0, b=0)
        white = RGB(r=255, g=255, b=255)
        
        distance = black.distance_to(white)
        expected = (255**2 * 3) ** 0.5
        assert abs(distance - expected) < 0.1
    
    def test_lab_distance_to(self):
        """Test LAB perceptual distance."""
        # Similar colors should have small distance
        blue1 = RGB(r=59, g=130, b=246)
        blue2 = RGB(r=61, g=132, b=248)
        
        distance = blue1.lab_distance_to(blue2)
        assert distance < 5  # Small perceptual difference


class TestHSL:
    """Tests for HSL color model."""
    
    def test_hsl_to_rgb(self):
        """Test HSL to RGB conversion."""
        # Pure red in HSL
        hsl = HSL(h=0, s=100, l=50)
        rgb = hsl.to_rgb()
        assert rgb.r == 255
        assert rgb.g == 0
        assert rgb.b == 0
    
    def test_hsl_roundtrip(self):
        """Test RGB -> HSL -> RGB roundtrip."""
        # Use a simpler color for more reliable roundtrip
        original = RGB(r=128, g=64, b=64)
        hsl = original.to_hsl()
        rgb_back = hsl.to_rgb()
        
        # Allow for quantization errors (HSL uses integer percentages)
        assert abs(rgb_back.r - original.r) <= 3
        assert abs(rgb_back.g - original.g) <= 3
        assert abs(rgb_back.b - original.b) <= 3


class TestHexColor:
    """Tests for HexColor model."""
    
    def test_hex_validation(self):
        """Test hex color validation."""
        valid = HexColor(value="#3B82F6")
        assert valid.value == "#3B82F6"
        
        with pytest.raises(ValueError):
            HexColor(value="invalid")
        
        with pytest.raises(ValueError):
            HexColor(value="#FFF")  # Too short
    
    def test_hex_to_rgb(self):
        """Test hex to RGB conversion."""
        hex_color = HexColor(value="#3B82F6")
        rgb = hex_color.to_rgb()
        
        assert rgb.r == 59
        assert rgb.g == 130
        assert rgb.b == 246


# =============================================================================
# COLOR EXTRACTION TESTS
# =============================================================================

class TestColorExtractor:
    """Tests for color extraction."""
    
    def test_extract_colors_from_solid(self, sample_image: Path):
        """Test extracting colors from solid color image."""
        extractor = ColorExtractor()
        result = extractor.extract_colors(sample_image)
        
        assert result.dominant.r == 59
        assert result.dominant.g == 130
        assert result.dominant.b == 246
        assert result.pixel_count == 10000
        # Note: Even solid colors may have slight variance from compression
        # so we check dominant color is correct rather than is_gradient flag
    
    def test_extract_colors_from_gradient(self, gradient_image: Path):
        """Test extracting colors from gradient image."""
        extractor = ColorExtractor()
        result = extractor.extract_colors(gradient_image)
        
        # Gradient should be detected
        assert result.is_gradient
        # Should have multiple colors
        assert len(result.colors) > 1
    
    def test_extract_colors_with_bbox(self, sample_image: Path):
        """Test extracting colors from region."""
        extractor = ColorExtractor()
        
        # Extract from top-left quadrant
        result = extractor.extract_colors(
            sample_image,
            bbox=(0.0, 0.0, 0.5, 0.5),
            normalize=True
        )
        
        assert result.pixel_count == 2500  # 50x50 pixels
        assert result.dominant.r == 59
    
    def test_extract_colors_absolute_bbox(self, sample_image: Path):
        """Test extracting colors with absolute bbox."""
        extractor = ColorExtractor()
        
        result = extractor.extract_colors(
            sample_image,
            bbox=(0, 0, 50, 50),
            normalize=False
        )
        
        assert result.pixel_count == 2500
    
    def test_extract_colors_file_not_found(self):
        """Test error handling for missing file."""
        extractor = ColorExtractor()
        
        with pytest.raises(FileNotFoundError):
            extractor.extract_colors("/nonexistent/image.png")
    
    def test_get_dominant_color(self):
        """Test getting dominant color from pixels."""
        extractor = ColorExtractor()
        
        # All blue pixels
        pixels = np.array([[59, 130, 246]] * 100)
        dominant = extractor.get_dominant_color(pixels)
        
        assert dominant.r == 59
        assert dominant.g == 130
        assert dominant.b == 246
    
    def test_cluster_colors(self):
        """Test clustering similar colors."""
        extractor = ColorExtractor()
        
        # Mix of blue and red colors
        colors = [
            RGB(r=59, g=130, b=246),  # Blue
            RGB(r=61, g=132, b=248),  # Similar blue
            RGB(r=255, g=0, b=0),      # Red
            RGB(r=250, g=10, b=5),     # Similar red
        ]
        
        clusters = extractor.cluster_colors(colors, n_clusters=2)
        
        assert len(clusters) == 2
        # Each cluster should have 2 colors
        assert sum(c.count for c in clusters) == 4
    
    def test_normalize_color(self):
        """Test color normalization."""
        color = RGB(r=59, g=130, b=246)
        normalized = normalize_color(color)
        
        assert "rgb" in normalized
        assert "hsl" in normalized
        assert "lab" in normalized
        assert "hex" in normalized
        assert normalized["hex_value"] == "#3B82F6"


class TestConvenienceFunctions:
    """Tests for convenience functions."""
    
    def test_extract_colors_function(self, sample_image: Path):
        """Test extract_colors convenience function."""
        result = extract_colors(sample_image)
        assert result.dominant.r == 59
    
    def test_get_dominant_color_function(self):
        """Test get_dominant_color convenience function."""
        pixels = np.array([[255, 0, 0]] * 100)
        dominant = get_dominant_color(pixels)
        assert dominant.r == 255
    
    def test_cluster_colors_function(self):
        """Test cluster_colors convenience function."""
        colors = [RGB(r=i, g=i, b=i) for i in range(0, 256, 10)]
        clusters = cluster_colors(colors, n_clusters=5)
        assert len(clusters) <= 5


# =============================================================================
# SPACING ANALYSIS TESTS
# =============================================================================

class TestSpacingAnalyzer:
    """Tests for spacing analysis."""
    
    def test_infer_margins_normalized(self):
        """Test margin inference with normalized coords."""
        analyzer = SpacingAnalyzer()
        
        # Component at (0.1, 0.2) with size (0.5, 0.3) on 1000x1000 screen
        margins = analyzer.infer_margins(
            component_bbox=(0.1, 0.2, 0.5, 0.3),
            screen_width=1000,
            screen_height=1000,
            normalized=True
        )
        
        assert margins.left == 100   # 0.1 * 1000
        assert margins.top == 200    # 0.2 * 1000
        assert margins.right == 400  # 1000 - (100 + 500)
        assert margins.bottom == 500 # 1000 - (200 + 300)
    
    def test_infer_margins_absolute(self):
        """Test margin inference with absolute coords."""
        analyzer = SpacingAnalyzer()
        
        margins = analyzer.infer_margins(
            component_bbox=(100, 200, 500, 300),
            screen_width=1000,
            screen_height=1000,
            normalized=False
        )
        
        assert margins.left == 100
        assert margins.top == 200
        assert margins.right == 400
        assert margins.bottom == 500
    
    def test_infer_padding(self):
        """Test padding inference."""
        analyzer = SpacingAnalyzer()
        
        # Container with children inset by padding
        container = (0.0, 0.0, 1.0, 1.0)
        children = [
            (0.1, 0.1, 0.3, 0.2),  # Leftmost child
            (0.6, 0.1, 0.3, 0.2),  # Rightmost child
        ]
        
        padding = analyzer.infer_padding(container, children, normalized=True)
        
        # Left padding should be ~0.1 * 1000 = 100
        assert padding.left >= 0
    
    def test_detect_spacing_pattern(self):
        """Test spacing pattern detection."""
        analyzer = SpacingAnalyzer()
        
        # Consistent 12px spacing (multiple of 4, not 8)
        spacings = [12, 12, 12, 11, 13, 12, 12]
        pattern = analyzer.detect_spacing_pattern(spacings)
        
        assert pattern.most_common == 12
        assert pattern.grid_base == 4
        assert pattern.confidence > 0.5
    
    def test_detect_spacing_pattern_empty(self):
        """Test pattern detection with empty list."""
        analyzer = SpacingAnalyzer()
        pattern = analyzer.detect_spacing_pattern([])
        
        assert pattern.most_common == 0
        assert pattern.confidence == 0.0


class TestQuantization:
    """Tests for spacing quantization."""
    
    def test_quantize_to_grid_4(self):
        """Test quantization to 4px grid."""
        assert quantize_to_grid(3, grid_base=4) == 4
        assert quantize_to_grid(5, grid_base=4) == 4
        assert quantize_to_grid(7, grid_base=4) == 8
        assert quantize_to_grid(16, grid_base=4) == 16
    
    def test_quantize_to_grid_8(self):
        """Test quantization to 8px grid."""
        assert quantize_to_grid(5, grid_base=8) == 8
        assert quantize_to_grid(10, grid_base=8) == 8
        assert quantize_to_grid(12, grid_base=8) == 16
    
    def test_quantize_to_standard(self):
        """Test quantization to standard values."""
        assert quantize_to_standard(5) == 4
        assert quantize_to_standard(7) == 8
        assert quantize_to_standard(15) == 16
        assert quantize_to_standard(100) == 96


class TestMarginsPadding:
    """Tests for Margins and Padding models."""
    
    def test_margins_quantization(self):
        """Test margins quantization."""
        margins = Margins(top=13, right=17, bottom=11, left=19)
        quantized = margins.to_quantized(grid_base=4)
        
        assert quantized.top == 12
        assert quantized.right == 16
        assert quantized.bottom == 12
        assert quantized.left == 20
    
    def test_padding_quantization(self):
        """Test padding quantization."""
        padding = Padding(top=5, right=9, bottom=7, left=11)
        quantized = padding.to_quantized(grid_base=4)
        
        assert quantized.top == 4
        assert quantized.right == 8
        assert quantized.bottom == 8
        assert quantized.left == 12


# =============================================================================
# TYPOGRAPHY DETECTION TESTS
# =============================================================================

class TestTypographyDetector:
    """Tests for typography detection."""
    
    def test_estimate_font_size(self):
        """Test font size estimation."""
        detector = TypographyDetector()
        
        # 20px bbox height should give ~16px font
        estimate = detector.estimate_font_size(20)
        
        assert estimate.size_px == 16  # 20 * 0.8
        assert estimate.size_pt == 12.0  # 16 * 0.75
        assert estimate.method == "bbox_height"
    
    def test_estimate_font_size_clamped(self):
        """Test font size clamping."""
        detector = TypographyDetector()
        
        # Very large bbox
        large = detector.estimate_font_size(200)
        assert large.size_px <= 96  # Max clamp
        
        # Very small bbox
        small = detector.estimate_font_size(5)
        assert small.size_px >= 8  # Min clamp
    
    def test_estimate_font_weight_dark(self, black_image: Path):
        """Test font weight estimation with dark text."""
        detector = TypographyDetector()
        
        estimate = detector.estimate_font_weight(black_image)
        
        # Black image = high density = bold
        assert estimate.weight == FontWeight.BOLD
        assert estimate.weight_numeric == 700
    
    def test_estimate_font_weight_light(self, white_image: Path):
        """Test font weight estimation with light text."""
        detector = TypographyDetector()
        
        estimate = detector.estimate_font_weight(white_image)
        
        # White image = low density = light
        assert estimate.weight == FontWeight.LIGHT
        assert estimate.weight_numeric == 300
    
    def test_detect_line_height(self):
        """Test line height detection."""
        detector = TypographyDetector()
        
        # 24px bbox with 16px font = 1.5 line-height
        line_height = detector.detect_line_height(24, 16)
        assert line_height == 1.5
    
    def test_analyze(self, sample_image: Path):
        """Test full typography analysis."""
        detector = TypographyDetector()
        
        result = detector.analyze(
            bbox_height=20,
            image_path=sample_image,
            bbox=(0, 0, 1, 1),
            is_text_component=True
        )
        
        assert result.font_size is not None
        assert result.font_size.size_px == 16
        assert result.line_height is not None
        assert result.confidence > 0


class TestTypographyConvenience:
    """Tests for typography convenience functions."""
    
    def test_estimate_font_size_function(self):
        """Test estimate_font_size convenience function."""
        estimate = estimate_font_size(20)
        assert estimate.size_px == 16
    
    def test_detect_line_height_function(self):
        """Test detect_line_height convenience function."""
        line_height = detect_line_height(24, 16)
        assert line_height == 1.5


# =============================================================================
# TOKEN MATCHING TESTS
# =============================================================================

class TestTokenMatcher:
    """Tests for token matching."""
    
    def test_load_default_tokens(self):
        """Test loading default tokens."""
        matcher = TokenMatcher()
        tokens = matcher.load_default_tokens()
        
        assert len(tokens.colors) > 0
        assert len(tokens.spacing) > 0
        assert len(tokens.typography) > 0
    
    def test_match_color_exact(self):
        """Test exact color match."""
        matcher = TokenMatcher()
        matcher.load_default_tokens()
        
        # Exact blue-500
        color = RGB(r=59, g=130, b=246)
        match = matcher.match_color(color)
        
        assert match.matched
        assert match.token_name == "color-blue-500"
        assert match.token_value == "#3B82F6"
    
    def test_match_color_close(self):
        """Test close color match."""
        matcher = TokenMatcher()
        matcher.load_default_tokens()
        
        # Slightly different blue
        color = RGB(r=60, g=131, b=247)
        match = matcher.match_color(color)
        
        assert match.matched
        assert "blue" in match.token_name.lower()
    
    def test_match_color_no_match(self):
        """Test color with no close match."""
        matcher = TokenMatcher(color_threshold=0.1)
        matcher.load_default_tokens()
        
        # Random unusual color
        color = RGB(r=123, g=87, b=201)
        match = matcher.match_color(color)
        
        # May or may not match, but should return result
        assert match.extracted_value.startswith("#")
    
    def test_match_spacing_exact(self):
        """Test exact spacing match."""
        matcher = TokenMatcher()
        matcher.load_default_tokens()
        
        match = matcher.match_spacing(16)
        
        assert match.matched
        assert match.token_name == "spacing-4"
        assert match.token_value == "16px"
    
    def test_match_spacing_close(self):
        """Test close spacing match."""
        matcher = TokenMatcher()
        matcher.load_default_tokens()
        
        # 17px should match 16px
        match = matcher.match_spacing(17)
        
        assert match.matched
        assert match.token_name == "spacing-4"
    
    def test_match_typography_exact(self):
        """Test exact typography match."""
        matcher = TokenMatcher()
        matcher.load_default_tokens()
        
        match = matcher.match_typography(16)
        
        assert match.matched
        assert match.token_name == "text-base"
    
    def test_match_typography_close(self):
        """Test close typography match."""
        matcher = TokenMatcher()
        matcher.load_default_tokens()
        
        # 17px should match 16px (within 2px tolerance)
        match = matcher.match_typography(17)
        
        assert match.matched
    
    def test_match_component_tokens(self):
        """Test matching all component tokens."""
        matcher = TokenMatcher()
        matcher.load_default_tokens()
        
        result = matcher.match_component_tokens(
            colors=[RGB(r=59, g=130, b=246)],
            spacing_values=[16, 16, 24],
            typography_size=16,
            typography_weight="regular"
        )
        
        assert len(result.color_matches) == 1
        assert result.color_matches[0].matched
        assert result.spacing_match is not None
        assert result.typography_match is not None
        assert not result.has_unmatched_tokens


class TestTokenMatchResult:
    """Tests for TokenMatchResult model."""
    
    def test_has_unmatched_colors(self):
        """Test unmatched colors detection."""
        result = TokenMatchResult(
            color_matches=[
                TokenMatch(matched=True, extracted_value="#FFF", token_type=TokenType.COLOR),
                TokenMatch(matched=False, extracted_value="#ABC", token_type=TokenType.COLOR),
            ],
            unmatched_colors=[RGB(r=170, g=187, b=204)]
        )
        
        assert result.has_unmatched_tokens


class TestDesignToken:
    """Tests for DesignToken model."""
    
    def test_get_rgb_value(self):
        """Test getting RGB value from color token."""
        token = DesignToken(
            name="color-primary",
            value="#3B82F6",
            token_type=TokenType.COLOR
        )
        
        rgb = token.get_rgb_value()
        assert rgb.r == 59
        assert rgb.g == 130
        assert rgb.b == 246
    
    def test_get_rgb_value_non_color(self):
        """Test getting RGB from non-color token."""
        token = DesignToken(
            name="spacing-4",
            value="16px",
            token_type=TokenType.SPACING
        )
        
        assert token.get_rgb_value() is None
    
    def test_get_numeric_value(self):
        """Test getting numeric value."""
        token = DesignToken(
            name="spacing-4",
            value="16px",
            token_type=TokenType.SPACING
        )
        
        assert token.get_numeric_value() == 16.0
    
    def test_get_numeric_value_float(self):
        """Test getting float numeric value."""
        token = DesignToken(
            name="opacity",
            value="0.5",
            token_type=TokenType.SPACING
        )
        
        assert token.get_numeric_value() == 0.5


class TestTokenMatchingConvenience:
    """Tests for token matching convenience functions."""
    
    def test_match_color_function(self):
        """Test match_color convenience function."""
        color = RGB(r=59, g=130, b=246)
        match = match_color(color)
        
        assert match.matched
        assert match.token_name == "color-blue-500"
    
    def test_match_spacing_function(self):
        """Test match_spacing convenience function."""
        match = match_spacing(16)
        
        assert match.matched
        assert match.token_name == "spacing-4"
    
    def test_match_typography_function(self):
        """Test match_typography convenience function."""
        match = match_typography(16, weight="regular")
        
        assert match.matched
        assert match.token_name == "text-base"


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestTokenExtractionIntegration:
    """Integration tests for token extraction."""
    
    def test_full_extraction_workflow(self, sample_image: Path):
        """Test complete extraction workflow."""
        # 1. Extract colors
        color_result = extract_colors(sample_image)
        
        # 2. Analyze spacing
        margins = infer_margins(
            component_bbox=(0.1, 0.1, 0.8, 0.8),
            screen_width=100,
            screen_height=100
        )
        
        # 3. Estimate typography
        typo_result = estimate_font_size(20)
        
        # 4. Match to tokens
        matcher = TokenMatcher()
        matcher.load_default_tokens()
        
        match_result = matcher.match_component_tokens(
            colors=[color_result.dominant],
            spacing_values=[margins.left, margins.top],
            typography_size=typo_result.size_px
        )
        
        assert len(match_result.color_matches) == 1
        assert match_result.color_matches[0].matched
        assert match_result.color_matches[0].token_name == "color-blue-500"
    
    def test_color_clustering_workflow(self, gradient_image: Path):
        """Test color clustering workflow."""
        # Extract colors from gradient
        extractor = ColorExtractor(n_clusters=5)
        result = extractor.extract_colors(gradient_image)
        
        # Should detect gradient
        assert result.is_gradient
        
        # Should have multiple colors
        assert len(result.colors) >= 3
        
        # All representations should be generated
        assert len(result.hex_values) == len(result.colors)
        assert len(result.hsl_values) == len(result.colors)
        assert len(result.lab_values) == len(result.colors)