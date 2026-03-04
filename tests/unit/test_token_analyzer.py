"""
Unit tests for token analyzer module.
"""

import pytest

from src.plan.token_analyzer import (
    TokenAnalyzer,
    DEFAULT_DESIGN_TOKENS,
    generate_color_token_name,
    generate_spacing_token_name,
    generate_typography_token_name,
    analyze_all_token_patterns,
)
from src.plan.proposal_models import TokenType


class TestDefaultDesignTokens:
    """Tests for default design tokens."""
    
    def test_default_tokens_exist(self):
        """Test default tokens are defined."""
        assert DEFAULT_DESIGN_TOKENS is not None
        assert "color" in DEFAULT_DESIGN_TOKENS
        assert "spacing" in DEFAULT_DESIGN_TOKENS
        assert "typography" in DEFAULT_DESIGN_TOKENS
    
    def test_color_tokens_exist(self):
        """Test color tokens are defined."""
        colors = DEFAULT_DESIGN_TOKENS["color"]
        assert "--color-primary" in colors
        assert "--color-background" in colors
        assert "--color-text-primary" in colors
    
    def test_spacing_tokens_exist(self):
        """Test spacing tokens are defined."""
        spacing = DEFAULT_DESIGN_TOKENS["spacing"]
        assert "--space-1" in spacing
        assert "--space-4" in spacing
        assert "--space-8" in spacing


class TestGenerateColorTokenName:
    """Tests for color token name generation."""
    
    def test_generate_color_token_name_default(self):
        """Test generating color token name with default semantic."""
        name = generate_color_token_name("#FF6B6B")
        
        assert name.startswith("--color-custom-")
        assert name.endswith("6b")  # Last 2 chars of hex
    
    def test_generate_color_token_name_with_semantic(self):
        """Test generating color token name with semantic."""
        name = generate_color_token_name("#FF6B6B", semantic="accent")
        
        assert name == "--color-accent-6b"
    
    def test_generate_color_token_name_without_hash(self):
        """Test generating color token name without hash prefix."""
        name = generate_color_token_name("FF6B6B")
        
        assert name == "--color-custom-6b"


class TestGenerateSpacingTokenName:
    """Tests for spacing token name generation."""
    
    def test_generate_spacing_small(self):
        """Test generating spacing token for small values."""
        assert generate_spacing_token_name(4) == "--spacing-sm"
        assert generate_spacing_token_name(8) == "--spacing-md"
    
    def test_generate_spacing_large(self):
        """Test generating spacing token for larger values."""
        assert generate_spacing_token_name(20) == "--spacing-20"
        assert generate_spacing_token_name(100) == "--spacing-100"


class TestGenerateTypographyTokenName:
    """Tests for typography token name generation."""
    
    def test_generate_font_size_name(self):
        """Test generating font size token name."""
        assert generate_typography_token_name("size", "14px") == "--font-size-sm"
        assert generate_typography_token_name("size", "16px") == "--font-size-base"
        assert generate_typography_token_name("size", "24px") == "--font-size-2xl"
    
    def test_generate_font_weight_name(self):
        """Test generating font weight token name."""
        assert generate_typography_token_name("weight", "400") == "--font-weight-normal"
        assert generate_typography_token_name("weight", "500") == "--font-weight-medium"
        assert generate_typography_token_name("weight", "700") == "--font-weight-bold"


class TestTokenAnalyzer:
    """Tests for TokenAnalyzer class."""
    
    def test_create_analyzer_default(self):
        """Test creating analyzer with defaults."""
        analyzer = TokenAnalyzer()
        
        assert analyzer.design_tokens == DEFAULT_DESIGN_TOKENS
        assert analyzer.usage_threshold == 3
    
    def test_create_analyzer_custom(self):
        """Test creating analyzer with custom settings."""
        custom_tokens = {"color": {"--color-test": "#000000"}}
        analyzer = TokenAnalyzer(
            design_tokens=custom_tokens,
            usage_threshold=5,
        )
        
        assert analyzer.design_tokens == custom_tokens
        assert analyzer.usage_threshold == 5
    
    def test_get_existing_tokens(self):
        """Test getting existing tokens by type."""
        analyzer = TokenAnalyzer()
        
        colors = analyzer.get_existing_tokens(TokenType.COLOR)
        
        assert "--color-primary" in colors
        assert colors["--color-primary"] == "#3B82F6"
    
    def test_is_existing_token_true(self):
        """Test checking if token exists (true case)."""
        analyzer = TokenAnalyzer()
        
        assert analyzer.is_existing_token("--color-primary") is True
        assert analyzer.is_existing_token("--space-4") is True
    
    def test_is_existing_token_false(self):
        """Test checking if token exists (false case)."""
        analyzer = TokenAnalyzer()
        
        assert analyzer.is_existing_token("--color-nonexistent") is False
    
    def test_detect_missing_tokens(self):
        """Test detecting missing tokens."""
        analyzer = TokenAnalyzer()
        
        detected = [
            {"value": "#3B82F6"},  # Existing
            {"value": "#FF6B6B"},  # Missing
            {"value": "#10B981"},  # Existing
        ]
        
        missing = analyzer.detect_missing_tokens(detected, TokenType.COLOR)
        
        assert "#FF6B6B" in missing
        assert "#3B82F6" not in missing
        assert "#10B981" not in missing
    
    def test_calculate_usage_frequency(self):
        """Test calculating usage frequency."""
        analyzer = TokenAnalyzer()
        
        values = ["#FF6B6B", "#FF6B6B", "#FF6B6B", "#10B981"]
        freq = analyzer.calculate_usage_frequency(values)
        
        assert freq["#FF6B6B"] == 3
        assert freq["#10B981"] == 1


class TestAnalyzeColorPatterns:
    """Tests for color pattern analysis."""
    
    def test_analyze_color_patterns_below_threshold(self):
        """Test colors below threshold are not proposed."""
        analyzer = TokenAnalyzer(usage_threshold=3)
        
        findings = [
            {"metadata": {"color": "#FF6B6B"}, "entity_id": "screen-1"},
            {"metadata": {"color": "#FF6B6B"}, "entity_id": "screen-2"},
        ]
        
        proposals = analyzer.analyze_color_patterns(findings)
        
        assert len(proposals) == 0  # Only 2 occurrences, below threshold
    
    def test_analyze_color_patterns_above_threshold(self):
        """Test colors above threshold are proposed."""
        analyzer = TokenAnalyzer(usage_threshold=3)
        
        findings = [
            {"metadata": {"color": "#FF6B6B"}, "entity_id": "screen-1"},
            {"metadata": {"color": "#FF6B6B"}, "entity_id": "screen-2"},
            {"metadata": {"color": "#FF6B6B"}, "entity_id": "screen-3"},
        ]
        
        proposals = analyzer.analyze_color_patterns(findings)
        
        assert len(proposals) == 1
        assert proposals[0].proposed_value == "#FF6B6B"
        assert proposals[0].usage_count == 3
    
    def test_analyze_color_patterns_with_detected(self):
        """Test color analysis with detected colors."""
        analyzer = TokenAnalyzer(usage_threshold=2)
        
        detected = [
            {"value": "#ABCDEF", "screen_id": "screen-1"},
            {"value": "#ABCDEF", "screen_id": "screen-2"},
        ]
        
        proposals = analyzer.analyze_color_patterns([], detected)
        
        assert len(proposals) == 1
        assert proposals[0].proposed_value == "#ABCDEF"


class TestAnalyzeSpacingPatterns:
    """Tests for spacing pattern analysis."""
    
    def test_analyze_spacing_patterns_above_threshold(self):
        """Test spacing above threshold is proposed."""
        analyzer = TokenAnalyzer(usage_threshold=3)
        
        findings = [
            {"metadata": {"spacing": "28px"}, "entity_id": "screen-1"},
            {"metadata": {"spacing": "28px"}, "entity_id": "screen-2"},
            {"metadata": {"spacing": "28px"}, "entity_id": "screen-3"},
        ]
        
        proposals = analyzer.analyze_spacing_patterns(findings)
        
        assert len(proposals) == 1
        assert proposals[0].proposed_value == "28px"
        assert proposals[0].token_type == TokenType.SPACING


class TestAnalyzeTypographyPatterns:
    """Tests for typography pattern analysis."""
    
    def test_analyze_typography_patterns_size(self):
        """Test typography size pattern analysis."""
        analyzer = TokenAnalyzer(usage_threshold=3)
        
        findings = [
            {"metadata": {"font_size": "22px"}, "entity_id": "screen-1"},
            {"metadata": {"font_size": "22px"}, "entity_id": "screen-2"},
            {"metadata": {"font_size": "22px"}, "entity_id": "screen-3"},
        ]
        
        proposals = analyzer.analyze_typography_patterns(findings)
        
        assert len(proposals) == 1
        assert proposals[0].proposed_value == "22px"
        assert proposals[0].token_type == TokenType.TYPOGRAPHY
    
    def test_analyze_typography_patterns_weight(self):
        """Test typography weight pattern analysis."""
        analyzer = TokenAnalyzer(usage_threshold=3)
        
        findings = [
            {"metadata": {"font_weight": "300"}, "entity_id": "screen-1"},
            {"metadata": {"font_weight": "300"}, "entity_id": "screen-2"},
            {"metadata": {"font_weight": "300"}, "entity_id": "screen-3"},
        ]
        
        proposals = analyzer.analyze_typography_patterns(findings)
        
        assert len(proposals) == 1
        assert proposals[0].proposed_value == "300"


class TestAnalyzeAllTokenPatterns:
    """Tests for analyze_all_token_patterns convenience function."""
    
    def test_analyze_all_empty(self):
        """Test analyzing empty findings."""
        proposals = analyze_all_token_patterns([])
        
        assert proposals == []
    
    def test_analyze_all_mixed(self):
        """Test analyzing mixed findings."""
        findings = [
            {"dimension": "color", "metadata": {"color": "#ABCDEF"}, "entity_id": "s1"},
            {"dimension": "color", "metadata": {"color": "#ABCDEF"}, "entity_id": "s2"},
            {"dimension": "color", "metadata": {"color": "#ABCDEF"}, "entity_id": "s3"},
            {"dimension": "spacing_rhythm", "metadata": {"spacing": "28px"}, "entity_id": "s4"},
            {"dimension": "spacing_rhythm", "metadata": {"spacing": "28px"}, "entity_id": "s5"},
            {"dimension": "spacing_rhythm", "metadata": {"spacing": "28px"}, "entity_id": "s6"},
        ]
        
        proposals = analyze_all_token_patterns(findings)
        
        # Should have 2 proposals (1 color, 1 spacing)
        assert len(proposals) == 2
        
        token_types = {p.token_type for p in proposals}
        assert TokenType.COLOR in token_types
        assert TokenType.SPACING in token_types


class TestFindSimilarColorToken:
    """Tests for finding similar color tokens."""
    
    def test_find_similar_exact_match(self):
        """Test finding similar color with exact match."""
        analyzer = TokenAnalyzer()
        
        # Using exact value from default tokens
        similar = analyzer._find_similar_color_token("#3B82F6")
        
        assert similar == "--color-primary"
    
    def test_find_similar_no_match(self):
        """Test finding similar color with no match."""
        analyzer = TokenAnalyzer()
        
        similar = analyzer._find_similar_color_token("#ABCDEF")
        
        assert similar is None