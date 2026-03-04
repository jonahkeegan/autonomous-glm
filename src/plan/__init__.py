"""
Plan Generation Module for Autonomous-GLM.

This module provides phased plan synthesis from audit findings, organizing
improvements into Critical → Refinement → Polish phases with proper
dependency resolution.
"""

from src.plan.models import (
    PhaseType,
    PlanStatus,
    PlanActionCreate,
    PlanPhaseCreate as PlanPhaseData,
    Plan,
    PlanSummary,
)
from src.plan.phasing import PhaseClassifier, classify_finding
from src.plan.dependencies import DependencyResolver
from src.plan.synthesizer import PlanSynthesizer

__all__ = [
    # Models
    "PhaseType",
    "PlanStatus",
    "PlanActionCreate",
    "PlanPhaseData",
    "Plan",
    "PlanSummary",
    # Classification
    "PhaseClassifier",
    "classify_finding",
    # Dependencies
    "DependencyResolver",
    # Synthesis
    "PlanSynthesizer",
]