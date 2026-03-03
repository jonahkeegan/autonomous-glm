"""
Pydantic models for flow analysis results.

Defines models for screen sequences, transitions, and frame analysis.
"""

from enum import Enum
from datetime import datetime
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class TransitionType(str, Enum):
    """Types of screen transitions."""
    NAVIGATION = "navigation"
    MODAL_OPEN = "modal_open"
    MODAL_CLOSE = "modal_close"
    SCROLL = "scroll"
    TAB_SWITCH = "tab_switch"
    FORM_SUBMIT = "form_submit"
    LOADING = "loading"
    ANIMATION = "animation"
    UNKNOWN = "unknown"


class KeyFrameReason(str, Enum):
    """Reasons why a frame is marked as a key frame."""
    SIGNIFICANT_CHANGE = "significant_change"
    TRANSITION_START = "transition_start"
    TRANSITION_END = "transition_end"
    NEW_ELEMENT = "new_element"
    ELEMENT_REMOVED = "element_removed"
    LAYOUT_CHANGE = "layout_change"
    USER_ACTION = "user_action"
    FIRST_FRAME = "first_frame"
    LAST_FRAME = "last_frame"


class SimilarityScore(BaseModel):
    """Screen similarity comparison result."""
    
    screen1_id: str = Field(..., description="First screen ID")
    screen2_id: str = Field(..., description="Second screen ID")
    perceptual_hash_similarity: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Visual similarity from perceptual hashing (0-1)"
    )
    component_overlap_similarity: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Component overlap similarity (0-1)"
    )
    combined_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Weighted combined similarity score (0-1)"
    )
    is_duplicate: bool = Field(
        default=False,
        description="Whether screens are considered duplicates"
    )
    
    @property
    def is_similar(self) -> bool:
        """Return True if screens are considered similar (> 0.95)."""
        return self.combined_score >= 0.95


class ScreenTransition(BaseModel):
    """Transition between two consecutive screens."""
    
    id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique transition identifier"
    )
    from_screen_id: str = Field(..., description="Source screen ID")
    to_screen_id: str = Field(..., description="Target screen ID")
    transition_type: TransitionType = Field(
        default=TransitionType.UNKNOWN,
        description="Type of transition"
    )
    similarity_score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Similarity between screens"
    )
    components_added: list[str] = Field(
        default_factory=list,
        description="Component IDs appearing in target but not source"
    )
    components_removed: list[str] = Field(
        default_factory=list,
        description="Component IDs appearing in source but not target"
    )
    components_moved: list[str] = Field(
        default_factory=list,
        description="Component IDs that changed position"
    )
    duration_ms: Optional[float] = Field(
        default=None,
        ge=0.0,
        description="Time between screens in milliseconds"
    )
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Confidence in transition detection"
    )


class KeyFrameMarker(BaseModel):
    """Marker indicating a key frame in a sequence."""
    
    screen_id: str = Field(..., description="Screen ID marked as key frame")
    reason: KeyFrameReason = Field(
        ...,
        description="Why this frame is a key frame"
    )
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Confidence in key frame detection"
    )
    description: Optional[str] = Field(
        default=None,
        description="Human-readable description of the key frame"
    )


class FlowSequence(BaseModel):
    """Ordered sequence of screens representing a user flow."""
    
    id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique flow identifier"
    )
    name: Optional[str] = Field(
        default=None,
        description="Human-readable flow name"
    )
    screen_ids: list[str] = Field(
        default_factory=list,
        description="Ordered list of screen IDs"
    )
    transitions: list[ScreenTransition] = Field(
        default_factory=list,
        description="Transitions between consecutive screens"
    )
    key_frames: list[KeyFrameMarker] = Field(
        default_factory=list,
        description="Key frame markers"
    )
    total_duration_ms: Optional[float] = Field(
        default=None,
        ge=0.0,
        description="Total flow duration in milliseconds"
    )
    screen_count: int = Field(
        default=0,
        ge=0,
        description="Number of screens in the flow"
    )
    key_frame_count: int = Field(
        default=0,
        ge=0,
        description="Number of key frames"
    )
    duplicate_count: int = Field(
        default=0,
        ge=0,
        description="Number of duplicate frames removed"
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="When the flow was created"
    )
    
    def model_post_init(self, __context) -> None:
        """Update counts after initialization."""
        self.screen_count = len(self.screen_ids)
        self.key_frame_count = len(self.key_frames)
    
    def get_transition(self, from_index: int) -> Optional[ScreenTransition]:
        """Get transition at a specific index."""
        if 0 <= from_index < len(self.transitions):
            return self.transitions[from_index]
        return None
    
    def is_key_frame(self, screen_id: str) -> bool:
        """Check if a screen is a key frame."""
        return any(kf.screen_id == screen_id for kf in self.key_frames)
    
    def get_key_frame_marker(self, screen_id: str) -> Optional[KeyFrameMarker]:
        """Get key frame marker for a screen."""
        for kf in self.key_frames:
            if kf.screen_id == screen_id:
                return kf
        return None


class FlowAnalysisResult(BaseModel):
    """Complete flow analysis result."""
    
    flow: FlowSequence = Field(..., description="Analyzed flow sequence")
    similarity_scores: list[SimilarityScore] = Field(
        default_factory=list,
        description="Pairwise similarity scores between consecutive screens"
    )
    processing_time_ms: float = Field(
        default=0.0,
        ge=0.0,
        description="Total processing time in milliseconds"
    )
    average_similarity: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Average similarity between consecutive screens"
    )
    
    @property
    def has_duplicates(self) -> bool:
        """Return True if any duplicate frames were detected."""
        return self.flow.duplicate_count > 0