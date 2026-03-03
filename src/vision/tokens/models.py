"""
Pydantic models for token extraction.

Defines models for colors, spacing, typography, and token matching results.
"""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator


# =============================================================================
# COLOR MODELS
# =============================================================================

class RGB(BaseModel):
    """RGB color representation."""
    r: int = Field(..., ge=0, le=255, description="Red channel (0-255)")
    g: int = Field(..., ge=0, le=255, description="Green channel (0-255)")
    b: int = Field(..., ge=0, le=255, description="Blue channel (0-255)")
    
    def to_hex(self) -> "HexColor":
        """Convert to hex color."""
        hex_str = f"#{self.r:02X}{self.g:02X}{self.b:02X}"
        return HexColor(value=hex_str)
    
    def to_hsl(self) -> "HSL":
        """Convert to HSL color."""
        r, g, b = self.r / 255.0, self.g / 255.0, self.b / 255.0
        
        max_c = max(r, g, b)
        min_c = min(r, g, b)
        l = (max_c + min_c) / 2
        
        if max_c == min_c:
            h = s = 0.0
        else:
            d = max_c - min_c
            s = d / (2 - max_c - min_c) if l > 0.5 else d / (max_c + min_c)
            
            if max_c == r:
                h = (g - b) / d + (6 if g < b else 0)
            elif max_c == g:
                h = (b - r) / d + 2
            else:
                h = (r - g) / d + 4
            h /= 6
        
        return HSL(h=int(h * 360), s=int(s * 100), l=int(l * 100))
    
    def to_lab(self) -> "LAB":
        """Convert to LAB color space via XYZ."""
        # RGB to XYZ
        r = self.r / 255.0
        g = self.g / 255.0
        b = self.b / 255.0
        
        # Apply gamma correction
        r = r ** 2.4 * 1.055 + 0.055 if r > 0.04045 else r / 12.92
        g = g ** 2.4 * 1.055 + 0.055 if g > 0.04045 else g / 12.92
        b = b ** 2.4 * 1.055 + 0.055 if b > 0.04045 else b / 12.92
        
        # Scale
        r *= 100
        g *= 100
        b *= 100
        
        # RGB to XYZ matrix (sRGB D65)
        x = r * 0.4124564 + g * 0.3575761 + b * 0.1804375
        y = r * 0.2126729 + g * 0.7151522 + b * 0.0721750
        z = r * 0.0193339 + g * 0.1191920 + b * 0.9503041
        
        # XYZ to LAB
        # Reference white D65
        xn, yn, zn = 95.047, 100.000, 108.883
        
        x = x / xn
        y = y / yn
        z = z / zn
        
        # Apply f function
        def f(t: float) -> float:
            delta = 6/29
            if t > delta ** 3:
                return t ** (1/3)
            else:
                return t / (3 * delta ** 2) + 4/29
        
        fx, fy, fz = f(x), f(y), f(z)
        
        L = 116 * fy - 16
        a = 500 * (fx - fy)
        b_val = 200 * (fy - fz)
        
        return LAB(L=round(L, 2), a=round(a, 2), b=round(b_val, 2))
    
    def distance_to(self, other: "RGB") -> float:
        """Calculate Euclidean distance to another RGB color."""
        return ((self.r - other.r) ** 2 + 
                (self.g - other.g) ** 2 + 
                (self.b - other.b) ** 2) ** 0.5
    
    def lab_distance_to(self, other: "RGB") -> float:
        """Calculate CIEDE2000-inspired distance using LAB color space.
        
        This is a simplified version that approximates perceptual distance.
        For full CIEDE2000, use colormath library.
        """
        lab1 = self.to_lab()
        lab2 = other.to_lab()
        
        # Simple LAB Euclidean distance (approximates perceptual distance)
        return ((lab1.L - lab2.L) ** 2 + 
                (lab1.a - lab2.a) ** 2 + 
                (lab1.b - lab2.b) ** 2) ** 0.5


class HSL(BaseModel):
    """HSL color representation."""
    h: int = Field(..., ge=0, le=360, description="Hue (0-360)")
    s: int = Field(..., ge=0, le=100, description="Saturation (0-100%)")
    l: int = Field(..., ge=0, le=100, description="Lightness (0-100%)")
    
    def to_rgb(self) -> RGB:
        """Convert to RGB color."""
        h, s, l = self.h / 360.0, self.s / 100.0, self.l / 100.0
        
        if s == 0:
            r = g = b = l
        else:
            def hue_to_rgb(p, q, t):
                if t < 0: t += 1
                if t > 1: t -= 1
                if t < 1/6: return p + (q - p) * 6 * t
                if t < 1/2: return q
                if t < 2/3: return p + (q - p) * (2/3 - t) * 6
                return p
            
            q = l * (1 + s) if l < 0.5 else l + s - l * s
            p = 2 * l - q
            r = hue_to_rgb(p, q, h + 1/3)
            g = hue_to_rgb(p, q, h)
            b = hue_to_rgb(p, q, h - 1/3)
        
        return RGB(
            r=int(round(r * 255)),
            g=int(round(g * 255)),
            b=int(round(b * 255))
        )


class HexColor(BaseModel):
    """Hex color representation."""
    value: str = Field(..., pattern=r"^#[0-9A-Fa-f]{6}$", description="Hex color (#RRGGBB)")
    
    def to_rgb(self) -> RGB:
        """Convert to RGB color."""
        hex_str = self.value.lstrip("#")
        return RGB(
            r=int(hex_str[0:2], 16),
            g=int(hex_str[2:4], 16),
            b=int(hex_str[4:6], 16)
        )


class LAB(BaseModel):
    """LAB color space representation for perceptual color distance."""
    L: float = Field(..., ge=0, le=128, description="Lightness (0-100, allow conversion overflow)")
    a: float = Field(..., ge=-128, le=128, description="Green-Red axis")
    b: float = Field(..., ge=-128, le=128, description="Blue-Yellow axis")


class ColorResult(BaseModel):
    """Result of color extraction from a component region."""
    dominant: RGB = Field(..., description="Most dominant color")
    colors: list[RGB] = Field(default_factory=list, description="All extracted colors")
    hex_values: list[str] = Field(default_factory=list, description="Hex representations")
    hsl_values: list[HSL] = Field(default_factory=list, description="HSL representations")
    lab_values: list[LAB] = Field(default_factory=list, description="LAB representations")
    pixel_count: int = Field(default=0, description="Number of pixels analyzed")
    is_gradient: bool = Field(
        default=False, 
        description="True if region appears to be a gradient"
    )


class ColorCluster(BaseModel):
    """A cluster of similar colors."""
    center: RGB = Field(..., description="Cluster center color")
    colors: list[RGB] = Field(default_factory=list, description="Colors in this cluster")
    count: int = Field(default=0, description="Number of pixels in cluster")
    percentage: float = Field(default=0.0, description="Percentage of total pixels")


# =============================================================================
# SPACING MODELS
# =============================================================================

class Margins(BaseModel):
    """Margin values for a component."""
    top: int = Field(default=0, ge=0, description="Top margin in pixels")
    right: int = Field(default=0, ge=0, description="Right margin in pixels")
    bottom: int = Field(default=0, ge=0, description="Bottom margin in pixels")
    left: int = Field(default=0, ge=0, description="Left margin in pixels")
    
    def to_quantized(self, grid_base: int = 4) -> "Margins":
        """Quantize margins to a grid base."""
        def quantize(value: int) -> int:
            return round(value / grid_base) * grid_base
        
        return Margins(
            top=quantize(self.top),
            right=quantize(self.right),
            bottom=quantize(self.bottom),
            left=quantize(self.left)
        )


class Padding(BaseModel):
    """Padding values for a container."""
    top: int = Field(default=0, ge=0, description="Top padding in pixels")
    right: int = Field(default=0, ge=0, description="Right padding in pixels")
    bottom: int = Field(default=0, ge=0, description="Bottom padding in pixels")
    left: int = Field(default=0, ge=0, description="Left padding in pixels")
    
    def to_quantized(self, grid_base: int = 4) -> "Padding":
        """Quantize padding to a grid base."""
        def quantize(value: int) -> int:
            return round(value / grid_base) * grid_base
        
        return Padding(
            top=quantize(self.top),
            right=quantize(self.right),
            bottom=quantize(self.bottom),
            left=quantize(self.left)
        )


class SpacingPattern(BaseModel):
    """Detected spacing pattern across multiple components."""
    values: list[int] = Field(default_factory=list, description="Spacing values found")
    most_common: int = Field(default=0, description="Most common spacing value")
    grid_base: int = Field(default=4, description="Detected grid base (4 or 8)")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Pattern confidence")


# =============================================================================
# TYPOGRAPHY MODELS
# =============================================================================

class FontWeight(str, Enum):
    """Font weight classifications."""
    LIGHT = "light"
    REGULAR = "regular"
    MEDIUM = "medium"
    SEMIBOLD = "semibold"
    BOLD = "bold"


class FontSizeEstimate(BaseModel):
    """Estimated font size from component bounding box."""
    size_px: int = Field(..., ge=1, description="Estimated font size in pixels")
    size_pt: float = Field(..., description="Estimated font size in points")
    confidence: float = Field(
        default=0.7, 
        ge=0.0, 
        le=1.0, 
        description="Estimation confidence"
    )
    method: str = Field(
        default="bbox_height",
        description="Method used for estimation"
    )


class FontWeightEstimate(BaseModel):
    """Estimated font weight from component appearance."""
    weight: FontWeight = Field(..., description="Estimated font weight")
    weight_numeric: int = Field(..., ge=100, le=900, description="Numeric weight (100-900)")
    confidence: float = Field(
        default=0.6,
        ge=0.0,
        le=1.0,
        description="Estimation confidence"
    )
    pixel_density: float = Field(
        default=0.0,
        description="Pixel density in text region"
    )


class TypographyResult(BaseModel):
    """Complete typography analysis result."""
    font_size: Optional[FontSizeEstimate] = Field(default=None, description="Font size estimate")
    font_weight: Optional[FontWeightEstimate] = Field(default=None, description="Font weight estimate")
    line_height: Optional[float] = Field(default=None, description="Line height if detectable")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Overall confidence")


# =============================================================================
# TOKEN MATCHING MODELS
# =============================================================================

class TokenType(str, Enum):
    """Types of design system tokens."""
    COLOR = "color"
    SPACING = "spacing"
    TYPOGRAPHY = "typography"
    BORDER = "border"
    SHADOW = "shadow"


class TokenMatch(BaseModel):
    """Result of matching an extracted value to a design system token."""
    matched: bool = Field(..., description="Whether a match was found")
    token_name: Optional[str] = Field(default=None, description="Name of matched token")
    token_value: Optional[str] = Field(default=None, description="Value of matched token")
    extracted_value: str = Field(..., description="The extracted value being matched")
    distance: float = Field(
        default=float('inf'),
        description="Distance from extracted value to token value"
    )
    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Match confidence (1.0 = exact match)"
    )
    token_type: TokenType = Field(..., description="Type of token")


class TokenMatchResult(BaseModel):
    """Complete token matching result for a component."""
    color_matches: list[TokenMatch] = Field(
        default_factory=list,
        description="Color token matches"
    )
    spacing_match: Optional[TokenMatch] = Field(
        default=None,
        description="Spacing token match"
    )
    typography_match: Optional[TokenMatch] = Field(
        default=None,
        description="Typography token match"
    )
    unmatched_colors: list[RGB] = Field(
        default_factory=list,
        description="Colors without matching tokens"
    )
    has_unmatched_tokens: bool = Field(
        default=False,
        description="True if any extracted values have no matching token"
    )
    
    @model_validator(mode='after')
    def compute_has_unmatched(self) -> 'TokenMatchResult':
        """Compute has_unmatched_tokens based on match results."""
        # Has unmatched if any color match failed or unmatched_colors list is non-empty
        has_failed_match = any(not m.matched for m in self.color_matches)
        if has_failed_match or len(self.unmatched_colors) > 0:
            self.has_unmatched_tokens = True
        return self


# =============================================================================
# DESIGN SYSTEM TOKEN MODELS
# =============================================================================

class DesignToken(BaseModel):
    """A single design system token."""
    name: str = Field(..., min_length=1, description="Token name (e.g., 'color-primary-500')")
    value: str = Field(..., min_length=1, description="Token value (e.g., '#3B82F6')")
    token_type: TokenType = Field(..., description="Type of token")
    description: Optional[str] = Field(default=None, description="Token description")
    
    def get_rgb_value(self) -> Optional[RGB]:
        """Get RGB value for color tokens."""
        if self.token_type != TokenType.COLOR:
            return None
        
        value = self.value.strip()
        if value.startswith("#"):
            return HexColor(value=value).to_rgb()
        return None
    
    def get_numeric_value(self) -> Optional[float]:
        """Get numeric value for spacing/typography tokens."""
        value = self.value.strip()
        # Extract numeric part (e.g., "16px" -> 16.0)
        import re
        match = re.match(r"([\d.]+)", value)
        if match:
            return float(match.group(1))
        return None


class DesignSystemTokens(BaseModel):
    """Collection of design system tokens."""
    colors: list[DesignToken] = Field(default_factory=list, description="Color tokens")
    spacing: list[DesignToken] = Field(default_factory=list, description="Spacing tokens")
    typography: list[DesignToken] = Field(default_factory=list, description="Typography tokens")
    borders: list[DesignToken] = Field(default_factory=list, description="Border tokens")
    shadows: list[DesignToken] = Field(default_factory=list, description="Shadow tokens")
    
    def get_all_tokens(self) -> list[DesignToken]:
        """Get all tokens as a flat list."""
        return (
            self.colors + 
            self.spacing + 
            self.typography + 
            self.borders + 
            self.shadows
        )