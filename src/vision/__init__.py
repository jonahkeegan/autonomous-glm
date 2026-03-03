"""
Vision module for Autonomous-GLM.

Provides GPT-4 Vision API integration for UI component detection,
hierarchy analysis, flow sequencing, and token extraction.
"""

from .models import (
    ComponentType,
    DetectedComponent,
    DetectionResult,
    DetectionConfig,
)
from .client import VisionClient
from .prompts import (
    SYSTEM_PROMPT,
    USER_PROMPT_TEMPLATE,
    build_detection_prompt,
)
from .hierarchy_models import (
    HierarchyNode,
    HierarchyTree,
    ContainerMatch,
    ZLayer,
    NestingLevel,
    HierarchyAnalysisResult,
)
from .flow_models import (
    TransitionType,
    KeyFrameReason,
    SimilarityScore,
    ScreenTransition,
    KeyFrameMarker,
    FlowSequence,
    FlowAnalysisResult,
)
from .similarity import (
    SimilarityCalculator,
    calculate_phash_similarity,
    calculate_component_overlap,
    are_duplicate_screens,
    DEFAULT_DUPLICATE_THRESHOLD,
    DEFAULT_SIMILAR_THRESHOLD,
)
from .hierarchy import (
    HierarchyAnalyzer,
    extract_hierarchy,
    detect_containers,
    infer_z_order,
    DEFAULT_AREA_RATIO_THRESHOLD,
    DEFAULT_CONTAINMENT_THRESHOLD,
)
from .flow import (
    ScreenData,
    FlowSequencer,
    sequence_screens,
    detect_key_frames,
    deduplicate_frames,
    DEFAULT_KEY_FRAME_THRESHOLD,
    DEFAULT_DEDUP_THRESHOLD,
)

__all__ = [
    # Models
    "ComponentType",
    "DetectedComponent",
    "DetectionResult",
    "DetectionConfig",
    # Client
    "VisionClient",
    # Prompts
    "SYSTEM_PROMPT",
    "USER_PROMPT_TEMPLATE",
    "build_detection_prompt",
    # Hierarchy Models
    "HierarchyNode",
    "HierarchyTree",
    "ContainerMatch",
    "ZLayer",
    "NestingLevel",
    "HierarchyAnalysisResult",
    # Flow Models
    "TransitionType",
    "KeyFrameReason",
    "SimilarityScore",
    "ScreenTransition",
    "KeyFrameMarker",
    "FlowSequence",
    "FlowAnalysisResult",
    # Similarity
    "SimilarityCalculator",
    "calculate_phash_similarity",
    "calculate_component_overlap",
    "are_duplicate_screens",
    "DEFAULT_DUPLICATE_THRESHOLD",
    "DEFAULT_SIMILAR_THRESHOLD",
    # Hierarchy
    "HierarchyAnalyzer",
    "extract_hierarchy",
    "detect_containers",
    "infer_z_order",
    "DEFAULT_AREA_RATIO_THRESHOLD",
    "DEFAULT_CONTAINMENT_THRESHOLD",
    # Flow
    "ScreenData",
    "FlowSequencer",
    "sequence_screens",
    "detect_key_frames",
    "deduplicate_frames",
    "DEFAULT_KEY_FRAME_THRESHOLD",
    "DEFAULT_DEDUP_THRESHOLD",
]
