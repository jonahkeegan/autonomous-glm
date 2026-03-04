"""
Design system proposal generator.

Main orchestration for generating design system proposals from audit results
and detected patterns.
"""

from typing import Any, Optional, Union

from src.plan.proposal_models import (
    BeforeAfterDescription,
    ComponentProposal,
    DesignSystemProposal,
    Priority,
    TokenProposal,
)
from src.plan.token_analyzer import (
    TokenAnalyzer,
    analyze_all_token_patterns,
)
from src.plan.comparison import (
    BeforeAfterGenerator,
    generate_token_comparison,
    generate_component_comparison,
)


# =============================================================================
# IMPACT SCORING
# =============================================================================

def calculate_impact_score(
    proposal: Union[TokenProposal, ComponentProposal],
    total_screens: int = 1,
) -> float:
    """Calculate impact score for a proposal.
    
    Formula: (affected_screens / total_screens) * usage_weight * consistency_factor
    
    Args:
        proposal: Token or Component proposal
        total_screens: Total number of screens in the audit
    
    Returns:
        Impact score between 0.0 and 1.0
    """
    # Get usage count based on proposal type
    if isinstance(proposal, TokenProposal):
        usage_count = proposal.usage_count
        affected_count = len(proposal.affected_screens)
    else:
        usage_count = proposal.detected_instances
        affected_count = len(proposal.affected_screens)
    
    # Affected screens ratio (0.0 - 1.0)
    screen_ratio = affected_count / max(total_screens, 1)
    
    # Usage weight (logarithmic scaling)
    # 3 occurrences = 0.3, 10 = 0.5, 30 = 0.7, 100 = 0.9
    import math
    usage_weight = min(0.9, 0.3 + 0.2 * math.log10(max(usage_count, 1)))
    
    # Consistency factor (higher for more usage)
    consistency_factor = min(1.0, usage_count / 10)
    
    # Combined score
    score = screen_ratio * usage_weight * (0.5 + 0.5 * consistency_factor)
    
    return min(1.0, max(0.0, score))


def determine_priority(impact_score: float) -> Priority:
    """Determine priority level from impact score.
    
    Args:
        impact_score: Impact score (0.0-1.0)
    
    Returns:
        Priority level
    """
    if impact_score >= 0.7:
        return Priority.CRITICAL
    elif impact_score >= 0.5:
        return Priority.HIGH
    elif impact_score >= 0.3:
        return Priority.MEDIUM
    else:
        return Priority.LOW


# =============================================================================
# PROPOSAL GENERATOR
# =============================================================================

class ProposalGenerator:
    """Main generator for design system proposals."""
    
    def __init__(
        self,
        design_tokens: Optional[dict[str, dict[str, str]]] = None,
        usage_threshold: int = 3,
    ):
        """Initialize the proposal generator.
        
        Args:
            design_tokens: Existing design tokens
            usage_threshold: Minimum occurrences to propose a token
        """
        self.token_analyzer = TokenAnalyzer(
            design_tokens=design_tokens,
            usage_threshold=usage_threshold,
        )
        self.before_after_generator = BeforeAfterGenerator()
        self.design_tokens = design_tokens
        self.usage_threshold = usage_threshold
    
    def create_token_proposal(
        self,
        pattern: dict[str, Any],
    ) -> TokenProposal:
        """Create a token proposal from a detected pattern.
        
        Args:
            pattern: Pattern dict with value, type, count, screens
        
        Returns:
            TokenProposal
        """
        from src.plan.token_analyzer import (
            generate_color_token_name,
            generate_spacing_token_name,
            generate_typography_token_name,
        )
        
        token_type = pattern.get("token_type", "color")
        value = pattern.get("value", "")
        count = pattern.get("count", 1)
        screens = pattern.get("screens", [])
        
        # Generate appropriate token name
        if token_type == "color":
            token_name = generate_color_token_name(value)
            rationale = f"Detected {count} instances of this color without a matching design token"
        elif token_type == "spacing":
            import re
            match = re.search(r"(\d+)", value)
            px = int(match.group(1)) if match else 0
            token_name = generate_spacing_token_name(px)
            rationale = f"Detected {count} instances of this spacing value without a matching design token"
        elif token_type == "typography":
            prop_type = pattern.get("property", "size")
            token_name = generate_typography_token_name(prop_type, value)
            rationale = f"Detected {count} instances of this font {prop_type} without a matching design token"
        else:
            token_name = f"--{token_type}-{value}"
            rationale = f"Detected {count} instances of this {token_type} value"
        
        return TokenProposal(
            token_name=token_name,
            token_type=token_type,
            proposed_value=value,
            rationale=rationale,
            usage_count=count,
            affected_screens=screens,
        )
    
    def create_component_proposal(
        self,
        component_type: str,
        variant_name: str,
        properties: dict[str, Any],
        findings: list[dict[str, Any]],
    ) -> ComponentProposal:
        """Create a component variant proposal from findings.
        
        Args:
            component_type: Base component type (e.g., "button")
            variant_name: Name for the variant (e.g., "elevated")
            properties: CSS properties defining the variant
            findings: Related audit findings
        
        Returns:
            ComponentProposal
        """
        # Collect affected screens from findings
        affected_screens = list(set(
            f.get("entity_id", "") for f in findings if f.get("entity_id")
        ))
        
        # Collect example components
        example_components = [
            f.get("component_id", "")
            for f in findings
            if f.get("component_id")
        ]
        
        # Build rationale from findings
        issue_summaries = [
            f.get("issue", "")[:50]
            for f in findings[:3]
            if f.get("issue")
        ]
        rationale = f"Inconsistent {component_type} styling detected"
        if issue_summaries:
            rationale += f": {', '.join(issue_summaries[:2])}"
        
        return ComponentProposal(
            component_type=component_type,
            variant_name=variant_name,
            properties=properties,
            rationale=rationale,
            detected_instances=len(findings),
            affected_screens=affected_screens,
            example_components=example_components,
        )
    
    def prioritize_proposals(
        self,
        proposals: list[Union[TokenProposal, ComponentProposal]],
        total_screens: int = 1,
    ) -> list[Union[TokenProposal, ComponentProposal]]:
        """Sort proposals by impact score (highest first).
        
        Args:
            proposals: List of proposals to prioritize
            total_screens: Total screens for impact calculation
        
        Returns:
            Sorted list of proposals
        """
        # Calculate impact scores
        scored = [
            (proposal, calculate_impact_score(proposal, total_screens))
            for proposal in proposals
        ]
        
        # Sort by score descending
        scored.sort(key=lambda x: x[1], reverse=True)
        
        return [proposal for proposal, _ in scored]
    
    def generate_proposals(
        self,
        findings: list[dict[str, Any]],
        detected_tokens: Optional[dict[str, list[dict[str, Any]]]] = None,
        screen_ids: Optional[list[str]] = None,
        audit_session_id: Optional[str] = None,
    ) -> DesignSystemProposal:
        """Generate design system proposals from audit results.
        
        Args:
            findings: Audit findings list
            detected_tokens: Detected tokens by type
            screen_ids: List of all screen IDs in the audit
            audit_session_id: ID of the audit session
        
        Returns:
            DesignSystemProposal with all recommendations
        """
        screen_ids = screen_ids or []
        total_screens = len(screen_ids) or 1
        
        # Generate token proposals
        token_proposals = analyze_all_token_patterns(
            findings=findings,
            detected_tokens=detected_tokens,
            design_tokens=self.design_tokens,
            usage_threshold=self.usage_threshold,
        )
        
        # Generate component proposals from component-related findings
        component_proposals = self._analyze_component_patterns(findings)
        
        # Combine all proposals for prioritization
        all_proposals: list[Union[TokenProposal, ComponentProposal]] = [
            *token_proposals,
            *component_proposals,
        ]
        
        # Prioritize
        prioritized = self.prioritize_proposals(all_proposals, total_screens)
        
        # Calculate overall impact score
        if prioritized:
            scores = [
                calculate_impact_score(p, total_screens)
                for p in prioritized
            ]
            overall_impact = sum(scores) / len(scores)
        else:
            overall_impact = 0.0
        
        # Determine overall priority
        overall_priority = determine_priority(overall_impact)
        
        # Collect all affected screens
        all_affected = set()
        for p in token_proposals:
            all_affected.update(p.affected_screens)
        for p in component_proposals:
            all_affected.update(p.affected_screens)
        
        # Generate before/after summaries for top proposals
        before_after_summaries = {}
        for proposal in prioritized[:5]:  # Top 5 proposals
            if isinstance(proposal, TokenProposal):
                key = proposal.token_name
                before_after_summaries[key] = generate_token_comparison(proposal)
            else:
                key = f"{proposal.component_type}-{proposal.variant_name}"
                before_after_summaries[key] = generate_component_comparison(proposal)
        
        # Separate back into token and component lists (prioritized)
        prioritized_tokens = [p for p in prioritized if isinstance(p, TokenProposal)]
        prioritized_components = [p for p in prioritized if isinstance(p, ComponentProposal)]
        
        return DesignSystemProposal(
            token_proposals=prioritized_tokens,
            component_proposals=prioritized_components,
            priority=overall_priority,
            impact_score=overall_impact,
            total_affected_screens=len(all_affected),
            audit_session_id=audit_session_id,
            before_after_summaries=before_after_summaries,
        )
    
    def _analyze_component_patterns(
        self,
        findings: list[dict[str, Any]],
    ) -> list[ComponentProposal]:
        """Analyze findings for component variant patterns.
        
        Args:
            findings: Audit findings
        
        Returns:
            List of component proposals
        """
        proposals = []
        
        # Group findings by component type
        by_component: dict[str, list[dict[str, Any]]] = {}
        for finding in findings:
            metadata = finding.get("metadata", {})
            component_type = metadata.get("component_type", "")
            if component_type:
                if component_type not in by_component:
                    by_component[component_type] = []
                by_component[component_type].append(finding)
        
        # Analyze each component type for variants
        for component_type, component_findings in by_component.items():
            # Check for size variants
            sizes = set()
            for f in component_findings:
                metadata = f.get("metadata", {})
                if "size" in metadata:
                    sizes.add(metadata["size"])
            
            if len(sizes) > 1:
                # Multiple sizes detected - propose size variants
                for size in sorted(sizes):
                    size_findings = [
                        f for f in component_findings
                        if f.get("metadata", {}).get("size") == size
                    ]
                    if len(size_findings) >= 2:  # At least 2 instances
                        proposals.append(self.create_component_proposal(
                            component_type=component_type,
                            variant_name=f"size-{size}",
                            properties={"font-size": f"{size}px"} if isinstance(size, int) else {},
                            findings=size_findings,
                        ))
            
            # Check for style variants (e.g., elevated, outlined)
            styles = set()
            for f in component_findings:
                metadata = f.get("metadata", {})
                if "style" in metadata:
                    styles.add(metadata["style"])
            
            if len(styles) > 1:
                for style in sorted(styles):
                    style_findings = [
                        f for f in component_findings
                        if f.get("metadata", {}).get("style") == style
                    ]
                    if len(style_findings) >= 2:
                        proposals.append(self.create_component_proposal(
                            component_type=component_type,
                            variant_name=str(style),
                            properties={"variant": str(style)},
                            findings=style_findings,
                        ))
        
        return proposals


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def generate_design_system_proposals(
    findings: list[dict[str, Any]],
    detected_tokens: Optional[dict[str, list[dict[str, Any]]]] = None,
    screen_ids: Optional[list[str]] = None,
    audit_session_id: Optional[str] = None,
    design_tokens: Optional[dict[str, dict[str, str]]] = None,
    usage_threshold: int = 3,
) -> DesignSystemProposal:
    """Generate design system proposals from audit results.
    
    Convenience function that creates a ProposalGenerator and generates proposals.
    
    Args:
        findings: Audit findings list
        detected_tokens: Detected tokens by type
        screen_ids: List of all screen IDs in the audit
        audit_session_id: ID of the audit session
        design_tokens: Existing design tokens
        usage_threshold: Minimum occurrences to propose a token
    
    Returns:
        DesignSystemProposal with all recommendations
    """
    generator = ProposalGenerator(
        design_tokens=design_tokens,
        usage_threshold=usage_threshold,
    )
    
    return generator.generate_proposals(
        findings=findings,
        detected_tokens=detected_tokens,
        screen_ids=screen_ids,
        audit_session_id=audit_session_id,
    )