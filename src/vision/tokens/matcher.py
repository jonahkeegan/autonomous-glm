"""
Token matching utilities for design system comparison.

Provides matching of extracted colors, spacing, and typography to design tokens.
"""

from pathlib import Path
from typing import Optional, Union

from .models import (
    RGB,
    DesignToken,
    DesignSystemTokens,
    TokenType,
    TokenMatch,
    TokenMatchResult,
)


# Default thresholds for matching
DEFAULT_COLOR_DISTANCE_THRESHOLD = 10.0  # LAB distance
DEFAULT_SPACING_TOLERANCE = 4  # pixels
DEFAULT_TYPOGRAPHY_SIZE_TOLERANCE = 2  # pixels


class TokenMatcher:
    """Match extracted values to design system tokens."""
    
    def __init__(
        self,
        color_threshold: float = DEFAULT_COLOR_DISTANCE_THRESHOLD,
        spacing_tolerance: int = DEFAULT_SPACING_TOLERANCE,
        typography_size_tolerance: int = DEFAULT_TYPOGRAPHY_SIZE_TOLERANCE,
    ):
        """Initialize the token matcher.
        
        Args:
            color_threshold: Maximum LAB distance for color match
            spacing_tolerance: Maximum pixel difference for spacing match
            typography_size_tolerance: Maximum pixel difference for typography
        """
        self.color_threshold = color_threshold
        self.spacing_tolerance = spacing_tolerance
        self.typography_size_tolerance = typography_size_tolerance
        self._design_tokens: Optional[DesignSystemTokens] = None
    
    def load_design_tokens(self, tokens: DesignSystemTokens) -> None:
        """Load design system tokens for matching.
        
        Args:
            tokens: DesignSystemTokens object
        """
        self._design_tokens = tokens
    
    def load_default_tokens(self) -> DesignSystemTokens:
        """Load default token set (built-in Tailwind-inspired tokens).
        
        Returns:
            DesignSystemTokens with default values
        """
        # Default color tokens (Tailwind-inspired)
        colors = [
            # Slate
            DesignToken(name="color-slate-50", value="#F8FAFC", token_type=TokenType.COLOR),
            DesignToken(name="color-slate-100", value="#F1F5F9", token_type=TokenType.COLOR),
            DesignToken(name="color-slate-200", value="#E2E8F0", token_type=TokenType.COLOR),
            DesignToken(name="color-slate-300", value="#CBD5E1", token_type=TokenType.COLOR),
            DesignToken(name="color-slate-400", value="#94A3B8", token_type=TokenType.COLOR),
            DesignToken(name="color-slate-500", value="#64748B", token_type=TokenType.COLOR),
            DesignToken(name="color-slate-600", value="#475569", token_type=TokenType.COLOR),
            DesignToken(name="color-slate-700", value="#334155", token_type=TokenType.COLOR),
            DesignToken(name="color-slate-800", value="#1E293B", token_type=TokenType.COLOR),
            DesignToken(name="color-slate-900", value="#0F172A", token_type=TokenType.COLOR),
            # Blue
            DesignToken(name="color-blue-50", value="#EFF6FF", token_type=TokenType.COLOR),
            DesignToken(name="color-blue-100", value="#DBEAFE", token_type=TokenType.COLOR),
            DesignToken(name="color-blue-200", value="#BFDBFE", token_type=TokenType.COLOR),
            DesignToken(name="color-blue-300", value="#93C5FD", token_type=TokenType.COLOR),
            DesignToken(name="color-blue-400", value="#60A5FA", token_type=TokenType.COLOR),
            DesignToken(name="color-blue-500", value="#3B82F6", token_type=TokenType.COLOR),
            DesignToken(name="color-blue-600", value="#2563EB", token_type=TokenType.COLOR),
            DesignToken(name="color-blue-700", value="#1D4ED8", token_type=TokenType.COLOR),
            DesignToken(name="color-blue-800", value="#1E40AF", token_type=TokenType.COLOR),
            DesignToken(name="color-blue-900", value="#1E3A8A", token_type=TokenType.COLOR),
            # Green
            DesignToken(name="color-green-50", value="#F0FDF4", token_type=TokenType.COLOR),
            DesignToken(name="color-green-100", value="#DCFCE7", token_type=TokenType.COLOR),
            DesignToken(name="color-green-500", value="#22C55E", token_type=TokenType.COLOR),
            DesignToken(name="color-green-600", value="#16A34A", token_type=TokenType.COLOR),
            # Red
            DesignToken(name="color-red-50", value="#FEF2F2", token_type=TokenType.COLOR),
            DesignToken(name="color-red-100", value="#FEE2E2", token_type=TokenType.COLOR),
            DesignToken(name="color-red-500", value="#EF4444", token_type=TokenType.COLOR),
            DesignToken(name="color-red-600", value="#DC2626", token_type=TokenType.COLOR),
            # Yellow
            DesignToken(name="color-yellow-50", value="#FEFCE8", token_type=TokenType.COLOR),
            DesignToken(name="color-yellow-100", value="#FEF9C3", token_type=TokenType.COLOR),
            DesignToken(name="color-yellow-500", value="#EAB308", token_type=TokenType.COLOR),
            # White/Black
            DesignToken(name="color-white", value="#FFFFFF", token_type=TokenType.COLOR),
            DesignToken(name="color-black", value="#000000", token_type=TokenType.COLOR),
        ]
        
        # Spacing tokens
        spacing = [
            DesignToken(name="spacing-0", value="0px", token_type=TokenType.SPACING),
            DesignToken(name="spacing-1", value="4px", token_type=TokenType.SPACING),
            DesignToken(name="spacing-2", value="8px", token_type=TokenType.SPACING),
            DesignToken(name="spacing-3", value="12px", token_type=TokenType.SPACING),
            DesignToken(name="spacing-4", value="16px", token_type=TokenType.SPACING),
            DesignToken(name="spacing-5", value="20px", token_type=TokenType.SPACING),
            DesignToken(name="spacing-6", value="24px", token_type=TokenType.SPACING),
            DesignToken(name="spacing-8", value="32px", token_type=TokenType.SPACING),
            DesignToken(name="spacing-10", value="40px", token_type=TokenType.SPACING),
            DesignToken(name="spacing-12", value="48px", token_type=TokenType.SPACING),
            DesignToken(name="spacing-16", value="64px", token_type=TokenType.SPACING),
            DesignToken(name="spacing-20", value="80px", token_type=TokenType.SPACING),
            DesignToken(name="spacing-24", value="96px", token_type=TokenType.SPACING),
        ]
        
        # Typography tokens
        typography = [
            DesignToken(name="text-xs", value="12px", token_type=TokenType.TYPOGRAPHY),
            DesignToken(name="text-sm", value="14px", token_type=TokenType.TYPOGRAPHY),
            DesignToken(name="text-base", value="16px", token_type=TokenType.TYPOGRAPHY),
            DesignToken(name="text-lg", value="18px", token_type=TokenType.TYPOGRAPHY),
            DesignToken(name="text-xl", value="20px", token_type=TokenType.TYPOGRAPHY),
            DesignToken(name="text-2xl", value="24px", token_type=TokenType.TYPOGRAPHY),
            DesignToken(name="text-3xl", value="30px", token_type=TokenType.TYPOGRAPHY),
            DesignToken(name="text-4xl", value="36px", token_type=TokenType.TYPOGRAPHY),
            DesignToken(name="text-5xl", value="48px", token_type=TokenType.TYPOGRAPHY),
        ]
        
        tokens = DesignSystemTokens(
            colors=colors,
            spacing=spacing,
            typography=typography,
            borders=[],
            shadows=[],
        )
        
        self._design_tokens = tokens
        return tokens
    
    def match_color(
        self,
        color: RGB,
        tokens: Optional[list[DesignToken]] = None
    ) -> TokenMatch:
        """Find the closest matching color token.
        
        Args:
            color: RGB color to match
            tokens: Optional list of tokens (uses loaded tokens if not provided)
        
        Returns:
            TokenMatch with match result
        """
        # Get tokens to search
        search_tokens = tokens or (self._design_tokens.colors if self._design_tokens else [])
        
        if not search_tokens:
            return TokenMatch(
                matched=False,
                extracted_value=color.to_hex().value,
                token_type=TokenType.COLOR
            )
        
        best_match = None
        best_distance = float('inf')
        
        for token in search_tokens:
            if token.token_type != TokenType.COLOR:
                continue
            
            token_rgb = token.get_rgb_value()
            if token_rgb is None:
                continue
            
            # Calculate LAB distance
            distance = color.lab_distance_to(token_rgb)
            
            if distance < best_distance:
                best_distance = distance
                best_match = token
        
        if best_match is None:
            return TokenMatch(
                matched=False,
                extracted_value=color.to_hex().value,
                token_type=TokenType.COLOR
            )
        
        # Calculate confidence (inverse of normalized distance)
        confidence = max(0.0, 1.0 - (best_distance / 100.0))
        matched = best_distance <= self.color_threshold
        
        return TokenMatch(
            matched=matched,
            token_name=best_match.name,
            token_value=best_match.value,
            extracted_value=color.to_hex().value,
            distance=round(best_distance, 2),
            confidence=round(confidence, 2),
            token_type=TokenType.COLOR
        )
    
    def match_spacing(
        self,
        value: float,
        tokens: Optional[list[DesignToken]] = None
    ) -> TokenMatch:
        """Find the closest matching spacing token.
        
        Args:
            value: Spacing value in pixels
            tokens: Optional list of tokens (uses loaded tokens if not provided)
        
        Returns:
            TokenMatch with match result
        """
        # Get tokens to search
        search_tokens = tokens or (self._design_tokens.spacing if self._design_tokens else [])
        
        if not search_tokens:
            return TokenMatch(
                matched=False,
                extracted_value=f"{value}px",
                token_type=TokenType.SPACING
            )
        
        best_match = None
        best_distance = float('inf')
        
        for token in search_tokens:
            if token.token_type != TokenType.SPACING:
                continue
            
            token_value = token.get_numeric_value()
            if token_value is None:
                continue
            
            distance = abs(value - token_value)
            
            if distance < best_distance:
                best_distance = distance
                best_match = token
        
        if best_match is None:
            return TokenMatch(
                matched=False,
                extracted_value=f"{value}px",
                token_type=TokenType.SPACING
            )
        
        # Calculate confidence
        confidence = max(0.0, 1.0 - (best_distance / 50.0))
        matched = best_distance <= self.spacing_tolerance
        
        return TokenMatch(
            matched=matched,
            token_name=best_match.name,
            token_value=best_match.value,
            extracted_value=f"{value}px",
            distance=round(best_distance, 2),
            confidence=round(confidence, 2),
            token_type=TokenType.SPACING
        )
    
    def match_typography(
        self,
        size: int,
        weight: Optional[str] = None,
        tokens: Optional[list[DesignToken]] = None
    ) -> TokenMatch:
        """Find the closest matching typography token.
        
        Args:
            size: Font size in pixels
            weight: Optional font weight string
            tokens: Optional list of tokens (uses loaded tokens if not provided)
        
        Returns:
            TokenMatch with match result
        """
        # Get tokens to search
        search_tokens = tokens or (self._design_tokens.typography if self._design_tokens else [])
        
        if not search_tokens:
            return TokenMatch(
                matched=False,
                extracted_value=f"{size}px",
                token_type=TokenType.TYPOGRAPHY
            )
        
        best_match = None
        best_distance = float('inf')
        
        for token in search_tokens:
            if token.token_type != TokenType.TYPOGRAPHY:
                continue
            
            token_value = token.get_numeric_value()
            if token_value is None:
                continue
            
            distance = abs(size - token_value)
            
            if distance < best_distance:
                best_distance = distance
                best_match = token
        
        if best_match is None:
            return TokenMatch(
                matched=False,
                extracted_value=f"{size}px",
                token_type=TokenType.TYPOGRAPHY
            )
        
        # Calculate confidence
        confidence = max(0.0, 1.0 - (best_distance / 20.0))
        matched = best_distance <= self.typography_size_tolerance
        
        # Include weight in extracted value if provided
        extracted = f"{size}px"
        if weight:
            extracted = f"{size}px/{weight}"
        
        return TokenMatch(
            matched=matched,
            token_name=best_match.name,
            token_value=best_match.value,
            extracted_value=extracted,
            distance=round(best_distance, 2),
            confidence=round(confidence, 2),
            token_type=TokenType.TYPOGRAPHY
        )
    
    def calculate_token_distance(
        self,
        value: Union[RGB, float, int],
        token: DesignToken
    ) -> float:
        """Calculate distance between a value and a token.
        
        Args:
            value: Value to compare (RGB for colors, number for spacing/typography)
            token: Design token to compare against
        
        Returns:
            Distance metric (lower = closer match)
        """
        if token.token_type == TokenType.COLOR:
            if isinstance(value, RGB):
                token_rgb = token.get_rgb_value()
                if token_rgb:
                    return value.lab_distance_to(token_rgb)
            return float('inf')
        
        elif token.token_type in (TokenType.SPACING, TokenType.TYPOGRAPHY):
            if isinstance(value, (int, float)):
                token_value = token.get_numeric_value()
                if token_value is not None:
                    return abs(value - token_value)
            return float('inf')
        
        return float('inf')
    
    def match_component_tokens(
        self,
        colors: list[RGB],
        spacing_values: list[float],
        typography_size: Optional[int] = None,
        typography_weight: Optional[str] = None,
    ) -> TokenMatchResult:
        """Match all tokens for a component.
        
        Args:
            colors: List of extracted colors
            spacing_values: List of spacing values in pixels
            typography_size: Optional font size in pixels
            typography_weight: Optional font weight string
        
        Returns:
            TokenMatchResult with all matches
        """
        # Ensure we have tokens loaded
        if self._design_tokens is None:
            self.load_default_tokens()
        
        # Match colors
        color_matches = []
        unmatched_colors = []
        
        for color in colors:
            match = self.match_color(color)
            color_matches.append(match)
            if not match.matched:
                unmatched_colors.append(color)
        
        # Match spacing (use most common value)
        spacing_match = None
        if spacing_values:
            avg_spacing = sum(spacing_values) / len(spacing_values)
            spacing_match = self.match_spacing(avg_spacing)
        
        # Match typography
        typography_match = None
        if typography_size:
            typography_match = self.match_typography(typography_size, typography_weight)
        
        return TokenMatchResult(
            color_matches=color_matches,
            spacing_match=spacing_match,
            typography_match=typography_match,
            unmatched_colors=unmatched_colors,
            has_unmatched_tokens=len(unmatched_colors) > 0 or 
                                 (spacing_match and not spacing_match.matched) or
                                 (typography_match and not typography_match.matched)
        )


def match_color(
    color: RGB,
    tokens: Optional[list[DesignToken]] = None
) -> TokenMatch:
    """Convenience function to match a color.
    
    Args:
        color: RGB color to match
        tokens: Optional list of tokens
    
    Returns:
        TokenMatch with match result
    """
    matcher = TokenMatcher()
    matcher.load_default_tokens()
    return matcher.match_color(color, tokens)


def match_spacing(
    value: float,
    tokens: Optional[list[DesignToken]] = None
) -> TokenMatch:
    """Convenience function to match spacing.
    
    Args:
        value: Spacing value in pixels
        tokens: Optional list of tokens
    
    Returns:
        TokenMatch with match result
    """
    matcher = TokenMatcher()
    matcher.load_default_tokens()
    return matcher.match_spacing(value, tokens)


def match_typography(
    size: int,
    weight: Optional[str] = None,
    tokens: Optional[list[DesignToken]] = None
) -> TokenMatch:
    """Convenience function to match typography.
    
    Args:
        size: Font size in pixels
        weight: Optional font weight string
        tokens: Optional list of tokens
    
    Returns:
        TokenMatch with match result
    """
    matcher = TokenMatcher()
    matcher.load_default_tokens()
    return matcher.match_typography(size, weight, tokens)