"""
Pydantic models for hierarchy analysis results.

Defines models for component hierarchy trees, container relationships, and z-order layers.
"""

from enum import Enum
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class HierarchyNode(BaseModel):
    """A node in the component hierarchy tree representing a single component."""
    
    id: str = Field(..., description="Component identifier")
    parent_id: Optional[str] = Field(
        default=None,
        description="Parent component ID (None for root)"
    )
    children: list[str] = Field(
        default_factory=list,
        description="List of child component IDs"
    )
    z_index: int = Field(
        default=0,
        ge=0,
        description="Z-order layer (0 = background)"
    )
    level: int = Field(
        default=0,
        ge=0,
        description="Nesting depth level (0 = root)"
    )
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Confidence in parent-child relationship"
    )


class HierarchyTree(BaseModel):
    """Complete hierarchy tree structure for a screen."""
    
    root_id: Optional[str] = Field(
        default=None,
        description="ID of the root component (usually the container)"
    )
    nodes: dict[str, HierarchyNode] = Field(
        default_factory=dict,
        description="Map of component ID to HierarchyNode"
    )
    max_depth: int = Field(
        default=0,
        ge=0,
        description="Maximum nesting depth in the tree"
    )
    component_count: int = Field(
        default=0,
        ge=0,
        description="Total number of components in the tree"
    )
    
    def get_node(self, node_id: str) -> Optional[HierarchyNode]:
        """Get a node by ID."""
        return self.nodes.get(node_id)
    
    def get_children(self, node_id: str) -> list[HierarchyNode]:
        """Get all child nodes for a given node ID."""
        node = self.get_node(node_id)
        if not node:
            return []
        return [self.nodes[cid] for cid in node.children if cid in self.nodes]
    
    def get_descendants(self, node_id: str) -> list[HierarchyNode]:
        """Get all descendant nodes recursively."""
        result = []
        node = self.get_node(node_id)
        if not node:
            return result
        
        for child_id in node.children:
            child = self.get_node(child_id)
            if child:
                result.append(child)
                result.extend(self.get_descendants(child_id))
        return result
    
    def get_ancestors(self, node_id: str) -> list[HierarchyNode]:
        """Get all ancestor nodes up to root."""
        result = []
        node = self.get_node(node_id)
        if not node or not node.parent_id:
            return result
        
        parent = self.get_node(node.parent_id)
        while parent:
            result.append(parent)
            parent = self.get_node(parent.parent_id) if parent.parent_id else None
        return result


class ContainerMatch(BaseModel):
    """Represents a detected parent-child container relationship."""
    
    parent_id: str = Field(..., description="Parent component ID")
    child_id: str = Field(..., description="Child component ID")
    containment_ratio: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Ratio of child area inside parent"
    )
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Confidence in the relationship"
    )


class ZLayer(BaseModel):
    """Represents a z-order layer with component IDs."""
    
    z_index: int = Field(
        ...,
        ge=0,
        description="Z-order index (0 = background)"
    )
    component_ids: list[str] = Field(
        default_factory=list,
        description="Component IDs at this layer"
    )
    layer_type: Optional[str] = Field(
        default=None,
        description="Inferred layer type (background, content, overlay, modal)"
    )


class NestingLevel(BaseModel):
    """Information about nesting depth for a component."""
    
    component_id: str = Field(..., description="Component identifier")
    depth: int = Field(
        ...,
        ge=0,
        description="Nesting depth (0 = root level)"
    )
    container_id: Optional[str] = Field(
        default=None,
        description="Immediate parent container ID"
    )
    has_children: bool = Field(
        default=False,
        description="Whether this component has children"
    )


class HierarchyAnalysisResult(BaseModel):
    """Complete hierarchy analysis result for a screen."""
    
    tree: HierarchyTree = Field(..., description="Complete hierarchy tree")
    z_layers: list[ZLayer] = Field(
        default_factory=list,
        description="Z-order layers sorted by index"
    )
    container_matches: list[ContainerMatch] = Field(
        default_factory=list,
        description="All detected container relationships"
    )
    orphan_ids: list[str] = Field(
        default_factory=list,
        description="Components without parent relationships"
    )
    processing_time_ms: float = Field(
        default=0.0,
        ge=0.0,
        description="Processing time in milliseconds"
    )