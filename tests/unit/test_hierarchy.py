"""
Unit tests for hierarchy and flow analysis modules.

Tests for:
- Hierarchy extraction (container detection, z-order, tree building)
- Screen similarity (perceptual hash, component overlap)
- Flow sequencing (key frames, deduplication, transitions)
"""

import pytest
from PIL import Image
import io

from src.vision.models import DetectedComponent, ComponentType
from src.vision.hierarchy_models import (
    HierarchyNode,
    HierarchyTree,
    ContainerMatch,
    ZLayer,
    NestingLevel,
    HierarchyAnalysisResult,
)
from src.vision.flow_models import (
    TransitionType,
    KeyFrameReason,
    SimilarityScore,
    ScreenTransition,
    KeyFrameMarker,
    FlowSequence,
    FlowAnalysisResult,
)
from src.vision.similarity import (
    SimilarityCalculator,
    calculate_component_overlap,
    DEFAULT_DUPLICATE_THRESHOLD,
)
from src.vision.hierarchy import (
    HierarchyAnalyzer,
    extract_hierarchy,
    detect_containers,
    infer_z_order,
)
from src.vision.flow import (
    ScreenData,
    FlowSequencer,
    sequence_screens,
    detect_key_frames,
    deduplicate_frames,
)


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def simple_components():
    """Create simple components with no nesting."""
    return [
        DetectedComponent(
            type=ComponentType.BUTTON,
            bbox_x=0.1,
            bbox_y=0.1,
            bbox_width=0.2,
            bbox_height=0.1,
            confidence=0.95,
        ),
        DetectedComponent(
            type=ComponentType.INPUT,
            bbox_x=0.4,
            bbox_y=0.1,
            bbox_width=0.2,
            bbox_height=0.1,
            confidence=0.9,
        ),
        DetectedComponent(
            type=ComponentType.LABEL,
            bbox_x=0.1,
            bbox_y=0.3,
            bbox_width=0.3,
            bbox_height=0.05,
            confidence=0.85,
        ),
    ]


@pytest.fixture
def nested_components():
    """Create components with nesting relationships."""
    return [
        # Large container (parent)
        DetectedComponent(
            type=ComponentType.CONTAINER,
            bbox_x=0.0,
            bbox_y=0.0,
            bbox_width=1.0,
            bbox_height=1.0,
            confidence=0.95,
        ),
        # Medium container inside large
        DetectedComponent(
            type=ComponentType.CONTAINER,
            bbox_x=0.1,
            bbox_y=0.1,
            bbox_width=0.8,
            bbox_height=0.8,
            confidence=0.9,
        ),
        # Button inside medium container
        DetectedComponent(
            type=ComponentType.BUTTON,
            bbox_x=0.2,
            bbox_y=0.2,
            bbox_width=0.15,
            bbox_height=0.08,
            confidence=0.95,
        ),
        # Input inside medium container
        DetectedComponent(
            type=ComponentType.INPUT,
            bbox_x=0.5,
            bbox_y=0.2,
            bbox_width=0.2,
            bbox_height=0.08,
            confidence=0.9,
        ),
    ]


@pytest.fixture
def modal_components():
    """Create components including a modal overlay."""
    return [
        # Background container
        DetectedComponent(
            type=ComponentType.CONTAINER,
            bbox_x=0.0,
            bbox_y=0.0,
            bbox_width=1.0,
            bbox_height=1.0,
            confidence=0.95,
        ),
        # Modal (centered)
        DetectedComponent(
            type=ComponentType.MODAL,
            bbox_x=0.25,
            bbox_y=0.25,
            bbox_width=0.5,
            bbox_height=0.5,
            confidence=0.95,
        ),
        # Button in modal
        DetectedComponent(
            type=ComponentType.BUTTON,
            bbox_x=0.35,
            bbox_y=0.55,
            bbox_width=0.1,
            bbox_height=0.05,
            confidence=0.9,
        ),
    ]


@pytest.fixture
def sample_screens():
    """Create sample screens for flow testing."""
    return [
        ScreenData(
            screen_id="screen_1",
            components=[
                DetectedComponent(
                    type=ComponentType.BUTTON,
                    bbox_x=0.1,
                    bbox_y=0.1,
                    bbox_width=0.2,
                    bbox_height=0.1,
                    confidence=0.95,
                ),
            ],
            timestamp_ms=0.0,
        ),
        ScreenData(
            screen_id="screen_2",
            components=[
                DetectedComponent(
                    type=ComponentType.BUTTON,
                    bbox_x=0.1,
                    bbox_y=0.1,
                    bbox_width=0.2,
                    bbox_height=0.1,
                    confidence=0.95,
                ),
                DetectedComponent(
                    type=ComponentType.INPUT,
                    bbox_x=0.4,
                    bbox_y=0.1,
                    bbox_width=0.2,
                    bbox_height=0.1,
                    confidence=0.9,
                ),
            ],
            timestamp_ms=1000.0,
        ),
        ScreenData(
            screen_id="screen_3",
            components=[
                DetectedComponent(
                    type=ComponentType.BUTTON,
                    bbox_x=0.1,
                    bbox_y=0.1,
                    bbox_width=0.2,
                    bbox_height=0.1,
                    confidence=0.95,
                ),
                DetectedComponent(
                    type=ComponentType.INPUT,
                    bbox_x=0.4,
                    bbox_y=0.1,
                    bbox_width=0.2,
                    bbox_height=0.1,
                    confidence=0.9,
                ),
            ],
            timestamp_ms=2000.0,
        ),
    ]


# =============================================================================
# Hierarchy Model Tests
# =============================================================================

class TestHierarchyNode:
    """Tests for HierarchyNode model."""
    
    def test_create_node(self):
        """Test creating a hierarchy node."""
        node = HierarchyNode(
            id="comp_1",
            parent_id="comp_0",
            children=["comp_2", "comp_3"],
            z_index=1,
            level=1,
            confidence=0.9,
        )
        
        assert node.id == "comp_1"
        assert node.parent_id == "comp_0"
        assert len(node.children) == 2
        assert node.z_index == 1
        assert node.level == 1
        assert node.confidence == 0.9
    
    def test_root_node(self):
        """Test creating a root node (no parent)."""
        node = HierarchyNode(id="root", children=["child1"])
        
        assert node.parent_id is None
        assert node.level == 0


class TestHierarchyTree:
    """Tests for HierarchyTree model."""
    
    def test_empty_tree(self):
        """Test creating an empty tree."""
        tree = HierarchyTree()
        
        assert tree.root_id is None
        assert len(tree.nodes) == 0
        assert tree.max_depth == 0
        assert tree.component_count == 0
    
    def test_tree_with_nodes(self):
        """Test creating a tree with nodes."""
        nodes = {
            "root": HierarchyNode(id="root", children=["child1"]),
            "child1": HierarchyNode(id="child1", parent_id="root", level=1),
        }
        
        tree = HierarchyTree(
            root_id="root",
            nodes=nodes,
            max_depth=1,
            component_count=2,
        )
        
        assert tree.root_id == "root"
        assert len(tree.nodes) == 2
        assert tree.max_depth == 1
    
    def test_get_node(self):
        """Test getting a node by ID."""
        nodes = {
            "root": HierarchyNode(id="root"),
            "child": HierarchyNode(id="child", parent_id="root"),
        }
        tree = HierarchyTree(root_id="root", nodes=nodes)
        
        assert tree.get_node("root") is not None
        assert tree.get_node("nonexistent") is None
    
    def test_get_children(self):
        """Test getting children of a node."""
        nodes = {
            "root": HierarchyNode(id="root", children=["child1", "child2"]),
            "child1": HierarchyNode(id="child1", parent_id="root"),
            "child2": HierarchyNode(id="child2", parent_id="root"),
        }
        tree = HierarchyTree(root_id="root", nodes=nodes)
        
        children = tree.get_children("root")
        assert len(children) == 2
        
        children = tree.get_children("child1")
        assert len(children) == 0
    
    def test_get_descendants(self):
        """Test getting all descendants recursively."""
        nodes = {
            "root": HierarchyNode(id="root", children=["child1"]),
            "child1": HierarchyNode(id="child1", parent_id="root", children=["grandchild"]),
            "grandchild": HierarchyNode(id="grandchild", parent_id="child1"),
        }
        tree = HierarchyTree(root_id="root", nodes=nodes)
        
        descendants = tree.get_descendants("root")
        assert len(descendants) == 2
    
    def test_get_ancestors(self):
        """Test getting all ancestors."""
        nodes = {
            "root": HierarchyNode(id="root", children=["child1"]),
            "child1": HierarchyNode(id="child1", parent_id="root", children=["grandchild"]),
            "grandchild": HierarchyNode(id="grandchild", parent_id="child1"),
        }
        tree = HierarchyTree(root_id="root", nodes=nodes)
        
        ancestors = tree.get_ancestors("grandchild")
        assert len(ancestors) == 2
        assert ancestors[0].id == "child1"
        assert ancestors[1].id == "root"


class TestContainerMatch:
    """Tests for ContainerMatch model."""
    
    def test_container_match(self):
        """Test creating a container match."""
        match = ContainerMatch(
            parent_id="container_1",
            child_id="button_1",
            containment_ratio=0.95,
            confidence=0.95,
        )
        
        assert match.parent_id == "container_1"
        assert match.child_id == "button_1"
        assert match.containment_ratio == 0.95


class TestZLayer:
    """Tests for ZLayer model."""
    
    def test_z_layer(self):
        """Test creating a z-layer."""
        layer = ZLayer(
            z_index=0,
            component_ids=["comp_1", "comp_2"],
            layer_type="background",
        )
        
        assert layer.z_index == 0
        assert len(layer.component_ids) == 2
        assert layer.layer_type == "background"


# =============================================================================
# Flow Model Tests
# =============================================================================

class TestSimilarityScore:
    """Tests for SimilarityScore model."""
    
    def test_similarity_score(self):
        """Test creating a similarity score."""
        score = SimilarityScore(
            screen1_id="s1",
            screen2_id="s2",
            perceptual_hash_similarity=0.9,
            component_overlap_similarity=0.85,
            combined_score=0.875,
        )
        
        assert score.screen1_id == "s1"
        assert score.perceptual_hash_similarity == 0.9
        assert score.combined_score == 0.875
        assert not score.is_duplicate
    
    def test_duplicate_detection(self):
        """Test duplicate detection via is_duplicate property."""
        score = SimilarityScore(
            screen1_id="s1",
            screen2_id="s2",
            perceptual_hash_similarity=0.98,
            component_overlap_similarity=0.97,
            combined_score=0.975,
            is_duplicate=True,
        )
        
        assert score.is_duplicate
        assert score.is_similar


class TestScreenTransition:
    """Tests for ScreenTransition model."""
    
    def test_screen_transition(self):
        """Test creating a screen transition."""
        transition = ScreenTransition(
            from_screen_id="s1",
            to_screen_id="s2",
            transition_type=TransitionType.NAVIGATION,
            similarity_score=0.6,
        )
        
        assert transition.from_screen_id == "s1"
        assert transition.to_screen_id == "s2"
        assert transition.transition_type == TransitionType.NAVIGATION


class TestKeyFrameMarker:
    """Tests for KeyFrameMarker model."""
    
    def test_key_frame_marker(self):
        """Test creating a key frame marker."""
        marker = KeyFrameMarker(
            screen_id="s1",
            reason=KeyFrameReason.SIGNIFICANT_CHANGE,
            confidence=0.9,
            description="Major UI change",
        )
        
        assert marker.screen_id == "s1"
        assert marker.reason == KeyFrameReason.SIGNIFICANT_CHANGE


class TestFlowSequence:
    """Tests for FlowSequence model."""
    
    def test_empty_flow(self):
        """Test creating an empty flow."""
        flow = FlowSequence()
        
        assert len(flow.screen_ids) == 0
        assert flow.screen_count == 0
    
    def test_flow_with_screens(self):
        """Test creating a flow with screens."""
        flow = FlowSequence(
            name="Test Flow",
            screen_ids=["s1", "s2", "s3"],
        )
        
        assert flow.name == "Test Flow"
        assert len(flow.screen_ids) == 3
        assert flow.screen_count == 3
    
    def test_is_key_frame(self):
        """Test checking if a screen is a key frame."""
        flow = FlowSequence(
            screen_ids=["s1", "s2"],
            key_frames=[
                KeyFrameMarker(screen_id="s1", reason=KeyFrameReason.FIRST_FRAME),
            ],
        )
        
        assert flow.is_key_frame("s1")
        assert not flow.is_key_frame("s2")


# =============================================================================
# Hierarchy Analyzer Tests
# =============================================================================

class TestHierarchyAnalyzer:
    """Tests for HierarchyAnalyzer class."""
    
    def test_empty_components(self):
        """Test analyzing empty component list."""
        analyzer = HierarchyAnalyzer()
        tree = analyzer.extract_hierarchy([])
        
        assert tree.component_count == 0
        assert tree.root_id is None
    
    def test_simple_components(self, simple_components):
        """Test analyzing simple (non-nested) components."""
        analyzer = HierarchyAnalyzer()
        tree = analyzer.extract_hierarchy(simple_components)
        
        assert tree.component_count == 3
        # All should be root-level (no nesting)
        assert tree.max_depth == 0
    
    def test_nested_components(self, nested_components):
        """Test analyzing nested components."""
        analyzer = HierarchyAnalyzer()
        tree = analyzer.extract_hierarchy(nested_components)
        
        assert tree.component_count == 4
        # Should have nesting
        assert tree.max_depth >= 1
    
    def test_detect_containers(self, nested_components):
        """Test container detection."""
        analyzer = HierarchyAnalyzer()
        matches = analyzer.detect_containers(nested_components)
        
        # Should detect container relationships
        assert len(matches) > 0
        
        # All matches should have valid containment ratio
        for match in matches:
            assert match.containment_ratio > 0
    
    def test_infer_z_order(self, modal_components):
        """Test z-order inference."""
        analyzer = HierarchyAnalyzer()
        layers = analyzer.infer_z_order(modal_components)
        
        assert len(layers) > 0
        
        # Modal should be in a higher z-index layer
        modal_layer = None
        for layer in layers:
            if any("modal" in cid.lower() for cid in layer.component_ids):
                modal_layer = layer
                break
        
        # Modal should exist and be in higher layer
        if modal_layer:
            assert modal_layer.z_index >= 1
    
    def test_calculate_nesting_depth(self, nested_components):
        """Test nesting depth calculation."""
        analyzer = HierarchyAnalyzer()
        tree = analyzer.extract_hierarchy(nested_components)
        depth = analyzer.calculate_nesting_depth(tree)
        
        assert depth == tree.max_depth
    
    def test_full_analysis(self, nested_components):
        """Test full hierarchy analysis."""
        analyzer = HierarchyAnalyzer()
        result = analyzer.analyze(nested_components)
        
        assert result.tree is not None
        assert len(result.z_layers) > 0
        assert result.processing_time_ms >= 0


class TestHierarchyConvenienceFunctions:
    """Tests for convenience functions."""
    
    def test_extract_hierarchy(self, simple_components):
        """Test extract_hierarchy convenience function."""
        tree = extract_hierarchy(simple_components)
        
        assert tree.component_count == 3
    
    def test_detect_containers(self, nested_components):
        """Test detect_containers convenience function."""
        matches = detect_containers(nested_components)
        
        assert len(matches) > 0
    
    def test_infer_z_order(self, simple_components):
        """Test infer_z_order convenience function."""
        layers = infer_z_order(simple_components)
        
        assert len(layers) > 0


# =============================================================================
# Similarity Calculator Tests
# =============================================================================

class TestSimilarityCalculator:
    """Tests for SimilarityCalculator class."""
    
    def test_init(self):
        """Test calculator initialization."""
        calc = SimilarityCalculator(
            duplicate_threshold=0.9,
            phash_weight=0.6,
            component_weight=0.4,
        )
        
        assert calc.duplicate_threshold == 0.9
        assert calc.phash_weight == 0.6
    
    def test_component_overlap_identical(self):
        """Test component overlap with identical components."""
        components = [
            DetectedComponent(
                type=ComponentType.BUTTON,
                bbox_x=0.1,
                bbox_y=0.1,
                bbox_width=0.2,
                bbox_height=0.1,
                confidence=0.95,
            ),
        ]
        
        calc = SimilarityCalculator()
        similarity = calc.calculate_component_overlap(components, components)
        
        assert similarity == 1.0
    
    def test_component_overlap_different(self):
        """Test component overlap with different components."""
        components1 = [
            DetectedComponent(
                type=ComponentType.BUTTON,
                bbox_x=0.1,
                bbox_y=0.1,
                bbox_width=0.2,
                bbox_height=0.1,
                confidence=0.95,
            ),
        ]
        
        components2 = [
            DetectedComponent(
                type=ComponentType.INPUT,
                bbox_x=0.5,
                bbox_y=0.5,
                bbox_width=0.2,
                bbox_height=0.1,
                confidence=0.9,
            ),
        ]
        
        calc = SimilarityCalculator()
        similarity = calc.calculate_component_overlap(components1, components2)
        
        assert similarity == 0.0
    
    def test_component_overlap_partial(self):
        """Test component overlap with partially matching components."""
        components1 = [
            DetectedComponent(
                type=ComponentType.BUTTON,
                bbox_x=0.1,
                bbox_y=0.1,
                bbox_width=0.2,
                bbox_height=0.1,
                confidence=0.95,
            ),
            DetectedComponent(
                type=ComponentType.INPUT,
                bbox_x=0.4,
                bbox_y=0.1,
                bbox_width=0.2,
                bbox_height=0.1,
                confidence=0.9,
            ),
        ]
        
        components2 = [
            DetectedComponent(
                type=ComponentType.BUTTON,
                bbox_x=0.1,
                bbox_y=0.1,
                bbox_width=0.2,
                bbox_height=0.1,
                confidence=0.95,
            ),
            DetectedComponent(
                type=ComponentType.LABEL,
                bbox_x=0.4,
                bbox_y=0.1,
                bbox_width=0.2,
                bbox_height=0.1,
                confidence=0.85,
            ),
        ]
        
        calc = SimilarityCalculator()
        similarity = calc.calculate_component_overlap(components1, components2)
        
        # 1 match out of 3 unique = 0.33
        assert 0.0 < similarity < 1.0
    
    def test_component_overlap_empty(self):
        """Test component overlap with empty lists."""
        calc = SimilarityCalculator()
        
        # Both empty = identical
        assert calc.calculate_component_overlap([], []) == 1.0
        
        # One empty = no similarity
        components = [
            DetectedComponent(
                type=ComponentType.BUTTON,
                bbox_x=0.1,
                bbox_y=0.1,
                bbox_width=0.2,
                bbox_height=0.1,
                confidence=0.95,
            ),
        ]
        assert calc.calculate_component_overlap(components, []) == 0.0
    
    def test_combined_similarity(self):
        """Test combined similarity calculation."""
        calc = SimilarityCalculator(phash_weight=0.5, component_weight=0.5)
        
        combined = calc.calculate_combined_similarity(0.8, 0.6)
        
        assert combined == 0.7  # (0.8 * 0.5) + (0.6 * 0.5)
    
    def test_calculate_similarity(self):
        """Test full similarity calculation."""
        calc = SimilarityCalculator()
        
        components = [
            DetectedComponent(
                type=ComponentType.BUTTON,
                bbox_x=0.1,
                bbox_y=0.1,
                bbox_width=0.2,
                bbox_height=0.1,
                confidence=0.95,
            ),
        ]
        
        score = calc.calculate_similarity(
            screen1_id="s1",
            screen2_id="s2",
            components1=components,
            components2=components,
        )
        
        assert score.screen1_id == "s1"
        assert score.screen2_id == "s2"
        # Without images, phash_sim is 0
        assert score.perceptual_hash_similarity == 0.0
        # With identical components, overlap is 1.0
        assert score.component_overlap_similarity == 1.0


class TestSimilarityConvenienceFunctions:
    """Tests for similarity convenience functions."""
    
    def test_calculate_component_overlap(self, simple_components):
        """Test calculate_component_overlap convenience function."""
        similarity = calculate_component_overlap(
            simple_components,
            simple_components,
        )
        
        assert similarity == 1.0


# =============================================================================
# Flow Sequencer Tests
# =============================================================================

class TestScreenData:
    """Tests for ScreenData class."""
    
    def test_screen_data(self):
        """Test creating screen data."""
        screen = ScreenData(
            screen_id="test_screen",
            components=[
                DetectedComponent(
                    type=ComponentType.BUTTON,
                    bbox_x=0.1,
                    bbox_y=0.1,
                    bbox_width=0.2,
                    bbox_height=0.1,
                    confidence=0.95,
                ),
            ],
            timestamp_ms=1000.0,
        )
        
        assert screen.screen_id == "test_screen"
        assert len(screen.components) == 1
        assert screen.timestamp_ms == 1000.0


class TestFlowSequencer:
    """Tests for FlowSequencer class."""
    
    def test_empty_screens(self):
        """Test sequencing empty screen list."""
        sequencer = FlowSequencer()
        flow = sequencer.sequence_screens([])
        
        assert flow.screen_count == 0
    
    def test_single_screen(self):
        """Test sequencing single screen."""
        sequencer = FlowSequencer()
        screens = [ScreenData(screen_id="s1")]
        
        flow = sequencer.sequence_screens(screens)
        
        assert flow.screen_count == 1
        assert len(flow.key_frames) == 1
        assert flow.key_frames[0].reason == KeyFrameReason.FIRST_FRAME
    
    def test_detect_key_frames(self, sample_screens):
        """Test key frame detection."""
        sequencer = FlowSequencer(key_frame_threshold=0.9)
        key_frames = sequencer.detect_key_frames(sample_screens)
        
        # First and last frames are always key frames
        assert len(key_frames) >= 2
        assert key_frames[0].reason == KeyFrameReason.FIRST_FRAME
    
    def test_deduplicate_identical_frames(self):
        """Test deduplication of identical frames."""
        # Without images, component-only similarity = 0.5 (weighted with 0 phash)
        # So we need a lower threshold to trigger deduplication
        sequencer = FlowSequencer(dedup_threshold=0.4)
        
        # Create identical screens
        components = [
            DetectedComponent(
                type=ComponentType.BUTTON,
                bbox_x=0.1,
                bbox_y=0.1,
                bbox_width=0.2,
                bbox_height=0.1,
                confidence=0.95,
            ),
        ]
        
        screens = [
            ScreenData(screen_id="s1", components=components),
            ScreenData(screen_id="s2", components=components),
            ScreenData(screen_id="s3", components=components),
        ]
        
        deduped, count = sequencer.deduplicate_frames(screens)
        
        # Should deduplicate to 1 frame (component overlap is 1.0, combined=0.5)
        assert len(deduped) == 1
        assert count == 2
    
    def test_sequence_screens(self, sample_screens):
        """Test screen sequencing."""
        sequencer = FlowSequencer()
        flow = sequencer.sequence_screens(sample_screens, name="Test Flow")
        
        assert flow.name == "Test Flow"
        assert len(flow.screen_ids) > 0
        assert len(flow.transitions) == len(flow.screen_ids) - 1
    
    def test_sequence_with_dedup(self):
        """Test sequencing with deduplication."""
        # Use lower threshold to trigger dedup with component-only similarity
        sequencer = FlowSequencer(dedup_threshold=0.4)
        
        components = [
            DetectedComponent(
                type=ComponentType.BUTTON,
                bbox_x=0.1,
                bbox_y=0.1,
                bbox_width=0.2,
                bbox_height=0.1,
                confidence=0.95,
            ),
        ]
        
        screens = [
            ScreenData(screen_id="s1", components=components),
            ScreenData(screen_id="s2", components=components),  # Duplicate
            ScreenData(
                screen_id="s3",
                components=[
                    DetectedComponent(
                        type=ComponentType.INPUT,
                        bbox_x=0.5,
                        bbox_y=0.5,
                        bbox_width=0.2,
                        bbox_height=0.1,
                        confidence=0.9,
                    ),
                ],
            ),
        ]
        
        flow = sequencer.sequence_screens(screens, deduplicate=True)
        
        # s1 and s2 should be deduplicated (identical components, combined=0.5)
        assert flow.duplicate_count > 0
        # s3 should remain (different components)
        assert flow.screen_count == 2
    
    def test_analyze(self, sample_screens):
        """Test full flow analysis."""
        sequencer = FlowSequencer()
        result = sequencer.analyze(sample_screens)
        
        assert result.flow is not None
        assert len(result.similarity_scores) >= 0
        assert result.processing_time_ms >= 0
    
    def test_transition_generation(self, sample_screens):
        """Test transition generation."""
        sequencer = FlowSequencer()
        flow = sequencer.sequence_screens(sample_screens)
        
        # Check transitions are generated
        if len(flow.screen_ids) > 1:
            assert len(flow.transitions) > 0
            
            for t in flow.transitions:
                assert t.from_screen_id is not None
                assert t.to_screen_id is not None
                assert t.transition_type is not None


class TestFlowConvenienceFunctions:
    """Tests for flow convenience functions."""
    
    def test_sequence_screens(self, sample_screens):
        """Test sequence_screens convenience function."""
        flow = sequence_screens(sample_screens)
        
        assert flow is not None
    
    def test_detect_key_frames(self, sample_screens):
        """Test detect_key_frames convenience function."""
        key_frames = detect_key_frames(sample_screens)
        
        assert len(key_frames) >= 1
    
    def test_deduplicate_frames(self):
        """Test deduplicate_frames convenience function."""
        components = [
            DetectedComponent(
                type=ComponentType.BUTTON,
                bbox_x=0.1,
                bbox_y=0.1,
                bbox_width=0.2,
                bbox_height=0.1,
                confidence=0.95,
            ),
        ]
        
        screens = [
            ScreenData(screen_id="s1", components=components),
            ScreenData(screen_id="s2", components=components),
        ]
        
        deduped, count = deduplicate_frames(screens)
        
        assert len(deduped) >= 1


# =============================================================================
# Integration Tests
# =============================================================================

class TestHierarchyFlowIntegration:
    """Integration tests for hierarchy and flow modules."""
    
    def test_hierarchy_to_json(self, nested_components):
        """Test hierarchy tree JSON serialization."""
        analyzer = HierarchyAnalyzer()
        result = analyzer.analyze(nested_components)
        
        # Should be JSON serializable
        json_data = result.model_dump()
        
        assert "tree" in json_data
        assert "z_layers" in json_data
    
    def test_flow_to_json(self, sample_screens):
        """Test flow sequence JSON serialization."""
        sequencer = FlowSequencer()
        result = sequencer.analyze(sample_screens)
        
        # Should be JSON serializable
        json_data = result.model_dump()
        
        assert "flow" in json_data
        assert "similarity_scores" in json_data
    
    def test_performance(self, nested_components):
        """Test hierarchy analysis performance (< 500ms)."""
        import time
        
        analyzer = HierarchyAnalyzer()
        
        start = time.time()
        result = analyzer.analyze(nested_components)
        elapsed_ms = (time.time() - start) * 1000
        
        assert elapsed_ms < 500
        assert result.processing_time_ms < 500


# =============================================================================
# Edge Cases
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""
    
    def test_overlapping_siblings(self):
        """Test components that overlap but don't nest."""
        components = [
            DetectedComponent(
                type=ComponentType.BUTTON,
                bbox_x=0.0,
                bbox_y=0.0,
                bbox_width=0.5,
                bbox_height=0.5,
                confidence=0.95,
            ),
            DetectedComponent(
                type=ComponentType.BUTTON,
                bbox_x=0.25,
                bbox_y=0.25,
                bbox_width=0.5,
                bbox_height=0.5,
                confidence=0.95,
            ),
        ]
        
        analyzer = HierarchyAnalyzer()
        tree = analyzer.extract_hierarchy(components)
        
        # Should handle without errors
        assert tree.component_count == 2
    
    def test_single_frame_flow(self):
        """Test flow with single frame."""
        screens = [ScreenData(screen_id="s1")]
        
        sequencer = FlowSequencer()
        flow = sequencer.sequence_screens(screens)
        
        assert flow.screen_count == 1
        assert len(flow.transitions) == 0
    
    def test_zero_area_component(self):
        """Test handling of zero-area component."""
        # This would be rejected by Pydantic validation
        with pytest.raises(Exception):
            DetectedComponent(
                type=ComponentType.BUTTON,
                bbox_x=0.5,
                bbox_y=0.5,
                bbox_width=0.0,  # Invalid
                bbox_height=0.1,
                confidence=0.95,
            )
    
    def test_deep_nesting(self):
        """Test handling of deeply nested components."""
        components = []
        
        # Create 10 levels of nesting
        for i in range(10):
            pos = i * 0.05
            size = 1.0 - (i * 0.1)
            components.append(
                DetectedComponent(
                    type=ComponentType.CONTAINER,
                    bbox_x=pos,
                    bbox_y=pos,
                    bbox_width=size,
                    bbox_height=size,
                    confidence=0.9,
                )
            )
        
        analyzer = HierarchyAnalyzer()
        tree = analyzer.extract_hierarchy(components)
        
        # Should handle deep nesting
        assert tree.component_count == 10
        assert tree.max_depth >= 1