"""
Typography detection utilities for token extraction.

Provides font size and weight estimation from component bounding boxes.
"""

from pathlib import Path
from typing import Optional, Union

import numpy as np
from PIL import Image

from .models import (
    FontWeight,
    FontSizeEstimate,
    FontWeightEstimate,
    TypographyResult,
)


# Font size estimation factor (bbox height includes line-height padding)
FONT_SIZE_FACTOR = 0.8

# Default line-height ratio
DEFAULT_LINE_HEIGHT = 1.5

# Pixel density thresholds for weight detection
WEIGHT_DENSITY_THRESHOLDS = {
    FontWeight.LIGHT: 0.15,
    FontWeight.REGULAR: 0.25,
    FontWeight.MEDIUM: 0.35,
    FontWeight.SEMIBOLD: 0.45,
    FontWeight.BOLD: 0.55,
}

# Numeric weight mappings
WEIGHT_NUMERIC = {
    FontWeight.LIGHT: 300,
    FontWeight.REGULAR: 400,
    FontWeight.MEDIUM: 500,
    FontWeight.SEMIBOLD: 600,
    FontWeight.BOLD: 700,
}


class TypographyDetector:
    """Detect typography properties from component appearance."""
    
    def __init__(self, line_height: float = DEFAULT_LINE_HEIGHT):
        """Initialize the typography detector.
        
        Args:
            line_height: Default line-height ratio (default: 1.5)
        """
        self.line_height = line_height
    
    def estimate_font_size(
        self,
        bbox_height: float,
        is_text_component: bool = True
    ) -> FontSizeEstimate:
        """Estimate font size from bounding box height.
        
        Args:
            bbox_height: Height of text bounding box in pixels
            is_text_component: Whether this is confirmed text
        
        Returns:
            FontSizeEstimate with estimated size
        """
        if bbox_height <= 0:
            return FontSizeEstimate(
                size_px=12,
                size_pt=9.0,
                confidence=0.3,
                method="bbox_height"
            )
        
        # Estimate: font_size ≈ bbox_height * factor
        # The factor accounts for line-height padding
        estimated_px = int(bbox_height * FONT_SIZE_FACTOR)
        
        # Clamp to reasonable range
        estimated_px = max(8, min(estimated_px, 96))
        
        # Convert to points (assuming 96 DPI)
        estimated_pt = estimated_px * 0.75
        
        # Confidence based on typical text sizes
        if 12 <= estimated_px <= 24:
            confidence = 0.8
        elif 8 <= estimated_px <= 48:
            confidence = 0.7
        else:
            confidence = 0.5
        
        if not is_text_component:
            confidence *= 0.8
        
        return FontSizeEstimate(
            size_px=estimated_px,
            size_pt=round(estimated_pt, 1),
            confidence=confidence,
            method="bbox_height"
        )
    
    def estimate_font_weight(
        self,
        image_path: Union[str, Path],
        bbox: Optional[tuple[float, float, float, float]] = None,
        normalize: bool = True
    ) -> FontWeightEstimate:
        """Estimate font weight from pixel density in text region.
        
        Args:
            image_path: Path to the image file
            bbox: Optional bounding box (x, y, width, height)
            normalize: Whether bbox is normalized (0-1)
        
        Returns:
            FontWeightEstimate with estimated weight
        """
        # Load image
        image_path = Path(image_path)
        if not image_path.exists():
            return FontWeightEstimate(
                weight=FontWeight.REGULAR,
                weight_numeric=400,
                confidence=0.3,
                pixel_density=0.0
            )
        
        img = Image.open(image_path).convert("L")  # Grayscale
        img_width, img_height = img.size
        
        # Extract region if bbox provided
        if bbox:
            x, y, width, height = bbox
            
            if normalize:
                x = int(x * img_width)
                y = int(y * img_height)
                width = int(width * img_width)
                height = int(height * img_height)
            else:
                x, y, width, height = int(x), int(y), int(width), int(height)
            
            # Clamp to bounds
            x = max(0, min(x, img_width))
            y = max(0, min(y, img_height))
            width = max(1, min(width, img_width - x))
            height = max(1, min(height, img_height - y))
            
            img = img.crop((x, y, x + width, y + height))
        
        # Convert to numpy array
        pixels = np.array(img)
        
        # Calculate pixel density (darker = more ink = heavier weight)
        # Normalize to 0-1 range where 0 = white, 1 = black
        if pixels.size > 0:
            # Invert so black = 1, white = 0
            inverted = 255 - pixels
            density = inverted.mean() / 255.0
        else:
            density = 0.0
        
        # Classify weight based on density
        weight = self._classify_weight(density)
        weight_numeric = WEIGHT_NUMERIC[weight]
        
        # Confidence based on how close to thresholds
        confidence = self._calculate_weight_confidence(density, weight)
        
        return FontWeightEstimate(
            weight=weight,
            weight_numeric=weight_numeric,
            confidence=confidence,
            pixel_density=round(density, 3)
        )
    
    def _classify_weight(self, density: float) -> FontWeight:
        """Classify font weight from pixel density.
        
        Args:
            density: Pixel density (0-1)
        
        Returns:
            FontWeight classification
        """
        if density < WEIGHT_DENSITY_THRESHOLDS[FontWeight.LIGHT]:
            return FontWeight.LIGHT
        elif density < WEIGHT_DENSITY_THRESHOLDS[FontWeight.REGULAR]:
            return FontWeight.LIGHT
        elif density < WEIGHT_DENSITY_THRESHOLDS[FontWeight.MEDIUM]:
            return FontWeight.REGULAR
        elif density < WEIGHT_DENSITY_THRESHOLDS[FontWeight.SEMIBOLD]:
            return FontWeight.MEDIUM
        elif density < WEIGHT_DENSITY_THRESHOLDS[FontWeight.BOLD]:
            return FontWeight.SEMIBOLD
        else:
            return FontWeight.BOLD
    
    def _calculate_weight_confidence(
        self, 
        density: float, 
        weight: FontWeight
    ) -> float:
        """Calculate confidence for weight classification.
        
        Args:
            density: Pixel density
            weight: Classified weight
        
        Returns:
            Confidence score (0-1)
        """
        threshold = WEIGHT_DENSITY_THRESHOLDS[weight]
        
        # Find distance to nearest threshold boundary
        thresholds = list(WEIGHT_DENSITY_THRESHOLDS.values())
        
        # Calculate distance to classification boundaries
        distances = [abs(density - t) for t in thresholds]
        min_distance = min(distances) if distances else 0
        
        # Closer to threshold center = higher confidence
        # Max distance between thresholds is ~0.1
        confidence = min(0.9, 0.5 + min_distance * 2)
        
        return round(confidence, 2)
    
    def detect_line_height(
        self,
        text_bbox_height: float,
        font_size: int
    ) -> float:
        """Calculate line height from text bbox and font size.
        
        Args:
            text_bbox_height: Height of text bounding box
            font_size: Estimated font size in pixels
        
        Returns:
            Estimated line-height ratio
        """
        if font_size <= 0:
            return DEFAULT_LINE_HEIGHT
        
        line_height = text_bbox_height / font_size
        
        # Clamp to reasonable range
        return max(1.0, min(line_height, 2.5))
    
    def analyze(
        self,
        bbox_height: float,
        image_path: Optional[Union[str, Path]] = None,
        bbox: Optional[tuple[float, float, float, float]] = None,
        is_text_component: bool = True
    ) -> TypographyResult:
        """Perform complete typography analysis.
        
        Args:
            bbox_height: Height of component bounding box
            image_path: Optional path to image for weight analysis
            bbox: Optional bounding box for weight analysis
            is_text_component: Whether this is a text component
        
        Returns:
            TypographyResult with all estimates
        """
        font_size = self.estimate_font_size(bbox_height, is_text_component)
        
        font_weight = None
        if image_path:
            font_weight = self.estimate_font_weight(image_path, bbox)
        
        line_height = self.detect_line_height(bbox_height, font_size.size_px)
        
        # Overall confidence
        confidence = font_size.confidence
        if font_weight:
            confidence = (confidence + font_weight.confidence) / 2
        
        return TypographyResult(
            font_size=font_size,
            font_weight=font_weight,
            line_height=round(line_height, 2),
            confidence=confidence
        )


def estimate_font_size(
    bbox_height: float,
    is_text_component: bool = True
) -> FontSizeEstimate:
    """Convenience function to estimate font size.
    
    Args:
        bbox_height: Height of text bounding box in pixels
        is_text_component: Whether this is confirmed text
    
    Returns:
        FontSizeEstimate with estimated size
    """
    detector = TypographyDetector()
    return detector.estimate_font_size(bbox_height, is_text_component)


def estimate_font_weight(
    image_path: Union[str, Path],
    bbox: Optional[tuple[float, float, float, float]] = None,
    normalize: bool = True
) -> FontWeightEstimate:
    """Convenience function to estimate font weight.
    
    Args:
        image_path: Path to the image file
        bbox: Optional bounding box (x, y, width, height)
        normalize: Whether bbox is normalized (0-1)
    
    Returns:
        FontWeightEstimate with estimated weight
    """
    detector = TypographyDetector()
    return detector.estimate_font_weight(image_path, bbox, normalize)


def detect_line_height(
    text_bbox_height: float,
    font_size: int
) -> float:
    """Convenience function to detect line height.
    
    Args:
        text_bbox_height: Height of text bounding box
        font_size: Estimated font size in pixels
    
    Returns:
        Estimated line-height ratio
    """
    detector = TypographyDetector()
    return detector.detect_line_height(text_bbox_height, font_size)