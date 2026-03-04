"""
Token pattern analysis for design system proposals.

Analyzes audit findings to detect patterns in colors, spacing, and typography
that could be promoted to design system tokens.
"""

import re
from collections import Counter
from typing import Any, Optional

from src.plan.proposal_models import (
    TokenProposal,
    TokenType,
)


# =============================================================================
# DEFAULT DESIGN TOKENS (Tailwind-style)
# =============================================================================

DEFAULT_DESIGN_TOKENS: dict[str, dict[str, str]] = {
    "color": {
        "--color-primary": "#3B82F6",
        "--color-primary-hover": "#2563EB",
        "--color-primary-active": "#1D4ED8",
        "--color-background": "#FFFFFF",
        "--color-surface": "#F9FAFB",
        "--color-text-primary": "#111827",
        "--color-text-secondary": "#6B7280",
        "--color-border": "#E5E7EB",
        "--color-success": "#10B981",
        "--color-warning": "#F59E0B",
        "--color-error": "#EF4444",
        "--color-info": "#3B82F6",
    },
    "spacing": {
        "--space-1": "4px",
        "--space-2": "8px",
        "--space-3": "12px",
        "--space-4": "16px",
        "--space-5": "20px",
        "--space-6": "24px",
        "--space-8": "32px",
        "--space-10": "40px",
        "--space-12": "48px",
        "--space-16": "64px",
    },
    "typography": {
        "--text-xs": "12px",
        "--text-sm": "14px",
        "--text-base": "16px",
        "--text-lg": "18px",
        "--text-xl": "20px",
        "--text-2xl": "24px",
        "--text-3xl": "30px",
        "--text-4xl": "36px",
        "--font-normal": "400",
        "--font-medium": "500",
        "--font-semibold": "600",
        "--font-bold": "700",
    },
    "radius": {
        "--radius-sm": "4px",
        "--radius-md": "8px",
        "--radius-lg": "12px",
        "--radius-xl": "16px",
        "--radius-full": "9999px",
    },
}


# =============================================================================
# TOKEN NAMING CONVENTIONS
# =============================================================================

def generate_color_token_name(hex_value: str, semantic: str = "custom") -> str:
    """Generate a semantic token name for a color.
    
    Args:
        hex_value: Hex color value (e.g., "#FF6B6B")
        semantic: Semantic category (e.g., "accent", "warning", "custom")
    
    Returns:
        Token name like "--color-custom-a3"
    """
    # Extract last 2 chars of hex for uniqueness
    short_hex = hex_value.lstrip("#")[-2:].lower()
    return f"--color-{semantic}-{short_hex}"


def generate_spacing_token_name(value_px: int) -> str:
    """Generate a spacing token name.
    
    Args:
        value_px: Spacing value in pixels
    
    Returns:
        Token name like "--spacing-20" or "--spacing-xl"
    """
    # Map to t-shirt sizes for common values
    size_map = {
        2: "xs",
        4: "sm", 
        8: "md",
        12: "lg",
        16: "xl",
        24: "2xl",
        32: "3xl",
    }
    
    if value_px in size_map:
        return f"--spacing-{size_map[value_px]}"
    return f"--spacing-{value_px}"


def generate_typography_token_name(property_type: str, value: str) -> str:
    """Generate a typography token name.
    
    Args:
        property_type: "size" or "weight"
        value: The value (e.g., "14px", "500")
    
    Returns:
        Token name like "--font-size-sm" or "--font-weight-medium"
    """
    if property_type == "size":
        # Extract numeric value
        match = re.search(r"(\d+)", value)
        if match:
            px = int(match.group(1))
            size_map = {
                12: "xs",
                14: "sm",
                16: "base",
                18: "lg",
                20: "xl",
                24: "2xl",
                30: "3xl",
                36: "4xl",
            }
            if px in size_map:
                return f"--font-size-{size_map[px]}"
            return f"--font-size-{px}"
    elif property_type == "weight":
        weight_map = {
            "400": "normal",
            "500": "medium",
            "600": "semibold",
            "700": "bold",
        }
        if value in weight_map:
            return f"--font-weight-{weight_map[value]}"
        return f"--font-weight-{value}"
    
    return f"--font-{property_type}-{value}"


# =============================================================================
# TOKEN ANALYZER
# =============================================================================

class TokenAnalyzer:
    """Analyzes token patterns from audit findings and detected tokens."""
    
    def __init__(
        self,
        design_tokens: Optional[dict[str, dict[str, str]]] = None,
        usage_threshold: int = 3,
    ):
        """Initialize the token analyzer.
        
        Args:
            design_tokens: Existing design tokens (defaults to Tailwind-style)
            usage_threshold: Minimum occurrences to propose a new token
        """
        self.design_tokens = design_tokens or DEFAULT_DESIGN_TOKENS
        self.usage_threshold = usage_threshold
    
    def get_existing_tokens(self, token_type: TokenType) -> dict[str, str]:
        """Get existing tokens of a specific type.
        
        Args:
            token_type: Type of tokens to retrieve
        
        Returns:
            Dict mapping token names to values
        """
        return self.design_tokens.get(token_type.value, {})
    
    def is_existing_token(self, token_name: str) -> bool:
        """Check if a token name already exists.
        
        Args:
            token_name: Token name to check
        
        Returns:
            True if token exists in any category
        """
        for token_dict in self.design_tokens.values():
            if token_name in token_dict:
                return True
        return False
    
    def detect_missing_tokens(
        self,
        detected_values: list[dict[str, Any]],
        token_type: TokenType,
    ) -> list[str]:
        """Detect values that don't match existing tokens.
        
        Args:
            detected_values: List of detected value dicts with 'value' key
            token_type: Type of token to check
        
        Returns:
            List of values not matching existing tokens
        """
        existing = self.get_existing_tokens(token_type)
        existing_values = set(existing.values())
        
        missing = []
        for item in detected_values:
            value = item.get("value", "")
            if value and value not in existing_values:
                missing.append(value)
        
        return missing
    
    def calculate_usage_frequency(
        self,
        values: list[str],
    ) -> dict[str, int]:
        """Calculate frequency of each value.
        
        Args:
            values: List of values to count
        
        Returns:
            Dict mapping values to occurrence counts
        """
        return dict(Counter(values))
    
    def analyze_color_patterns(
        self,
        findings: list[dict[str, Any]],
        detected_colors: Optional[list[dict[str, Any]]] = None,
    ) -> list[TokenProposal]:
        """Analyze color patterns from findings and detected colors.
        
        Args:
            findings: Audit findings related to color
            detected_colors: List of detected colors with metadata
        
        Returns:
            List of token proposals for colors
        """
        proposals = []
        
        # Extract colors from findings
        color_values = []
        for finding in findings:
            metadata = finding.get("metadata", {})
            if metadata:
                # Look for color-related metadata
                if "color" in metadata:
                    color_values.append({
                        "value": metadata["color"],
                        "screen_id": finding.get("entity_id", ""),
                    })
                if "colors" in metadata:
                    for color in metadata["colors"]:
                        color_values.append({
                            "value": color,
                            "screen_id": finding.get("entity_id", ""),
                        })
        
        # Add detected colors if provided
        if detected_colors:
            color_values.extend(detected_colors)
        
        # Find missing tokens
        missing = self.detect_missing_tokens(color_values, TokenType.COLOR)
        
        # Calculate frequencies
        frequencies = self.calculate_usage_frequency(missing)
        
        # Generate proposals for values meeting threshold
        existing_color_values = set(self.get_existing_tokens(TokenType.COLOR).values())
        
        for value, count in frequencies.items():
            if count >= self.usage_threshold and value not in existing_color_values:
                # Collect affected screens
                affected_screens = list(set(
                    item.get("screen_id", "") 
                    for item in color_values 
                    if item.get("value") == value
                ))
                
                # Check for similar existing token
                conflict = self._find_similar_color_token(value)
                
                proposals.append(TokenProposal(
                    token_name=generate_color_token_name(value),
                    token_type=TokenType.COLOR,
                    proposed_value=value,
                    rationale=f"Detected {count} instances of this color without a matching token",
                    usage_count=count,
                    affected_screens=[s for s in affected_screens if s],
                    existing_token_conflict=conflict,
                ))
        
        return proposals
    
    def analyze_spacing_patterns(
        self,
        findings: list[dict[str, Any]],
        detected_spacing: Optional[list[dict[str, Any]]] = None,
    ) -> list[TokenProposal]:
        """Analyze spacing patterns from findings and detected spacing.
        
        Args:
            findings: Audit findings related to spacing
            detected_spacing: List of detected spacing values with metadata
        
        Returns:
            List of token proposals for spacing
        """
        proposals = []
        
        # Extract spacing from findings
        spacing_values = []
        for finding in findings:
            metadata = finding.get("metadata", {})
            if metadata:
                # Look for spacing-related metadata
                for key in ["spacing", "margin", "padding", "gap"]:
                    if key in metadata:
                        spacing_values.append({
                            "value": metadata[key],
                            "screen_id": finding.get("entity_id", ""),
                        })
        
        # Add detected spacing if provided
        if detected_spacing:
            spacing_values.extend(detected_spacing)
        
        # Find missing tokens
        missing = self.detect_missing_tokens(spacing_values, TokenType.SPACING)
        
        # Calculate frequencies
        frequencies = self.calculate_usage_frequency(missing)
        
        # Generate proposals
        existing_spacing_values = set(self.get_existing_tokens(TokenType.SPACING).values())
        
        for value, count in frequencies.items():
            if count >= self.usage_threshold and value not in existing_spacing_values:
                affected_screens = list(set(
                    item.get("screen_id", "")
                    for item in spacing_values
                    if item.get("value") == value
                ))
                
                # Extract pixel value for naming
                match = re.search(r"(\d+)", value)
                px_value = int(match.group(1)) if match else 0
                
                proposals.append(TokenProposal(
                    token_name=generate_spacing_token_name(px_value),
                    token_type=TokenType.SPACING,
                    proposed_value=value,
                    rationale=f"Detected {count} instances of this spacing without a matching token",
                    usage_count=count,
                    affected_screens=[s for s in affected_screens if s],
                ))
        
        return proposals
    
    def analyze_typography_patterns(
        self,
        findings: list[dict[str, Any]],
        detected_typography: Optional[list[dict[str, Any]]] = None,
    ) -> list[TokenProposal]:
        """Analyze typography patterns from findings and detected typography.
        
        Args:
            findings: Audit findings related to typography
            detected_typography: List of detected typography values with metadata
        
        Returns:
            List of token proposals for typography
        """
        proposals = []
        
        # Extract typography from findings
        typography_values = []
        for finding in findings:
            metadata = finding.get("metadata", {})
            if metadata:
                # Look for typography-related metadata
                if "font_size" in metadata:
                    typography_values.append({
                        "value": metadata["font_size"],
                        "property": "size",
                        "screen_id": finding.get("entity_id", ""),
                    })
                if "font_weight" in metadata:
                    typography_values.append({
                        "value": metadata["font_weight"],
                        "property": "weight",
                        "screen_id": finding.get("entity_id", ""),
                    })
        
        # Add detected typography if provided
        if detected_typography:
            typography_values.extend(detected_typography)
        
        # Process sizes and weights separately
        for prop_type in ["size", "weight"]:
            prop_values = [v for v in typography_values if v.get("property") == prop_type]
            
            missing = self.detect_missing_tokens(prop_values, TokenType.TYPOGRAPHY)
            frequencies = self.calculate_usage_frequency(missing)
            
            existing_typo_values = set(self.get_existing_tokens(TokenType.TYPOGRAPHY).values())
            
            for value, count in frequencies.items():
                if count >= self.usage_threshold and value not in existing_typo_values:
                    affected_screens = list(set(
                        item.get("screen_id", "")
                        for item in prop_values
                        if item.get("value") == value
                    ))
                    
                    proposals.append(TokenProposal(
                        token_name=generate_typography_token_name(prop_type, value),
                        token_type=TokenType.TYPOGRAPHY,
                        proposed_value=value,
                        rationale=f"Detected {count} instances of this font {prop_type} without a matching token",
                        usage_count=count,
                        affected_screens=[s for s in affected_screens if s],
                    ))
        
        return proposals
    
    def _find_similar_color_token(self, hex_value: str) -> Optional[str]:
        """Find an existing color token with similar value.
        
        Args:
            hex_value: Hex color to compare
        
        Returns:
            Token name if similar color exists, None otherwise
        """
        # Simple implementation: check for exact match or prefix match
        existing_colors = self.get_existing_tokens(TokenType.COLOR)
        
        hex_upper = hex_value.upper().lstrip("#")
        
        for token_name, token_value in existing_colors.items():
            token_hex = token_value.upper().lstrip("#")
            # Check if first 4 chars match (rough similarity)
            if hex_upper[:4] == token_hex[:4]:
                return token_name
        
        return None


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def analyze_all_token_patterns(
    findings: list[dict[str, Any]],
    detected_tokens: Optional[dict[str, list[dict[str, Any]]]] = None,
    design_tokens: Optional[dict[str, dict[str, str]]] = None,
    usage_threshold: int = 3,
) -> list[TokenProposal]:
    """Analyze all token patterns from findings.
    
    Args:
        findings: All audit findings
        detected_tokens: Detected tokens by type (color, spacing, typography)
        design_tokens: Existing design tokens
        usage_threshold: Minimum occurrences to propose a token
    
    Returns:
        Combined list of all token proposals
    """
    analyzer = TokenAnalyzer(
        design_tokens=design_tokens,
        usage_threshold=usage_threshold,
    )
    
    detected_tokens = detected_tokens or {}
    
    # Filter findings by dimension
    color_findings = [f for f in findings if f.get("dimension") == "color"]
    spacing_findings = [f for f in findings if f.get("dimension") == "spacing_rhythm"]
    typography_findings = [f for f in findings if f.get("dimension") == "typography"]
    
    proposals = []
    
    proposals.extend(analyzer.analyze_color_patterns(
        color_findings,
        detected_tokens.get("color"),
    ))
    
    proposals.extend(analyzer.analyze_spacing_patterns(
        spacing_findings,
        detected_tokens.get("spacing"),
    ))
    
    proposals.extend(analyzer.analyze_typography_patterns(
        typography_findings,
        detected_tokens.get("typography"),
    ))
    
    return proposals