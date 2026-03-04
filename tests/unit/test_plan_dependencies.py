"""
Unit tests for plan dependency resolution.

Tests for DependencyResolver topological sorting and dependency tracking.
"""

import pytest

from src.plan.dependencies import (
    DependencyResolver,
    resolve_order,
    get_dependencies,
    DEPENDENCY_RULES,
)
from src.plan.models import PlanActionCreate, PhaseType
from src.audit.models import AuditDimension
from src.db.models import Severity


class TestDependencyResolver:
    """Tests for DependencyResolver."""
    
    def test_get_dependencies(self):
        """Getting prerequisites for dimensions."""
        resolver = DependencyResolver()
        
        # Spacing depends on hierarchy and alignment
        deps = resolver.get_dependencies(AuditDimension.SPACING_RHYTHM)
        assert AuditDimension.VISUAL_HIERARCHY in deps
        assert AuditDimension.ALIGNMENT_GRID in deps
        
        # Typography depends on hierarchy
        deps = resolver.get_dependencies(AuditDimension.TYPOGRAPHY)
        assert AuditDimension.VISUAL_HIERARCHY in deps
        
        # Theming depends on color
        deps = resolver.get_dependencies(AuditDimension.DARK_MODE_THEMING)
        assert AuditDimension.COLOR in deps
        
        # Density depends on components
        deps = resolver.get_dependencies(AuditDimension.DENSITY)
        assert AuditDimension.COMPONENTS in deps
    
    def test_get_blocked(self):
        """Getting dependents for dimensions."""
        resolver = DependencyResolver()
        
        # Hierarchy blocks spacing and typography
        blocked = resolver.get_blocked(AuditDimension.VISUAL_HIERARCHY)
        assert AuditDimension.SPACING_RHYTHM in blocked
        assert AuditDimension.TYPOGRAPHY in blocked
        
        # Color blocks theming
        blocked = resolver.get_blocked(AuditDimension.COLOR)
        assert AuditDimension.DARK_MODE_THEMING in blocked
        
        # Components blocks density
        blocked = resolver.get_blocked(AuditDimension.COMPONENTS)
        assert AuditDimension.DENSITY in blocked
        
        # Alignment blocks spacing
        blocked = resolver.get_blocked(AuditDimension.ALIGNMENT_GRID)
        assert AuditDimension.SPACING_RHYTHM in blocked
    
    def test_has_dependency_cycle_no_cycle(self):
        """Cycle detection with no cycles."""
        resolver = DependencyResolver()
        
        dimensions = [
            AuditDimension.VISUAL_HIERARCHY,
            AuditDimension.SPACING_RHYTHM,
            AuditDimension.TYPOGRAPHY,
        ]
        
        assert not resolver.has_dependency_cycle(dimensions)
    
    def test_has_dependency_cycle_with_cycle(self):
        """Cycle detection with artificial cycle."""
        # Create rules with a cycle: A -> B -> C -> A
        cyclic_rules = {
            AuditDimension.SPACING_RHYTHM: [AuditDimension.TYPOGRAPHY],
            AuditDimension.TYPOGRAPHY: [AuditDimension.COLOR],
            AuditDimension.COLOR: [AuditDimension.SPACING_RHYTHM],
        }
        
        resolver = DependencyResolver(dependency_rules=cyclic_rules)
        
        dimensions = [
            AuditDimension.SPACING_RHYTHM,
            AuditDimension.TYPOGRAPHY,
            AuditDimension.COLOR,
        ]
        
        assert resolver.has_dependency_cycle(dimensions)
    
    def test_resolve_order_single_action(self):
        """Ordering with single action returns unchanged."""
        resolver = DependencyResolver()
        
        action = PlanActionCreate(
            finding_id="f1",
            description="Fix spacing",
            target_entity="Container",
            dimension=AuditDimension.SPACING_RHYTHM,
        )
        
        result = resolver.resolve_order([action])
        
        assert len(result) == 1
        assert result[0].finding_id == "f1"
    
    def test_resolve_order_respects_dependencies(self):
        """Ordering respects dimension dependencies within same phase."""
        resolver = DependencyResolver()
        
        # Create actions in same phase (Refinement) with dependencies
        # Typography depends on nothing, Spacing depends on Alignment
        # So with alignment, typography, spacing - alignment should come first
        alignment_action = PlanActionCreate(
            finding_id="f-alignment",
            description="Fix alignment",
            target_entity="Grid",
            dimension=AuditDimension.ALIGNMENT_GRID,  # Refinement
        )
        typography_action = PlanActionCreate(
            finding_id="f-typography",
            description="Fix typography",
            target_entity="Text",
            dimension=AuditDimension.TYPOGRAPHY,  # Refinement, no deps in refinement
        )
        spacing_action = PlanActionCreate(
            finding_id="f-spacing",
            description="Fix spacing",
            target_entity="Container",
            dimension=AuditDimension.SPACING_RHYTHM,  # Refinement, depends on alignment
        )
        
        # All are in Refinement phase, so ordering should respect dependencies
        result = resolver.resolve_order([spacing_action, typography_action, alignment_action])
        
        assert len(result) == 3
        # Alignment should be first (spacing depends on it)
        assert result[0].dimension == AuditDimension.ALIGNMENT_GRID
        # Check sequence numbers are set
        assert result[0].sequence >= 1
    
    def test_resolve_order_respects_phase_boundaries(self):
        """Ordering respects phase boundaries when enabled."""
        resolver = DependencyResolver()
        
        # Create actions from different phases
        hierarchy_action = PlanActionCreate(
            finding_id="f-hierarchy",
            description="Fix hierarchy",
            target_entity="Header",
            dimension=AuditDimension.VISUAL_HIERARCHY,  # Critical
        )
        spacing_action = PlanActionCreate(
            finding_id="f-spacing",
            description="Fix spacing",
            target_entity="Container",
            dimension=AuditDimension.SPACING_RHYTHM,  # Refinement
        )
        empty_state_action = PlanActionCreate(
            finding_id="f-empty",
            description="Fix empty state",
            target_entity="List",
            dimension=AuditDimension.EMPTY_STATES,  # Polish
        )
        
        result = resolver.resolve_order(
            [empty_state_action, spacing_action, hierarchy_action],
            respect_phase_boundaries=True
        )
        
        # Should be sorted by phase: Critical, Refinement, Polish
        assert result[0].dimension == AuditDimension.VISUAL_HIERARCHY
        assert result[1].dimension == AuditDimension.SPACING_RHYTHM
        assert result[2].dimension == AuditDimension.EMPTY_STATES
    
    def test_add_dependencies_to_actions(self):
        """Adding dependency IDs to actions."""
        resolver = DependencyResolver()
        
        hierarchy_action = PlanActionCreate(
            finding_id="f-hierarchy",
            description="Fix hierarchy",
            target_entity="Header",
            dimension=AuditDimension.VISUAL_HIERARCHY,
        )
        spacing_action = PlanActionCreate(
            finding_id="f-spacing",
            description="Fix spacing",
            target_entity="Container",
            dimension=AuditDimension.SPACING_RHYTHM,
        )
        
        result = resolver.add_dependencies_to_actions([hierarchy_action, spacing_action])
        
        # Find spacing action in result
        spacing_result = next(a for a in result if a.finding_id == "f-spacing")
        hierarchy_result = next(a for a in result if a.finding_id == "f-hierarchy")
        
        # Spacing should have hierarchy as dependency
        assert "f-hierarchy" in spacing_result.dependencies
        # Hierarchy should have no dependencies
        assert len(hierarchy_result.dependencies) == 0
    
    def test_custom_dependency_rules(self):
        """Custom dependency rules override defaults."""
        custom_rules = {
            AuditDimension.COLOR: [AuditDimension.TYPOGRAPHY],
        }
        
        resolver = DependencyResolver(dependency_rules=custom_rules)
        
        # Typography should depend on color (custom rule)
        deps = resolver.get_dependencies(AuditDimension.TYPOGRAPHY)
        assert AuditDimension.COLOR in deps


class TestConvenienceFunctions:
    """Tests for module-level convenience functions."""
    
    def test_resolve_order_function(self):
        """resolve_order uses default resolver."""
        action1 = PlanActionCreate(
            finding_id="f1",
            description="Fix spacing",
            target_entity="Container",
            dimension=AuditDimension.SPACING_RHYTHM,
        )
        action2 = PlanActionCreate(
            finding_id="f2",
            description="Fix hierarchy",
            target_entity="Header",
            dimension=AuditDimension.VISUAL_HIERARCHY,
        )
        
        result = resolve_order([action1, action2])
        
        # Hierarchy should come first
        assert result[0].dimension == AuditDimension.VISUAL_HIERARCHY
    
    def test_get_dependencies_function(self):
        """get_dependencies uses default resolver."""
        deps = get_dependencies(AuditDimension.SPACING_RHYTHM)
        assert AuditDimension.VISUAL_HIERARCHY in deps


class TestDefaultRules:
    """Tests for default dependency rules."""
    
    def test_rules_are_acyclic(self):
        """Default rules don't contain cycles."""
        resolver = DependencyResolver()
        
        all_dimensions = list(DEPENDENCY_RULES.keys())
        for blocked_list in DEPENDENCY_RULES.values():
            all_dimensions.extend(blocked_list)
        
        unique_dimensions = list(set(all_dimensions))
        assert not resolver.has_dependency_cycle(unique_dimensions)