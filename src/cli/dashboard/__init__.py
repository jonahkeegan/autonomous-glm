"""
Dashboard module for autonomous-glm CLI.

Provides metrics aggregation and dashboard rendering capabilities.
"""

from .metrics import (
    MetricsAggregator,
    DashboardMetrics,
    FindingsSummary,
    TrendData,
    TrendPoint,
    ArtifactStats,
    Period,
)
from .renderer import (
    DashboardRenderer,
    render_dashboard,
)

__all__ = [
    # Metrics
    "MetricsAggregator",
    "DashboardMetrics",
    "FindingsSummary",
    "TrendData",
    "TrendPoint",
    "ArtifactStats",
    "Period",
    # Renderer
    "DashboardRenderer",
    "render_dashboard",
]