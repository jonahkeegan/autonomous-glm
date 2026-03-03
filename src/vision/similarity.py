"""
Screen similarity detection utilities.

Provides perceptual hashing and component overlap comparison for screen similarity.
"""

import time
from pathlib import Path
from typing import Optional, Union

from PIL import Image

from .models import DetectedComponent
from .flow_models import SimilarityScore


# Default thresholds
DEFAULT_DUPLICATE_THRESHOLD = 0.95
DEFAULT_SIMILAR_THRESHOLD = 0.90
DEFAULT_PHASH_WEIGHT = 0.5
DEFAULT_COMPONENT_WEIGHT = 0.5


class SimilarityCalculator:
    """Calculate similarity between screens using perceptual hashing and component overlap."""
    
    def __init__(
        self,
        duplicate_threshold: float = DEFAULT_DUPLICATE_THRESHOLD,
        similar_threshold: float = DEFAULT_SIMILAR_THRESHOLD,
        phash_weight: float = DEFAULT_PHASH_WEIGHT,
        component_weight: float = DEFAULT_COMPONENT_WEIGHT,
    ):
        """Initialize similarity calculator.
        
        Args:
            duplicate_threshold: Threshold above which screens are considered duplicates
            similar_threshold: Threshold above which screens are considered similar
            phash_weight: Weight for perceptual hash similarity in combined score
            component_weight: Weight for component overlap in combined score
        """
        self.duplicate_threshold = duplicate_threshold
        self.similar_threshold = similar_threshold
        self.phash_weight = phash_weight
        self.component_weight = component_weight
        
        # Import imagehash lazily to allow module to load without it
        self._imagehash = None
    
    @property
    def imagehash(self):
        """Lazy load imagehash module."""
        if self._imagehash is None:
            try:
                import imagehash
                self._imagehash = imagehash
            except ImportError:
                raise ImportError(
                    "imagehash is required for similarity detection. "
                    "Install with: pip install imagehash>=4.3.1"
                )
        return self._imagehash
    
    def calculate_phash_similarity(
        self,
        image1: Union[str, Path, Image.Image],
        image2: Union[str, Path, Image.Image],
        hash_size: int = 16,
    ) -> float:
        """Calculate perceptual hash similarity between two images.
        
        Args:
            image1: First image (path or PIL Image)
            image2: Second image (path or PIL Image)
            hash_size: Size of the hash (larger = more precise)
        
        Returns:
            Similarity score between 0.0 and 1.0
        """
        # Load images if paths provided
        if isinstance(image1, (str, Path)):
            img1 = Image.open(image1)
        else:
            img1 = image1
        
        if isinstance(image2, (str, Path)):
            img2 = Image.open(image2)
        else:
            img2 = image2
        
        # Convert to RGB if necessary
        if img1.mode != "RGB":
            img1 = img1.convert("RGB")
        if img2.mode != "RGB":
            img2 = img2.convert("RGB")
        
        # Calculate perceptual hashes
        hash1 = self.imagehash.phash(img1, hash_size=hash_size)
        hash2 = self.imagehash.phash(img2, hash_size=hash_size)
        
        # Calculate similarity (hash distance normalized to 0-1)
        max_distance = hash_size * hash_size  # Maximum possible Hamming distance
        distance = hash1 - hash2  # imagehash overloads subtraction for Hamming distance
        
        similarity = 1.0 - (distance / max_distance)
        return max(0.0, min(1.0, similarity))
    
    def calculate_component_overlap(
        self,
        components1: list[DetectedComponent],
        components2: list[DetectedComponent],
    ) -> float:
        """Calculate component overlap similarity between two screens.
        
        Uses Jaccard-like similarity based on component type and position overlap.
        
        Args:
            components1: Components from first screen
            components2: Components from second screen
        
        Returns:
            Similarity score between 0.0 and 1.0
        """
        if not components1 and not components2:
            return 1.0  # Both empty = identical
        if not components1 or not components2:
            return 0.0  # One empty = no similarity
        
        # Create component signatures (type + approximate position)
        def make_signature(c: DetectedComponent) -> tuple:
            # Quantize position to 0.1 precision for fuzzy matching
            x = round(c.bbox_x, 1)
            y = round(c.bbox_y, 1)
            w = round(c.bbox_width, 1)
            h = round(c.bbox_height, 1)
            return (c.type.value, x, y, w, h)
        
        sigs1 = set(make_signature(c) for c in components1)
        sigs2 = set(make_signature(c) for c in components2)
        
        # Calculate Jaccard similarity
        intersection = len(sigs1 & sigs2)
        union = len(sigs1 | sigs2)
        
        return intersection / union if union > 0 else 0.0
    
    def calculate_combined_similarity(
        self,
        phash_similarity: float,
        component_similarity: float,
    ) -> float:
        """Calculate weighted combined similarity score.
        
        Args:
            phash_similarity: Perceptual hash similarity
            component_similarity: Component overlap similarity
        
        Returns:
            Weighted combined score between 0.0 and 1.0
        """
        return (
            self.phash_weight * phash_similarity +
            self.component_weight * component_similarity
        )
    
    def calculate_similarity(
        self,
        screen1_id: str,
        screen2_id: str,
        image1: Optional[Union[str, Path, Image.Image]] = None,
        image2: Optional[Union[str, Path, Image.Image]] = None,
        components1: Optional[list[DetectedComponent]] = None,
        components2: Optional[list[DetectedComponent]] = None,
    ) -> SimilarityScore:
        """Calculate comprehensive similarity between two screens.
        
        Args:
            screen1_id: First screen identifier
            screen2_id: Second screen identifier
            image1: Optional first screen image
            image2: Optional second screen image
            components1: Optional first screen components
            components2: Optional second screen components
        
        Returns:
            SimilarityScore with all metrics
        """
        # Calculate perceptual hash similarity
        if image1 is not None and image2 is not None:
            phash_sim = self.calculate_phash_similarity(image1, image2)
        else:
            phash_sim = 0.0  # No images available
        
        # Calculate component overlap similarity
        if components1 is not None and components2 is not None:
            comp_sim = self.calculate_component_overlap(components1, components2)
        else:
            comp_sim = 0.0  # No components available
        
        # Calculate combined score
        combined = self.calculate_combined_similarity(phash_sim, comp_sim)
        
        return SimilarityScore(
            screen1_id=screen1_id,
            screen2_id=screen2_id,
            perceptual_hash_similarity=phash_sim,
            component_overlap_similarity=comp_sim,
            combined_score=combined,
            is_duplicate=combined >= self.duplicate_threshold,
        )
    
    def are_duplicates(
        self,
        image1: Union[str, Path, Image.Image],
        image2: Union[str, Path, Image.Image],
    ) -> bool:
        """Quick check if two images are duplicates.
        
        Args:
            image1: First image
            image2: Second image
        
        Returns:
            True if images are considered duplicates
        """
        similarity = self.calculate_phash_similarity(image1, image2)
        return similarity >= self.duplicate_threshold
    
    def find_most_similar(
        self,
        target: Union[str, Path, Image.Image],
        candidates: list[Union[str, Path, Image.Image]],
        top_k: int = 5,
    ) -> list[tuple[int, float]]:
        """Find most similar images to target from candidates.
        
        Args:
            target: Target image to match
            candidates: List of candidate images
            top_k: Number of top matches to return
        
        Returns:
            List of (index, similarity) tuples sorted by similarity descending
        """
        similarities = []
        for i, candidate in enumerate(candidates):
            sim = self.calculate_phash_similarity(target, candidate)
            similarities.append((i, sim))
        
        # Sort by similarity descending
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        return similarities[:top_k]


def calculate_phash_similarity(
    image1: Union[str, Path, Image.Image],
    image2: Union[str, Path, Image.Image],
) -> float:
    """Convenience function for perceptual hash similarity.
    
    Args:
        image1: First image
        image2: Second image
    
    Returns:
        Similarity score between 0.0 and 1.0
    """
    calculator = SimilarityCalculator()
    return calculator.calculate_phash_similarity(image1, image2)


def calculate_component_overlap(
    components1: list[DetectedComponent],
    components2: list[DetectedComponent],
) -> float:
    """Convenience function for component overlap similarity.
    
    Args:
        components1: Components from first screen
        components2: Components from second screen
    
    Returns:
        Similarity score between 0.0 and 1.0
    """
    calculator = SimilarityCalculator()
    return calculator.calculate_component_overlap(components1, components2)


def are_duplicate_screens(
    image1: Union[str, Path, Image.Image],
    image2: Union[str, Path, Image.Image],
    threshold: float = DEFAULT_DUPLICATE_THRESHOLD,
) -> bool:
    """Quick check if two screens are duplicates.
    
    Args:
        image1: First image
        image2: Second image
        threshold: Similarity threshold for duplicate detection
    
    Returns:
        True if screens are considered duplicates
    """
    calculator = SimilarityCalculator(duplicate_threshold=threshold)
    return calculator.are_duplicates(image1, image2)