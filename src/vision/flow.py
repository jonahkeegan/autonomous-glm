"""
Flow sequencing for video frame analysis.

Provides frame sequencing, key frame detection, and deduplication.
"""

import time
from pathlib import Path
from typing import Optional, Union
from uuid import uuid4

from PIL import Image

from .models import DetectedComponent
from .flow_models import (
    FlowSequence,
    FlowAnalysisResult,
    ScreenTransition,
    KeyFrameMarker,
    KeyFrameReason,
    TransitionType,
    SimilarityScore,
)
from .similarity import SimilarityCalculator, DEFAULT_DUPLICATE_THRESHOLD


# Default thresholds
DEFAULT_KEY_FRAME_THRESHOLD = 0.85  # Below this = key frame (significant change)
DEFAULT_DEDUP_THRESHOLD = 0.95  # Above this = duplicate


class ScreenData:
    """Container for screen data including image and components."""
    
    def __init__(
        self,
        screen_id: str,
        image: Optional[Union[str, Path, Image.Image]] = None,
        components: Optional[list[DetectedComponent]] = None,
        timestamp_ms: Optional[float] = None,
    ):
        """Initialize screen data.
        
        Args:
            screen_id: Unique screen identifier
            image: Optional image (path or PIL Image)
            components: Optional list of detected components
            timestamp_ms: Optional timestamp in milliseconds
        """
        self.screen_id = screen_id
        self.image = image
        self.components = components or []
        self.timestamp_ms = timestamp_ms


class FlowSequencer:
    """Sequence screens from video frames and detect key frames."""
    
    def __init__(
        self,
        key_frame_threshold: float = DEFAULT_KEY_FRAME_THRESHOLD,
        dedup_threshold: float = DEFAULT_DEDUP_THRESHOLD,
        similarity_calculator: Optional[SimilarityCalculator] = None,
    ):
        """Initialize flow sequencer.
        
        Args:
            key_frame_threshold: Similarity threshold below which frames are key frames
            dedup_threshold: Similarity threshold above which frames are duplicates
            similarity_calculator: Optional custom similarity calculator
        """
        self.key_frame_threshold = key_frame_threshold
        self.dedup_threshold = dedup_threshold
        self.similarity = similarity_calculator or SimilarityCalculator(
            duplicate_threshold=dedup_threshold
        )
    
    def calculate_screen_similarity(
        self,
        screen1: ScreenData,
        screen2: ScreenData,
    ) -> SimilarityScore:
        """Calculate similarity between two screens.
        
        Args:
            screen1: First screen
            screen2: Second screen
        
        Returns:
            SimilarityScore with all metrics
        """
        return self.similarity.calculate_similarity(
            screen1_id=screen1.screen_id,
            screen2_id=screen2.screen_id,
            image1=screen1.image,
            image2=screen2.image,
            components1=screen1.components,
            components2=screen2.components,
        )
    
    def detect_key_frames(
        self,
        screens: list[ScreenData],
    ) -> list[KeyFrameMarker]:
        """Detect key frames in a sequence of screens.
        
        Key frames are screens with significant visual changes.
        
        Args:
            screens: Ordered list of screens
        
        Returns:
            List of KeyFrameMarker for detected key frames
        """
        if not screens:
            return []
        
        key_frames = []
        
        # First frame is always a key frame
        key_frames.append(KeyFrameMarker(
            screen_id=screens[0].screen_id,
            reason=KeyFrameReason.FIRST_FRAME,
            confidence=1.0,
            description="First frame in sequence",
        ))
        
        if len(screens) == 1:
            return key_frames
        
        # Compare consecutive frames
        for i in range(1, len(screens)):
            prev_screen = screens[i - 1]
            curr_screen = screens[i]
            
            similarity = self.calculate_screen_similarity(prev_screen, curr_screen)
            
            # Key frame if similarity is below threshold
            if similarity.combined_score < self.key_frame_threshold:
                reason = self._determine_key_frame_reason(
                    prev_screen, curr_screen, similarity
                )
                
                key_frames.append(KeyFrameMarker(
                    screen_id=curr_screen.screen_id,
                    reason=reason,
                    confidence=1.0 - similarity.combined_score,
                    description=f"Significant change from previous (similarity: {similarity.combined_score:.2f})",
                ))
        
        # Last frame is always a key frame
        if len(screens) > 1:
            last_screen = screens[-1]
            if not any(kf.screen_id == last_screen.screen_id for kf in key_frames):
                key_frames.append(KeyFrameMarker(
                    screen_id=last_screen.screen_id,
                    reason=KeyFrameReason.LAST_FRAME,
                    confidence=1.0,
                    description="Last frame in sequence",
                ))
        
        return key_frames
    
    def deduplicate_frames(
        self,
        screens: list[ScreenData],
        threshold: Optional[float] = None,
    ) -> tuple[list[ScreenData], int]:
        """Remove duplicate frames from a sequence.
        
        Args:
            screens: Ordered list of screens
            threshold: Similarity threshold (uses default if not provided)
        
        Returns:
            Tuple of (deduplicated screens, duplicate count)
        """
        if not screens:
            return [], 0
        
        threshold = threshold or self.dedup_threshold
        
        deduplicated = [screens[0]]
        duplicate_count = 0
        
        for i in range(1, len(screens)):
            prev_screen = deduplicated[-1]  # Compare to last kept frame
            curr_screen = screens[i]
            
            similarity = self.calculate_screen_similarity(prev_screen, curr_screen)
            
            if similarity.combined_score < threshold:
                deduplicated.append(curr_screen)
            else:
                duplicate_count += 1
        
        return deduplicated, duplicate_count
    
    def sequence_screens(
        self,
        screens: list[ScreenData],
        deduplicate: bool = True,
        name: Optional[str] = None,
    ) -> FlowSequence:
        """Create a flow sequence from screens.
        
        Args:
            screens: Ordered list of screens
            deduplicate: Whether to remove duplicate frames
            name: Optional flow name
        
        Returns:
            FlowSequence with ordered screens and metadata
        """
        if not screens:
            return FlowSequence(name=name)
        
        # Deduplicate if requested
        processed_screens = screens
        duplicate_count = 0
        
        if deduplicate:
            processed_screens, duplicate_count = self.deduplicate_frames(screens)
        
        # Generate transitions
        transitions = self._generate_transitions(processed_screens)
        
        # Detect key frames
        key_frames = self.detect_key_frames(processed_screens)
        
        # Calculate total duration
        timestamps = [s.timestamp_ms for s in processed_screens if s.timestamp_ms is not None]
        total_duration = None
        if len(timestamps) >= 2:
            total_duration = timestamps[-1] - timestamps[0]
        
        return FlowSequence(
            name=name,
            screen_ids=[s.screen_id for s in processed_screens],
            transitions=transitions,
            key_frames=key_frames,
            total_duration_ms=total_duration,
            duplicate_count=duplicate_count,
        )
    
    def analyze(
        self,
        screens: list[ScreenData],
        deduplicate: bool = True,
        name: Optional[str] = None,
    ) -> FlowAnalysisResult:
        """Perform complete flow analysis.
        
        Args:
            screens: Ordered list of screens
            deduplicate: Whether to remove duplicate frames
            name: Optional flow name
        
        Returns:
            FlowAnalysisResult with all analysis data
        """
        start_time = time.time()
        
        # Create flow sequence
        flow = self.sequence_screens(screens, deduplicate=deduplicate, name=name)
        
        # Calculate all similarity scores
        similarity_scores = []
        screen_ids = flow.screen_ids
        
        for i in range(len(screen_ids) - 1):
            screen1 = next((s for s in screens if s.screen_id == screen_ids[i]), None)
            screen2 = next((s for s in screens if s.screen_id == screen_ids[i + 1]), None)
            
            if screen1 and screen2:
                sim = self.calculate_screen_similarity(screen1, screen2)
                similarity_scores.append(sim)
        
        # Calculate average similarity
        avg_similarity = 0.0
        if similarity_scores:
            avg_similarity = sum(s.combined_score for s in similarity_scores) / len(similarity_scores)
        
        processing_time = (time.time() - start_time) * 1000
        
        return FlowAnalysisResult(
            flow=flow,
            similarity_scores=similarity_scores,
            processing_time_ms=processing_time,
            average_similarity=avg_similarity,
        )
    
    def _generate_transitions(
        self,
        screens: list[ScreenData],
    ) -> list[ScreenTransition]:
        """Generate transitions between consecutive screens."""
        transitions = []
        
        for i in range(len(screens) - 1):
            from_screen = screens[i]
            to_screen = screens[i + 1]
            
            # Calculate similarity
            similarity = self.calculate_screen_similarity(from_screen, to_screen)
            
            # Detect component changes
            added, removed, moved = self._detect_component_changes(
                from_screen.components,
                to_screen.components,
            )
            
            # Determine transition type
            transition_type = self._infer_transition_type(
                from_screen, to_screen, similarity, added, removed
            )
            
            # Calculate duration
            duration = None
            if from_screen.timestamp_ms and to_screen.timestamp_ms:
                duration = to_screen.timestamp_ms - from_screen.timestamp_ms
            
            transitions.append(ScreenTransition(
                from_screen_id=from_screen.screen_id,
                to_screen_id=to_screen.screen_id,
                transition_type=transition_type,
                similarity_score=similarity.combined_score,
                components_added=[c.type.value for c in added],
                components_removed=[c.type.value for c in removed],
                components_moved=[c.type.value for c in moved],
                duration_ms=duration,
                confidence=similarity.combined_score,
            ))
        
        return transitions
    
    def _detect_component_changes(
        self,
        from_components: list[DetectedComponent],
        to_components: list[DetectedComponent],
    ) -> tuple[list[DetectedComponent], list[DetectedComponent], list[DetectedComponent]]:
        """Detect added, removed, and moved components."""
        def make_signature(c: DetectedComponent) -> tuple:
            return (
                c.type.value,
                round(c.bbox_x, 1),
                round(c.bbox_y, 1),
                round(c.bbox_width, 1),
                round(c.bbox_height, 1),
            )
        
        from_sigs = {make_signature(c): c for c in from_components}
        to_sigs = {make_signature(c): c for c in to_components}
        
        from_set = set(from_sigs.keys())
        to_set = set(to_sigs.keys())
        
        # Added: in to but not in from
        added = [to_sigs[sig] for sig in to_set - from_set]
        
        # Removed: in from but not in to
        removed = [from_sigs[sig] for sig in from_set - to_set]
        
        # Moved: same type but different position
        moved = []
        from_by_type: dict[str, list[tuple]] = {}
        for sig in from_set:
            comp_type = sig[0]
            if comp_type not in from_by_type:
                from_by_type[comp_type] = []
            from_by_type[comp_type].append(sig)
        
        to_by_type: dict[str, list[tuple]] = {}
        for sig in to_set:
            comp_type = sig[0]
            if comp_type not in to_by_type:
                to_by_type[comp_type] = []
            to_by_type[comp_type].append(sig)
        
        for comp_type, from_sigs_list in from_by_type.items():
            to_sigs_list = to_by_type.get(comp_type, [])
            
            # If same type appears in both but with different positions
            if from_sigs_list and to_sigs_list:
                from_positions = set(sig[1:3] for sig in from_sigs_list)  # x, y
                to_positions = set(sig[1:3] for sig in to_sigs_list)
                
                if from_positions != to_positions:
                    # Component of this type moved
                    for sig in to_sigs_list:
                        if sig[1:3] not in from_positions:
                            moved.append(to_sigs[sig])
        
        return added, removed, moved
    
    def _infer_transition_type(
        self,
        from_screen: ScreenData,
        to_screen: ScreenData,
        similarity: SimilarityScore,
        added: list[DetectedComponent],
        removed: list[DetectedComponent],
    ) -> TransitionType:
        """Infer the type of transition between screens."""
        from .models import ComponentType
        
        # Check for modal
        added_types = [c.type for c in added]
        removed_types = [c.type for c in removed]
        
        # Modal opened
        if ComponentType.MODAL in added_types:
            return TransitionType.MODAL_OPEN
        
        # Modal closed
        if ComponentType.MODAL in removed_types:
            return TransitionType.MODAL_CLOSE
        
        # Significant navigation (low similarity)
        if similarity.combined_score < 0.5:
            return TransitionType.NAVIGATION
        
        # Tab switch (moderate similarity, different content)
        if similarity.combined_score < 0.7:
            return TransitionType.TAB_SWITCH
        
        # Scroll (high similarity, slight position changes)
        if similarity.combined_score > 0.9:
            return TransitionType.SCROLL
        
        return TransitionType.UNKNOWN
    
    def _determine_key_frame_reason(
        self,
        prev_screen: ScreenData,
        curr_screen: ScreenData,
        similarity: SimilarityScore,
    ) -> KeyFrameReason:
        """Determine why a frame is a key frame."""
        # Very low similarity = navigation or new screen
        if similarity.combined_score < 0.5:
            return KeyFrameReason.SIGNIFICANT_CHANGE
        
        # Check for new elements
        added, removed, _ = self._detect_component_changes(
            prev_screen.components, curr_screen.components
        )
        
        if added:
            return KeyFrameReason.NEW_ELEMENT
        
        if removed:
            return KeyFrameReason.ELEMENT_REMOVED
        
        # Check for layout changes
        if similarity.perceptual_hash_similarity > similarity.component_overlap_similarity:
            return KeyFrameReason.LAYOUT_CHANGE
        
        return KeyFrameReason.SIGNIFICANT_CHANGE


def sequence_screens(
    screens: list[ScreenData],
    deduplicate: bool = True,
    name: Optional[str] = None,
) -> FlowSequence:
    """Convenience function for screen sequencing.
    
    Args:
        screens: Ordered list of screens
        deduplicate: Whether to remove duplicate frames
        name: Optional flow name
    
    Returns:
        FlowSequence with ordered screens and metadata
    """
    sequencer = FlowSequencer()
    return sequencer.sequence_screens(screens, deduplicate=deduplicate, name=name)


def detect_key_frames(
    screens: list[ScreenData],
) -> list[KeyFrameMarker]:
    """Convenience function for key frame detection.
    
    Args:
        screens: Ordered list of screens
    
    Returns:
        List of KeyFrameMarker for detected key frames
    """
    sequencer = FlowSequencer()
    return sequencer.detect_key_frames(screens)


def deduplicate_frames(
    screens: list[ScreenData],
    threshold: Optional[float] = None,
) -> tuple[list[ScreenData], int]:
    """Convenience function for frame deduplication.
    
    Args:
        screens: Ordered list of screens
        threshold: Similarity threshold
    
    Returns:
        Tuple of (deduplicated screens, duplicate count)
    """
    sequencer = FlowSequencer()
    return sequencer.deduplicate_frames(screens, threshold=threshold)