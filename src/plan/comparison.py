"""
Before/After comparison generator for design system proposals.

Generates text descriptions that clearly communicate the current state
and proposed changes for design system proposals.
"""

from typing import Any, Optional

from src.plan.proposal_models import (
    BeforeAfterDescription,
    ComponentProposal,
    DesignSystemProposal,
    TokenProposal,
    TokenType,
)


# =============================================================================
# BEFORE/AFTER GENERATOR
# =============================================================================

class BeforeAfterGenerator:
    """Generates before/after descriptions for proposals."""
    
    def __init__(self):
        """Initialize the generator."""
        pass
    
    def generate_token_comparison(
        self,
        proposal: TokenProposal,
    ) -> BeforeAfterDescription:
        """Generate before/after description for a token proposal.
        
        Args:
            proposal: Token proposal
        
        Returns:
            BeforeAfterDescription
        """
        # Build before text based on token type
        if proposal.token_type == TokenType.COLOR:
            before = f"No design token for color {proposal.proposed_value}"
            after = f"Use `{proposal.token_name}` token ({proposal.proposed_value})"
            benefit = "Consistent color usage across screens"
            changes = [
                f"Add new color token: `{proposal.token_name}`",
                f"Replace {proposal.usage_count} hardcoded instances",
            ]
        elif proposal.token_type == TokenType.SPACING:
            before = f"Inconsistent spacing with value {proposal.proposed_value}"
            after = f"Use `{proposal.token_name}` token for consistent spacing"
            benefit = "Predictable spacing rhythm throughout the UI"
            changes = [
                f"Add new spacing token: `{proposal.token_name}`",
                f"Standardize {proposal.usage_count} instances",
            ]
        elif proposal.token_type == TokenType.TYPOGRAPHY:
            before = f"Typography value {proposal.proposed_value} lacks token reference"
            after = f"Use `{proposal.token_name}` token for typography"
            benefit = "Consistent typography hierarchy"
            changes = [
                f"Add new typography token: `{proposal.token_name}`",
                f"Apply to {proposal.usage_count} instances",
            ]
        else:
            before = f"No token for {proposal.token_type.value} value {proposal.proposed_value}"
            after = f"Use `{proposal.token_name}` token"
            benefit = "Improved design system consistency"
            changes = [
                f"Add new token: `{proposal.token_name}`",
                f"Replace {proposal.usage_count} instances",
            ]
        
        return BeforeAfterDescription(
            before_text=before,
            after_text=after,
            key_changes=changes,
            benefit=benefit,
        )
    
    def generate_component_comparison(
        self,
        proposal: ComponentProposal,
    ) -> BeforeAfterDescription:
        """Generate before/after description for a component proposal.
        
        Args:
            proposal: Component proposal
        
        Returns:
            BeforeAfterDescription
        """
        # Build before text
        before = f"{proposal.component_type} components have inconsistent styling"
        if proposal.detected_instances > 1:
            before += f" across {proposal.detected_instances} instances"
        
        # Build after text
        after = f"Use `{proposal.component_type}-{proposal.variant_name}` variant"
        if proposal.properties:
            prop_desc = ", ".join(
                f"{k}: {v}" for k, v in list(proposal.properties.items())[:3]
            )
            after += f" with {prop_desc}"
        
        # Build benefit
        benefit = f"Consistent {proposal.component_type} appearance across all screens"
        
        # Build key changes
        changes = [
            f"Define {proposal.component_type}-{proposal.variant_name} variant",
            f"Apply to {proposal.detected_instances} instances",
        ]
        
        for prop, value in list(proposal.properties.items())[:3]:
            changes.append(f"Set {prop}: {value}")
        
        return BeforeAfterDescription(
            before_text=before,
            after_text=after,
            key_changes=changes,
            benefit=benefit,
        )
    
    def generate_summary_comparison(
        self,
        proposal: DesignSystemProposal,
    ) -> str:
        """Generate a summary comparison for the full proposal.
        
        Args:
            proposal: Full design system proposal
        
        Returns:
            Summary text
        """
        total = proposal.total_proposals()
        
        if total == 0:
            return "No design system changes proposed."
        
        parts = [
            f"Design System Proposal Summary:",
            f"- {len(proposal.token_proposals)} token proposals",
            f"- {len(proposal.component_proposals)} component proposals",
            f"- {proposal.total_affected_screens} screens affected",
            f"- Priority: {proposal.priority.value.upper()}",
            f"- Impact Score: {proposal.impact_score:.2f}",
        ]
        
        # Add top recommendation
        highest = proposal.get_highest_impact_proposal()
        if highest:
            if isinstance(highest, TokenProposal):
                parts.append(f"\nTop Recommendation: Add `{highest.token_name}` token")
            else:
                parts.append(f"\nTop Recommendation: Add `{highest.component_type}-{highest.variant_name}` variant")
        
        return "\n".join(parts)


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

_default_generator: Optional[BeforeAfterGenerator] = None


def get_default_generator() -> BeforeAfterGenerator:
    """Get or create the default generator instance."""
    global _default_generator
    if _default_generator is None:
        _default_generator = BeforeAfterGenerator()
    return _default_generator


def generate_token_comparison(
    proposal: TokenProposal,
) -> BeforeAfterDescription:
    """Generate before/after description for a token proposal.
    
    Convenience function using default generator.
    
    Args:
        proposal: Token proposal
    
    Returns:
        BeforeAfterDescription
    """
    return get_default_generator().generate_token_comparison(proposal)


def generate_component_comparison(
    proposal: ComponentProposal,
) -> BeforeAfterDescription:
    """Generate before/after description for a component proposal.
    
    Convenience function using default generator.
    
    Args:
        proposal: Component proposal
    
    Returns:
        BeforeAfterDescription
    """
    return get_default_generator().generate_component_comparison(proposal)


def generate_summary_comparison(
    proposal: DesignSystemProposal,
) -> str:
    """Generate summary comparison for a full proposal.
    
    Convenience function using default generator.
    
    Args:
        proposal: Full design system proposal
    
    Returns:
        Summary text
    """
    return get_default_generator().generate_summary_comparison(proposal)