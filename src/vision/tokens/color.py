"""
Color extraction utilities for token analysis.

Provides k-means clustering-based color extraction from UI component regions.
"""

from pathlib import Path
from typing import Optional, Union

import numpy as np
from PIL import Image
from sklearn.cluster import KMeans

from .models import (
    RGB,
    HSL,
    LAB,
    HexColor,
    ColorResult,
    ColorCluster,
)


# Default number of clusters for k-means
DEFAULT_N_CLUSTERS = 3

# Minimum pixels required for extraction
MIN_PIXELS_FOR_EXTRACTION = 100

# Threshold for gradient detection (color variance)
GRADIENT_VARIANCE_THRESHOLD = 50.0


class ColorExtractor:
    """Extract dominant colors from image regions using k-means clustering."""
    
    def __init__(
        self,
        n_clusters: int = DEFAULT_N_CLUSTERS,
        random_state: int = 42
    ):
        """Initialize the color extractor.
        
        Args:
            n_clusters: Number of color clusters to find (default: 3)
            random_state: Random state for reproducibility
        """
        self.n_clusters = n_clusters
        self.random_state = random_state
    
    def extract_colors(
        self,
        image_path: Union[str, Path],
        bbox: Optional[tuple[float, float, float, float]] = None,
        normalize: bool = True
    ) -> ColorResult:
        """Extract colors from an image or region.
        
        Args:
            image_path: Path to the image file
            bbox: Optional bounding box as (x, y, width, height) in normalized coords (0-1)
                  or absolute pixels if normalize=False
            normalize: Whether bbox coordinates are normalized (0-1)
        
        Returns:
            ColorResult with dominant colors and all representations
        """
        # Load image
        image_path = Path(image_path)
        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")
        
        img = Image.open(image_path).convert("RGB")
        img_width, img_height = img.size
        
        # Extract region if bbox provided
        if bbox:
            x, y, width, height = bbox
            
            if normalize:
                # Convert normalized to absolute
                x = int(x * img_width)
                y = int(y * img_height)
                width = int(width * img_width)
                height = int(height * img_height)
            else:
                x, y, width, height = int(x), int(y), int(width), int(height)
            
            # Clamp to image bounds
            x = max(0, min(x, img_width))
            y = max(0, min(y, img_height))
            width = max(1, min(width, img_width - x))
            height = max(1, min(height, img_height - y))
            
            img = img.crop((x, y, x + width, y + height))
        
        # Convert to numpy array
        pixels = np.array(img)
        pixel_count = pixels.shape[0] * pixels.shape[1]
        
        if pixel_count < MIN_PIXELS_FOR_EXTRACTION:
            # Return a simple average for small regions
            avg_color = pixels.mean(axis=(0, 1)).astype(int)
            dominant = RGB(r=avg_color[0], g=avg_color[1], b=avg_color[2])
            return ColorResult(
                dominant=dominant,
                colors=[dominant],
                pixel_count=pixel_count,
                is_gradient=False
            )
        
        # Reshape to list of pixels
        pixels_flat = pixels.reshape(-1, 3)
        
        # Check for gradient (high variance)
        variance = pixels_flat.var()
        is_gradient = variance > GRADIENT_VARIANCE_THRESHOLD
        
        # Run k-means clustering
        n_clusters = min(self.n_clusters, pixel_count)
        kmeans = KMeans(
            n_clusters=n_clusters,
            random_state=self.random_state,
            n_init=10
        )
        kmeans.fit(pixels_flat)
        
        # Get cluster centers and counts
        centers = kmeans.cluster_centers_.astype(int)
        labels = kmeans.labels_
        counts = np.bincount(labels)
        
        # Sort by count (most dominant first)
        sorted_indices = np.argsort(-counts)
        
        # Create RGB objects
        colors = []
        for idx in sorted_indices:
            center = centers[idx]
            colors.append(RGB(r=center[0], g=center[1], b=center[2]))
        
        dominant = colors[0] if colors else RGB(r=0, g=0, b=0)
        
        # Generate all color representations
        hex_values = [c.to_hex().value for c in colors]
        hsl_values = [c.to_hsl() for c in colors]
        lab_values = [c.to_lab() for c in colors]
        
        return ColorResult(
            dominant=dominant,
            colors=colors,
            hex_values=hex_values,
            hsl_values=hsl_values,
            lab_values=lab_values,
            pixel_count=pixel_count,
            is_gradient=is_gradient
        )
    
    def get_dominant_color(
        self,
        pixels: np.ndarray
    ) -> RGB:
        """Get the single dominant color from pixel array.
        
        Args:
            pixels: Numpy array of shape (N, 3) containing RGB values
        
        Returns:
            RGB object representing the dominant color
        """
        if len(pixels) < MIN_PIXELS_FOR_EXTRACTION:
            avg = pixels.mean(axis=0).astype(int)
            return RGB(r=avg[0], g=avg[1], b=avg[2])
        
        kmeans = KMeans(
            n_clusters=1,
            random_state=self.random_state,
            n_init=10
        )
        kmeans.fit(pixels)
        center = kmeans.cluster_centers_[0].astype(int)
        
        return RGB(r=center[0], g=center[1], b=center[2])
    
    def cluster_colors(
        self,
        colors: list[RGB],
        n_clusters: int = 5
    ) -> list[ColorCluster]:
        """Cluster similar colors together.
        
        Args:
            colors: List of RGB colors to cluster
            n_clusters: Number of clusters to create
        
        Returns:
            List of ColorCluster objects
        """
        if not colors:
            return []
        
        if len(colors) <= n_clusters:
            # Each color is its own cluster
            return [
                ColorCluster(center=c, colors=[c], count=1, percentage=100.0 / len(colors))
                for c in colors
            ]
        
        # Convert to numpy array
        color_array = np.array([[c.r, c.g, c.b] for c in colors])
        
        # Run k-means
        kmeans = KMeans(
            n_clusters=n_clusters,
            random_state=self.random_state,
            n_init=10
        )
        kmeans.fit(color_array)
        
        # Create clusters
        clusters = []
        labels = kmeans.labels_
        centers = kmeans.cluster_centers_.astype(int)
        total = len(colors)
        
        for i in range(n_clusters):
            mask = labels == i
            cluster_colors = [colors[j] for j in range(len(colors)) if mask[j]]
            center = RGB(r=centers[i][0], g=centers[i][1], b=centers[i][2])
            
            clusters.append(ColorCluster(
                center=center,
                colors=cluster_colors,
                count=len(cluster_colors),
                percentage=len(cluster_colors) / total * 100
            ))
        
        # Sort by count (largest first)
        clusters.sort(key=lambda c: c.count, reverse=True)
        
        return clusters


def normalize_color(color: RGB) -> dict[str, Union[RGB, HSL, LAB, HexColor, str]]:
    """Normalize a color to all representations.
    
    Args:
        color: RGB color to normalize
    
    Returns:
        Dictionary with all color representations
    """
    return {
        "rgb": color,
        "hsl": color.to_hsl(),
        "lab": color.to_lab(),
        "hex": color.to_hex(),
        "hex_value": color.to_hex().value,
    }


def extract_colors(
    image_path: Union[str, Path],
    bbox: Optional[tuple[float, float, float, float]] = None,
    normalize: bool = True
) -> ColorResult:
    """Convenience function to extract colors from an image.
    
    Args:
        image_path: Path to the image file
        bbox: Optional bounding box as (x, y, width, height)
        normalize: Whether bbox coordinates are normalized (0-1)
    
    Returns:
        ColorResult with dominant colors
    """
    extractor = ColorExtractor()
    return extractor.extract_colors(image_path, bbox, normalize)


def get_dominant_color(pixels: np.ndarray) -> RGB:
    """Convenience function to get dominant color from pixels.
    
    Args:
        pixels: Numpy array of shape (N, 3) containing RGB values
    
    Returns:
        RGB object representing the dominant color
    """
    extractor = ColorExtractor()
    return extractor.get_dominant_color(pixels)


def cluster_colors(
    colors: list[RGB],
    n_clusters: int = 5
) -> list[ColorCluster]:
    """Convenience function to cluster colors.
    
    Args:
        colors: List of RGB colors to cluster
        n_clusters: Number of clusters to create
    
    Returns:
        List of ColorCluster objects
    """
    extractor = ColorExtractor()
    return extractor.cluster_colors(colors, n_clusters)