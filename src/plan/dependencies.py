"""
Dependency resolution for plan synthesis.

Handles cross-dimension dependencies and topological sorting to ensure
actions are executed in the correct order (e.g., fix hierarchy before spacing).
"""

from collections import defaultdict
from typing import Optional

from src.audit.models import AuditDimension
from src.plan.models import PlanActionCreate


# =============================================================================
# DEFAULT DEPENDENCY RULES
# =============================================================================

# Dependency graph: dimension -> list of dimensions it blocks
# Meaning: if VISUAL_HIERARCHY has issues, SPACING_RHYTHM and TYPOGRAPHY
# fixes should wait until hierarchy is resolved
DEPENDENCY_RULES: dict[AuditDimension, list[AuditDimension]] = {
    # Hierarchy must be fixed before spacing and typography
    AuditDimension.VISUAL_HIERARCHY: [
        AuditDimension.SPACING_RHYTHM,
        AuditDimension.TYPOGRAPHY,
    ],
    
    # Color must be fixed before theming
    AuditDimension.COLOR: [
        AuditDimension.DARK_MODE_THEMING,
    ],
    
    # Components must be fixed before density
    AuditDimension.COMPONENTS: [
        AuditDimension.DENSITY,
    ],
    
    # Alignment affects spacing
    AuditDimension.ALIGNMENT_GRID: [
        AuditDimension.SPACING_RHYTHM,
    ],
}


# =============================================================================
# DEPENDENCY RESOLVER
# =============================================================================

class DependencyResolver:
    """Resolves cross-dimension dependencies for plan actions.
    
    Uses a predefined dependency graph to determine which dimensions
    must be fixed before others. Applies topological sorting to
    sequence actions correctly.
    """
    
    def __init__(
        self,
        dependency_rules: Optional[dict[AuditDimension, list[AuditDimension]]] = None,
    ):
        """Initialize the resolver with optional custom rules.
        
        Args:
            dependency_rules: Custom dimension dependency rules
        """
        self.dependency_rules = dependency_rules or DEPENDENCY_RULES
        self._reverse_cache: Optional[dict[AuditDimension, list[AuditDimension]]] = None
    
    def get_dependencies(self, dimension: AuditDimension) -> list[AuditDimension]:
        """Get the dimensions that must be completed before the given dimension.
        
        This returns the "prerequisites" - dimensions that block the given dimension.
        
        Args:
            dimension: The dimension to check prerequisites for
            
        Returns:
            List of dimensions that must be completed first
        """
        # Build reverse lookup cache
        if self._reverse_cache is None:
            self._reverse_cache = defaultdict(list)
            for blocker, blocked in self.dependency_rules.items():
                for dim in blocked:
                    self._reverse_cache[dim].append(blocker)
        
        return self._reverse_cache.get(dimension, [])
    
    def get_blocked(self, dimension: AuditDimension) -> list[AuditDimension]:
        """Get the dimensions that are blocked by the given dimension.
        
        This returns the "dependents" - dimensions that wait for the given dimension.
        
        Args:
            dimension: The dimension to check dependents for
            
        Returns:
            List of dimensions that are blocked
        """
        return self.dependency_rules.get(dimension, [])
    
    def has_dependency_cycle(self, dimensions: list[AuditDimension]) -> bool:
        """Check if there's a dependency cycle among the given dimensions.
        
        Uses DFS to detect cycles in the dependency graph.
        
        Args:
            dimensions: List of dimensions to check
            
        Returns:
            True if a cycle exists, False otherwise
        """
        # Build adjacency list for just these dimensions
        dim_set = set(dimensions)
        adj: dict[AuditDimension, list[AuditDimension]] = defaultdict(list)
        
        for dim in dimensions:
            for blocked in self.get_blocked(dim):
                if blocked in dim_set:
                    adj[dim].append(blocked)
        
        # DFS cycle detection
        WHITE, GRAY, BLACK = 0, 1, 2
        color = {dim: WHITE for dim in dimensions}
        
        def dfs(node: AuditDimension) -> bool:
            color[node] = GRAY
            for neighbor in adj[node]:
                if color[neighbor] == GRAY:
                    return True  # Back edge = cycle
                if color[neighbor] == WHITE and dfs(neighbor):
                    return True
            color[node] = BLACK
            return False
        
        for dim in dimensions:
            if color[dim] == WHITE:
                if dfs(dim):
                    return True
        
        return False
    
    def resolve_order(
        self, 
        actions: list[PlanActionCreate],
        respect_phase_boundaries: bool = True
    ) -> list[PlanActionCreate]:
        """Order actions respecting dependencies via topological sort.
        
        Actions are sorted so that dependencies are resolved first.
        Within dependency levels, actions maintain their original relative order.
        
        Args:
            actions: List of actions to order
            respect_phase_boundaries: If True, only reorder within same phase
            
        Returns:
            Actions in dependency-resolved order
        """
        if len(actions) <= 1:
            return actions
        
        # Group actions by phase if needed
        if respect_phase_boundaries:
            from src.plan.models import PhaseType
            by_phase: dict[PhaseType, list[PlanActionCreate]] = defaultdict(list)
            for action in actions:
                phase = self._get_phase_for_dimension(action.dimension)
                by_phase[phase].append(action)
            
            # Sort within each phase and recombine
            result = []
            for phase in [PhaseType.CRITICAL, PhaseType.REFINEMENT, PhaseType.POLISH]:
                if phase in by_phase:
                    sorted_phase = self._topological_sort(by_phase[phase])
                    result.extend(sorted_phase)
            return result
        else:
            return self._topological_sort(actions)
    
    def _get_phase_for_dimension(self, dimension: AuditDimension) -> "PhaseType":
        """Get the phase for a dimension using default classification."""
        from src.plan.phasing import classify
        from src.db.models import Severity
        # Use MEDIUM severity as default for phase lookup
        return classify(dimension, Severity.MEDIUM)
    
    def _topological_sort(
        self, 
        actions: list[PlanActionCreate]
    ) -> list[PlanActionCreate]:
        """Perform topological sort on actions based on dimension dependencies.
        
        Uses Kahn's algorithm for stable topological sort.
        
        Args:
            actions: Actions to sort
            
        Returns:
            Actions in topologically sorted order
        """
        if len(actions) <= 1:
            return actions
        
        # Build dimension -> actions mapping
        dim_to_actions: dict[AuditDimension, list[PlanActionCreate]] = defaultdict(list)
        for action in actions:
            dim_to_actions[action.dimension].append(action)
        
        # Build dependency graph for present dimensions
        present_dims = set(dim_to_actions.keys())
        
        # Calculate in-degree for each dimension
        in_degree: dict[AuditDimension, int] = {dim: 0 for dim in present_dims}
        adj: dict[AuditDimension, list[AuditDimension]] = defaultdict(list)
        
        for dim in present_dims:
            deps = self.get_dependencies(dim)
            for dep in deps:
                if dep in present_dims:
                    adj[dep].append(dim)
                    in_degree[dim] += 1
        
        # Kahn's algorithm with stable ordering
        result_dims: list[AuditDimension] = []
        queue: list[AuditDimension] = []
        
        # Start with dimensions that have no dependencies
        for dim in sorted(present_dims, key=lambda d: d.value):
            if in_degree[dim] == 0:
                queue.append(dim)
        
        while queue:
            # Sort to ensure deterministic order
            queue.sort(key=lambda d: d.value)
            current = queue.pop(0)
            result_dims.append(current)
            
            for neighbor in adj[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        # Check for cycle (shouldn't happen if has_dependency_cycle was checked)
        if len(result_dims) != len(present_dims):
            # Fall back to original order if cycle detected
            return actions
        
        # Build result list with sequenced actions
        result: list[PlanActionCreate] = []
        sequence = 1
        for dim in result_dims:
            for action in dim_to_actions[dim]:
                result.append(action.with_sequence(sequence))
                sequence += 1
        
        return result
    
    def add_dependencies_to_actions(
        self, 
        actions: list[PlanActionCreate]
    ) -> list[PlanActionCreate]:
        """Add dependency IDs to actions based on dimension dependencies.
        
        This populates the `dependencies` field on each action with the
        IDs of actions that must complete first.
        
        Args:
            actions: Actions to update with dependencies
            
        Returns:
            Actions with dependencies populated
        """
        if len(actions) <= 1:
            return actions
        
        # Group actions by dimension
        dim_to_action_ids: dict[AuditDimension, list[str]] = defaultdict(list)
        for action in actions:
            dim_to_action_ids[action.dimension].append(action.finding_id)
        
        # Build dependency map: action_id -> list of dependency action_ids
        action_deps: dict[str, list[str]] = defaultdict(list)
        
        for action in actions:
            prereq_dims = self.get_dependencies(action.dimension)
            for prereq_dim in prereq_dims:
                # All actions from the prerequisite dimension are dependencies
                action_deps[action.finding_id].extend(dim_to_action_ids[prereq_dim])
        
        # Update actions with dependencies
        result: list[PlanActionCreate] = []
        for action in actions:
            deps = action_deps.get(action.finding_id, [])
            result.append(action.with_dependencies(deps))
        
        return result


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

_default_resolver = DependencyResolver()


def resolve_order(actions: list[PlanActionCreate]) -> list[PlanActionCreate]:
    """Order actions respecting dependencies using the default resolver.
    
    Args:
        actions: List of actions to order
        
    Returns:
        Actions in dependency-resolved order
    """
    return _default_resolver.resolve_order(actions)


def get_dependencies(dimension: AuditDimension) -> list[AuditDimension]:
    """Get prerequisites for a dimension using the default resolver.
    
    Args:
        dimension: The dimension to check
        
    Returns:
        List of dimensions that must be completed first
    """
    return _default_resolver.get_dependencies(dimension)