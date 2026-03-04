"""
Unit tests for comparison (before/after) module.
"""

import pytest

from src.plan.comparison import (
    BeforeAfterGenerator,
    generate_token_comparison,
    generate_component_comparison,
    generate_summary_comparison,
)
from src.plan.proposal_models import (
    TokenProposal,
    ComponentProposal,
    DesignSystemProposal,
    TokenType,
)


class TestBeforeAfterGenerator:
    """Tests for BeforeAfterGenerator class."""
    
    def test_create_generator(self):
        """Test creating generator."""
        generator = BeforeAfterGenerator()
        
        assert generator is not None
    
    def test_generate_token_comparison_color(self):
        """Test generating comparison for color token."""
        generator = BeforeAfterGenerator()
        
        proposal = TokenProposal(
            token_name="--color-accent",
            token_type=TokenType.COLOR,
            proposed_value="#FF6B6B",
            rationale="Brand color",
            usage_count=5,
        )
        
        comparison = generator.generate_token_comparison(proposal)
        
        assert comparison.before_text is not None
        assert comparison.after_text is not None
        assert "accent" in comparison.after_text.lower() or "token" in comparison.after_text.lower()
        assert len(comparison.key_changes) > 0
    
    def test_generate_token_comparison_spacing(self):
        """Test generating comparison for spacing token."""
        generator = BeforeAfterGenerator()
        
        proposal = TokenProposal(
            token_name="--spacing-lg",
            token_type=TokenType.SPACING,
            proposed_value="16px",
            rationale="Large spacing",
            usage_count=3,
        )
        
        comparison = generator.generate_token_comparison(proposal)
        
        assert "spacing" in comparison.before_text.lower()
        assert "benefit" in comparison.benefit.lower() or "rhythm" in comparison.benefit.lower()
    
    def test_generate_token_comparison_typography(self):
        """Test generating comparison for typography token."""
        generator = BeforeAfterGenerator()
        
        proposal = TokenProposal(
            token_name="--font-size-lg",
            token_type=TokenType.TYPOGRAPHY,
            proposed_value="18px",
            rationale="Large text",
            usage_count=4,
        )
        
        comparison = generator.generate_token_comparison(proposal)
        
        assert "typography" in comparison.before_text.lower() or "font" in comparison.before_text.lower()
    
    def test_generate_component_comparison(self):
        """Test generating comparison for component proposal."""
        generator = BeforeAfterGenerator()
        
        proposal = ComponentProposal(
            component_type="card",
            variant_name="elevated",
            properties={"box-shadow": "0 4px 6px rgba(0,0,0,0.1)"},
            rationale="Elevated cards",
            detected_instances=5,
        )
        
        comparison = generator.generate_component_comparison(proposal)
        
        assert "card" in comparison.before_text.lower()
        assert "elevated" in comparison.after_text.lower()
        assert len(comparison.key_changes) > 0
    
    def test_generate_component_comparison_with_properties(self):
        """Test component comparison includes properties."""
        generator = BeforeAfterGenerator()
        
        proposal = ComponentProposal(
            component_type="button",
            variant_name="large",
            properties={"padding": "16px 32px", "font-size": "18px"},
            rationale="Large buttons",
            detected_instances=3,
        )
        
        comparison = generator.generate_component_comparison(proposal)
        
        # Should include properties in changes
        changes_text = " ".join(comparison.key_changes)
        assert "padding" in changes_text or "font-size" in changes_text
    
    def test_generate_summary_comparison_empty(self):
        """Test summary for empty proposal."""
        generator = BeforeAfterGenerator()
        
        proposal = DesignSystemProposal()
        
        summary = generator.generate_summary_comparison(proposal)
        
        assert "No design system changes" in summary
    
    def test_generate_summary_comparison_with_proposals(self):
        """Test summary for proposal with content."""
        generator = BeforeAfterGenerator()
        
        token = TokenProposal(
            token_name="--color-accent",
            token_type=TokenType.COLOR,
            proposed_value="#FF6B6B",
            rationale="Brand color",
            usage_count=10,
        )
        
        proposal = DesignSystemProposal(
            token_proposals=[token],
            impact_score=0.65,
            total_affected_screens=5,
        )
        
        summary = generator.generate_summary_comparison(proposal)
        
        assert "1 token proposals" in summary
        assert "5 screens affected" in summary
        assert "0.65" in summary


class TestConvenienceFunctions:
    """Tests for convenience functions."""
    
    def test_generate_token_comparison_func(self):
        """Test convenience function for token comparison."""
        proposal = TokenProposal(
            token_name="--color-test",
            token_type=TokenType.COLOR,
            proposed_value="#000000",
            rationale="Test",
        )
        
        comparison = generate_token_comparison(proposal)
        
        assert comparison is not None
        assert comparison.before_text is not None
    
    def test_generate_component_comparison_func(self):
        """Test convenience function for component comparison."""
        proposal = ComponentProposal(
            component_type="button",
            variant_name="primary",
            properties={},
            rationale="Test",
        )
        
        comparison = generate_component_comparison(proposal)
        
        assert comparison is not None
        assert comparison.before_text is not None
    
    def test_generate_summary_comparison_func(self):
        """Test convenience function for summary comparison."""
        proposal = DesignSystemProposal()
        
        summary = generate_summary_comparison(proposal)
        
        assert summary is not None


class TestBeforeAfterDescription:
    """Tests for BeforeAfterDescription output."""
    
    def test_to_markdown(self):
        """Test markdown generation."""
        generator = BeforeAfterGenerator()
        
        proposal = TokenProposal(
            token_name="--color-test",
            token_type=TokenType.COLOR,
            proposed_value="#000000",
            rationale="Test",
            usage_count=3,
        )
        
        comparison = generator.generate_token_comparison(proposal)
        md = comparison.to_markdown()
        
        assert "#### Before/After Comparison" in md
        assert "**Currently:**" in md
        assert "**Proposed:**" in md
    
    def test_to_summary(self):
        """Test one-line summary."""
        generator = BeforeAfterGenerator()
        
        proposal = TokenProposal(
            token_name="--color-test",
            token_type=TokenType.COLOR,
            proposed_value="#000000",
            rationale="Test",
            usage_count=3,
        )
        
        comparison = generator.generate_token_comparison(proposal)
        summary = comparison.to_summary()
        
        assert "Currently:" in summary
        assert "Proposed:" in summary
        assert "Benefit:" in summary