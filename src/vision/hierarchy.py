"""
Hierarchy extraction for UI component trees.

Provides container detection, z-order inference, and hierarchy tree building.
"""

import time
from typing import Optional
from uuid import uuid4

from .models import DetectedComponent, ComponentType
from .hierarchy_models import (
    HierarchyNode,
    HierarchyTree,
    ContainerMatch,
    ZLayer,
    NestingLevel,
    HierarchyAnalysisResult,
)


# Default thresholds
DEFAULT_AREA_RATIO_THRESHOLD = 0.1  # Minimum child/parent area ratio
DEFAULT_CONTAINMENT_THRESHOLD = 0.9  # Minimum overlap for containment


class HierarchyAnalyzer:
    """Analyze component hierarchy from detected components."""
    
    def __init__(
        self,
        area_ratio_threshold: float = DEFAULT_AREA_RATIO_THRESHOLD,
        containment_threshold: float = DEFAULT_CONTAINMENT_THRESHOLD,
    ):
        """Initialize hierarchy analyzer.
        
        Args:
            area_ratio_threshold: Minimum ratio of child area to parent area
            containment_threshold: Minimum overlap ratio for containment
        """
        self.area_ratio_threshold = area_ratio_threshold
        self.containment_threshold = containment_threshold
    
    def detect_containers(
        self,
        components: list[DetectedComponent],
    ) -> list[ContainerMatch]:
        """Detect parent-child container relationships.
        
        Uses bounding box containment algorithm:
        - For each component A, check if it contains component B
        - If A.bbox fully contains B.bbox and B.area/A.area > threshold
        - Then A is a potential parent of B
        - Resolve multiple parents by selecting smallest container
        
        Args:
            components: List of detected components
        
        Returns:
            List of ContainerMatch objects representing relationships
        """
        if not components:
            return []
        
        # Assign IDs if not present
        component_ids = {}
        for i, c in enumerate(components):
            component_ids[i] = f"comp_{i}"
        
        # Find all potential container relationships
        potential_parents: dict[int, list[tuple[int, float]]] = {}
        
        for i, comp_a in enumerate(components):
            for j, comp_b in enumerate(components):
                if i == j:
                    continue
                
                # Check if A contains B
                containment = self._calculate_containment(comp_a, comp_b)
                if containment >= self.containment_threshold:
                    # Check area ratio
                    area_a = self._calculate_area(comp_a)
                    area_b = self._calculate_area(comp_b)
                    
                    if area_a > 0:
                        area_ratio = area_b / area_a
                        if area_ratio >= self.area_ratio_threshold:
                            if j not in potential_parents:
                                potential_parents[j] = []
                            potential_parents[j].append((i, containment))
        
        # Resolve multiple parents (smallest containing parent wins)
        container_matches = []
        for child_idx, parents in potential_parents.items():
            if not parents:
                continue
            
            # Sort by parent area (smallest first)
            parents_sorted = sorted(
                parents,
                key=lambda p: self._calculate_area(components[p[0]])
            )
            
            best_parent_idx, containment = parents_sorted[0]
            
            container_matches.append(ContainerMatch(
                parent_id=component_ids[best_parent_idx],
                child_id=component_ids[child_idx],
                containment_ratio=min(containment, 1.0),
                confidence=min(containment, 1.0),
            ))
        
        return container_matches
    
    def infer_z_order(
        self,
        components: list[DetectedComponent],
    ) -> list[ZLayer]:
        """Infer z-order layers from component positions and sizes.
        
        Uses heuristics:
        - Larger components → lower z-index (background)
        - Centered components → higher z-index (modals/overlays)
        - Component type influences layer type
        
        Args:
            components: List of detected components
        
        Returns:
            List of ZLayer objects sorted by z_index
        """
        if not components:
            return []
        
        # Assign IDs
        component_ids = {}
        for i, c in enumerate(components):
            component_ids[i] = f"comp_{i}"
        
        # Calculate z-scores for each component
        z_scores = []
        for i, comp in enumerate(components):
            score = self._calculate_z_score(comp)
            z_scores.append((i, score))
        
        # Sort by z-score and assign layers
        z_scores.sort(key=lambda x: x[1])
        
        # Group into discrete layers
        layers: dict[int, list[str]] = {}
        for i, (comp_idx, score) in enumerate(z_scores):
            layer_idx = min(int(score / 25), 3)  # 0-3 layers
            if layer_idx not in layers:
                layers[layer_idx] = []
            layers[layer_idx].append(component_ids[comp_idx])
        
        # Create ZLayer objects
        z_layers = []
        layer_types = ["background", "content", "overlay", "modal"]
        
        for layer_idx in sorted(layers.keys()):
            component_ids_in_layer = layers[layer_idx]
            
            # Infer layer type from component types
            layer_type = self._infer_layer_type(
                [components[i] for i in range(len(components)) 
                 if f"comp_{i}" in component_ids_in_layer]
            )
            
            z_layers.append(ZLayer(
                z_index=layer_idx,
                component_ids=component_ids_in_layer,
                layer_type=layer_type or layer_types[layer_idx] if layer_idx < len(layer_types) else "content",
            ))
        
        return z_layers
    
    def extract_hierarchy(
        self,
        components: list[DetectedComponent],
    ) -> HierarchyTree:
        """Extract complete hierarchy tree from components.
        
        Args:
            components: List of detected components
        
        Returns:
            HierarchyTree with all nodes and relationships
        """
        if not components:
            return HierarchyTree()
        
        start_time = time.time()
        
        # Assign IDs
        component_ids = {}
        id_to_component = {}
        for i, c in enumerate(components):
            comp_id = f"comp_{i}"
            component_ids[i] = comp_id
            id_to_component[comp_id] = c
        
        # Detect container relationships
        container_matches = self.detect_containers(components)
        
        # Build parent-child mapping
        children_map: dict[str, list[str]] = {cid: [] for cid in component_ids.values()}
        parent_map: dict[str, str] = {}
        
        for match in container_matches:
            parent_id = match.parent_id
            child_id = match.child_id
            
            # Check for conflicting parent
            if child_id in parent_map:
                # Keep the smaller parent (already resolved in detect_containers)
                continue
            
            parent_map[child_id] = parent_id
            if parent_id in children_map:
                children_map[parent_id].append(child_id)
        
        # Calculate levels
        levels = self._calculate_levels(component_ids.values(), parent_map)
        
        # Infer z-order
        z_layers = self.infer_z_order(components)
        z_index_map = {}
        for layer in z_layers:
            for comp_id in layer.component_ids:
                z_index_map[comp_id] = layer.z_index
        
        # Create HierarchyNodes
        nodes = {}
        for comp_id in component_ids.values():
            parent_id = parent_map.get(comp_id)
            children = children_map.get(comp_id, [])
            level = levels.get(comp_id, 0)
            z_index = z_index_map.get(comp_id, 0)
            
            # Calculate confidence
            confidence = 1.0
            if comp_id in parent_map:
                # Confidence based on containment quality
                for match in container_matches:
                    if match.child_id == comp_id:
                        confidence = match.confidence
                        break
            
            nodes[comp_id] = HierarchyNode(
                id=comp_id,
                parent_id=parent_id,
                children=children,
                z_index=z_index,
                level=level,
                confidence=confidence,
            )
        
        # Find root (component with no parent, or largest container)
        root_id = None
        root_candidates = [cid for cid in component_ids.values() if cid not in parent_map]
        
        if root_candidates:
            if len(root_candidates) == 1:
                root_id = root_candidates[0]
            else:
                # Select largest component as root
                largest_area = 0
                for cid in root_candidates:
                    comp = id_to_component[cid]
                    area = self._calculate_area(comp)
                    if area > largest_area:
                        largest_area = area
                        root_id = cid
        
        # Calculate max depth
        max_depth = max(levels.values()) if levels else 0
        
        return HierarchyTree(
            root_id=root_id,
            nodes=nodes,
            max_depth=max_depth,
            component_count=len(components),
        )
    
    def calculate_nesting_depth(
        self,
        tree: HierarchyTree,
    ) -> int:
        """Calculate maximum nesting depth of hierarchy tree.
        
        Args:
            tree: HierarchyTree to analyze
        
        Returns:
            Maximum nesting depth (0 = flat, 1 = one level of nesting, etc.)
        """
        return tree.max_depth
    
    def analyze(
        self,
        components: list[DetectedComponent],
    ) -> HierarchyAnalysisResult:
        """Perform complete hierarchy analysis.
        
        Args:
            components: List of detected components
        
        Returns:
            HierarchyAnalysisResult with all analysis data
        """
        start_time = time.time()
        
        # Extract hierarchy
        tree = self.extract_hierarchy(components)
        
        # Detect containers (already done, but get for result)
        container_matches = self.detect_containers(components)
        
        # Infer z-order
        z_layers = self.infer_z_order(components)
        
        # Find orphans (components with no parent and no children)
        orphan_ids = [
            node.id for node in tree.nodes.values()
            if node.parent_id is None and not node.children and tree.root_id != node.id
        ]
        
        processing_time = (time.time() - start_time) * 1000
        
        return HierarchyAnalysisResult(
            tree=tree,
            z_layers=z_layers,
            container_matches=container_matches,
            orphan_ids=orphan_ids,
            processing_time_ms=processing_time,
        )
    
    def _calculate_area(self, component: DetectedComponent) -> float:
        """Calculate bounding box area."""
        return component.bbox_width * component.bbox_height
    
    def _calculate_containment(
        self,
        parent: DetectedComponent,
        child: DetectedComponent,
    ) -> float:
        """Calculate how much of child is contained in parent.
        
        Returns:
            Ratio of child area inside parent (0.0-1.0)
        """
        # Calculate intersection
        parent_left = parent.bbox_x
        parent_right = parent.bbox_x + parent.bbox_width
        parent_top = parent.bbox_y
        parent_bottom = parent.bbox_y + parent.bbox_height
        
        child_left = child.bbox_x
        child_right = child.bbox_x + child.bbox_width
        child_top = child.bbox_y
        child_bottom = child.bbox_y + child.bbox_height
        
        # Intersection
        inter_left = max(parent_left, child_left)
        inter_right = min(parent_right, child_right)
        inter_top = max(parent_top, child_top)
        inter_bottom = min(parent_bottom, child_bottom)
        
        if inter_right <= inter_left or inter_bottom <= inter_top:
            return 0.0  # No intersection
        
        inter_area = (inter_right - inter_left) * (inter_bottom - inter_top)
        child_area = self._calculate_area(child)
        
        return inter_area / child_area if child_area > 0 else 0.0
    
    def _calculate_z_score(self, component: DetectedComponent) -> float:
        """Calculate z-score for layering inference.
        
        Higher score = higher z-index (foreground)
        Lower score = lower z-index (background)
        """
        score = 50.0  # Base score
        
        # Size factor: larger = lower (background)
        area = self._calculate_area(component)
        if area > 0.5:  # Takes up more than half the screen
            score -= 20
        elif area > 0.25:
            score -= 10
        elif area < 0.05:  # Small elements
            score += 10
        
        # Position factor: centered = higher (modals)
        center_x = component.bbox_x + component.bbox_width / 2
        center_y = component.bbox_y + component.bbox_height / 2
        
        # Distance from center (0.5, 0.5)
        dist_from_center = (
            (center_x - 0.5) ** 2 + (center_y - 0.5) ** 2
        ) ** 0.5
        
        if dist_from_center < 0.2:  # Close to center
            score += 15
        
        # Component type factor
        if component.type == ComponentType.MODAL:
            score += 30
        elif component.type == ComponentType.BUTTON:
            score += 10
        elif component.type == ComponentType.INPUT:
            score += 5
        elif component.type == ComponentType.HEADER:
            score -= 5
        elif component.type == ComponentType.FOOTER:
            score -= 5
        elif component.type == ComponentType.CONTAINER:
            score -= 15
        elif component.type == ComponentType.NAVIGATION:
            score -= 10
        
        return max(0, min(100, score))
    
    def _infer_layer_type(
        self,
        components: list[DetectedComponent],
    ) -> Optional[str]:
        """Infer layer type from component types."""
        if not components:
            return None
        
        type_counts: dict[ComponentType, int] = {}
        for c in components:
            type_counts[c.type] = type_counts.get(c.type, 0) + 1
        
        # Check for modal
        if ComponentType.MODAL in type_counts:
            return "modal"
        
        # Check for navigation
        if ComponentType.NAVIGATION in type_counts or ComponentType.HEADER in type_counts:
            return "content"
        
        # Check for container dominance
        if type_counts.get(ComponentType.CONTAINER, 0) > len(components) / 2:
            return "background"
        
        return "content"
    
    def _calculate_levels(
        self,
        component_ids: list[str],
        parent_map: dict[str, str],
    ) -> dict[str, int]:
        """Calculate nesting level for each component."""
        levels = {}
        
        def get_level(comp_id: str) -> int:
            if comp_id in levels:
                return levels[comp_id]
            
            if comp_id not in parent_map:
                levels[comp_id] = 0
                return 0
            
            parent_id = parent_map[comp_id]
            level = get_level(parent_id) + 1
            levels[comp_id] = level
            return level
        
        for comp_id in component_ids:
            get_level(comp_id)
        
        return levels


def extract_hierarchy(
    components: list[DetectedComponent],
) -> HierarchyTree:
    """Convenience function for hierarchy extraction.
    
    Args:
        components: List of detected components
    
    Returns:
        HierarchyTree with all nodes and relationships
    """
    analyzer = HierarchyAnalyzer()
    return analyzer.extract_hierarchy(components)


def detect_containers(
    components: list[DetectedComponent],
) -> list[ContainerMatch]:
    """Convenience function for container detection.
    
    Args:
        components: List of detected components
    
    Returns:
        List of ContainerMatch objects
    """
    analyzer = HierarchyAnalyzer()
    return analyzer.detect_containers(components)


def infer_z_order(
    components: list[DetectedComponent],
) -> list[ZLayer]:
    """Convenience function for z-order inference.
    
    Args:
        components: List of detected components
    
    Returns:
        List of ZLayer objects
    """
    analyzer = HierarchyAnalyzer()
    return analyzer.infer_z_order(components)