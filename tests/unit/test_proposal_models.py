"""
Unit tests for design system proposal models.
"""

import pytest
from datetime import datetime

from src.plan.proposal_models import (
    ProposalType,
    TokenType,
    Priority,
    TokenProposal,
    ComponentVariant,
    ComponentProposal,
    BeforeAfterDescription,
    DesignSystemProposal,
)


class TestProposalType:
    """Tests for ProposalType enum."""
    
    def test_proposal_types_exist(self):
        """Test all expected proposal types exist."""
        assert ProposalType.NEW_TOKEN == "new_token"
        assert ProposalType.TOKEN_VARIANT == "token_variant"
        assert ProposalType.COMPONENT_VARIANT == "component_variant"
        assert ProposalType.STANDARD_UPDATE == "standard_update"
    
    def test_proposal_type_count(self):
        """Test we have 4 proposal types."""
        assert len(ProposalType) == 4


class TestTokenType:
    """Tests for TokenType enum."""
    
    def test_token_types_exist(self):
        """Test all expected token types exist."""
        assert TokenType.COLOR == "color"
        assert TokenType.SPACING == "spacing"
        assert TokenType.TYPOGRAPHY == "typography"
        assert TokenType.RADIUS == "radius"
        assert TokenType.SHADOW == "shadow"
        assert TokenType.MOTION == "motion"
    
    def test_token_type_count(self):
        """Test we have 6 token types."""
        assert len(TokenType) == 6


class TestPriority:
    """Tests for Priority enum."""
    
    def test_priorities_exist(self):
        """Test all expected priorities exist."""
        assert Priority.CRITICAL == "critical"
        assert Priority.HIGH == "high"
        assert Priority.MEDIUM == "medium"
        assert Priority.LOW == "low"
    
    def test_priority_count(self):
        """Test we have 4 priority levels."""
        assert len(Priority) == 4


class TestTokenProposal:
    """Tests for TokenProposal model."""
    
    def test_create_token_proposal_minimal(self):
        """Test creating a token proposal with minimal fields."""
        proposal = TokenProposal(
            token_name="--color-accent",
            token_type=TokenType.COLOR,
            proposed_value="#FF6B6B",
            rationale="Brand accent color",
        )
        
        assert proposal.token_name == "--color-accent"
        assert proposal.token_type == TokenType.COLOR
        assert proposal.proposed_value == "#FF6B6B"
        assert proposal.rationale == "Brand accent color"
        assert proposal.usage_count == 1
        assert proposal.affected_screens == []
        assert proposal.existing_token_conflict is None
    
    def test_create_token_proposal_full(self):
        """Test creating a token proposal with all fields."""
        proposal = TokenProposal(
            token_name="--spacing-xl",
            token_type=TokenType.SPACING,
            proposed_value="24px",
            rationale="Extra large spacing",
            usage_count=5,
            affected_screens=["screen-1", "screen-2", "screen-3"],
            existing_token_conflict="--space-6",
        )
        
        assert proposal.token_name == "--spacing-xl"
        assert proposal.token_type == TokenType.SPACING
        assert proposal.proposed_value == "24px"
        assert proposal.usage_count == 5
        assert len(proposal.affected_screens) == 3
        assert proposal.existing_token_conflict == "--space-6"
    
    def test_token_proposal_frozen(self):
        """Test TokenProposal is immutable (frozen)."""
        proposal = TokenProposal(
            token_name="--color-test",
            token_type=TokenType.COLOR,
            proposed_value="#000000",
            rationale="Test",
        )
        
        with pytest.raises(Exception):
            proposal.token_name = "--color-changed"
    
    def test_token_proposal_to_markdown(self):
        """Test markdown generation."""
        proposal = TokenProposal(
            token_name="--color-accent",
            token_type=TokenType.COLOR,
            proposed_value="#FF6B6B",
            rationale="Brand accent color",
            usage_count=3,
        )
        
        md = proposal.to_markdown()
        
        assert "### Token Proposal: `--color-accent`" in md
        assert "**Type:** color" in md
        assert "**Proposed Value:** `#FF6B6B`" in md
        assert "**Usage Count:** 3" in md
        assert "**Rationale:** Brand accent color" in md
    
    def test_token_proposal_to_markdown_with_conflict(self):
        """Test markdown includes conflict warning."""
        proposal = TokenProposal(
            token_name="--color-accent",
            token_type=TokenType.COLOR,
            proposed_value="#FF6B6B",
            rationale="Test",
            existing_token_conflict="--color-primary",
        )
        
        md = proposal.to_markdown()
        
        assert "⚠️ **Potential Conflict:**" in md
        assert "--color-primary" in md
    
    def test_token_proposal_to_markdown_with_screens(self):
        """Test markdown includes affected screens count."""
        proposal = TokenProposal(
            token_name="--spacing-lg",
            token_type=TokenType.SPACING,
            proposed_value="16px",
            rationale="Test",
            affected_screens=["s1", "s2", "s3"],
        )
        
        md = proposal.to_markdown()
        
        assert "**Affected Screens:** 3 screens" in md


class TestComponentVariant:
    """Tests for ComponentVariant model."""
    
    def test_create_component_variant(self):
        """Test creating a component variant."""
        variant = ComponentVariant(
            variant_name="elevated",
            properties={"box-shadow": "0 4px 6px rgba(0,0,0,0.1)"},
            description="Elevated card with shadow",
        )
        
        assert variant.variant_name == "elevated"
        assert "box-shadow" in variant.properties
        assert variant.description == "Elevated card with shadow"
    
    def test_component_variant_frozen(self):
        """Test ComponentVariant is immutable."""
        variant = ComponentVariant(
            variant_name="test",
            properties={},
        )
        
        with pytest.raises(Exception):
            variant.variant_name = "changed"


class TestComponentProposal:
    """Tests for ComponentProposal model."""
    
    def test_create_component_proposal_minimal(self):
        """Test creating a component proposal with minimal fields."""
        proposal = ComponentProposal(
            component_type="card",
            variant_name="elevated",
            properties={"box-shadow": "0 4px 6px rgba(0,0,0,0.1)"},
            rationale="Cards need elevation variant",
        )
        
        assert proposal.component_type == "card"
        assert proposal.variant_name == "elevated"
        assert proposal.rationale == "Cards need elevation variant"
        assert proposal.detected_instances == 1
        assert proposal.affected_screens == []
    
    def test_create_component_proposal_full(self):
        """Test creating a component proposal with all fields."""
        proposal = ComponentProposal(
            component_type="button",
            variant_name="large",
            properties={"padding": "16px 32px", "font-size": "18px"},
            rationale="Large button variant for CTAs",
            detected_instances=5,
            affected_screens=["screen-1", "screen-2"],
            example_components=["btn-1", "btn-2"],
        )
        
        assert proposal.component_type == "button"
        assert proposal.variant_name == "large"
        assert proposal.detected_instances == 5
        assert len(proposal.affected_screens) == 2
        assert len(proposal.example_components) == 2
    
    def test_component_proposal_to_markdown(self):
        """Test markdown generation."""
        proposal = ComponentProposal(
            component_type="card",
            variant_name="outlined",
            properties={"border": "1px solid #E5E7EB", "box-shadow": "none"},
            rationale="Outlined card variant",
            detected_instances=3,
        )
        
        md = proposal.to_markdown()
        
        assert "### Component Variant Proposal: `card-outlined`" in md
        assert "**Detected Instances:** 3" in md
        assert "**Rationale:** Outlined card variant" in md
        assert "`border: 1px solid #E5E7EB`" in md


class TestBeforeAfterDescription:
    """Tests for BeforeAfterDescription model."""
    
    def test_create_before_after_minimal(self):
        """Test creating before/after with minimal fields."""
        desc = BeforeAfterDescription(
            before_text="No design token",
            after_text="Use --color-primary token",
        )
        
        assert desc.before_text == "No design token"
        assert desc.after_text == "Use --color-primary token"
        assert desc.key_changes == []
        assert desc.benefit == ""
    
    def test_create_before_after_full(self):
        """Test creating before/after with all fields."""
        desc = BeforeAfterDescription(
            before_text="Inconsistent spacing",
            after_text="Consistent 8px grid",
            key_changes=["Add --spacing-md token", "Apply to all components"],
            benefit="Predictable spacing rhythm",
        )
        
        assert desc.before_text == "Inconsistent spacing"
        assert desc.after_text == "Consistent 8px grid"
        assert len(desc.key_changes) == 2
        assert desc.benefit == "Predictable spacing rhythm"
    
    def test_to_markdown(self):
        """Test markdown generation."""
        desc = BeforeAfterDescription(
            before_text="No token",
            after_text="Use token",
            benefit="Consistency",
            key_changes=["Change 1", "Change 2"],
        )
        
        md = desc.to_markdown()
        
        assert "#### Before/After Comparison" in md
        assert "**Currently:** No token" in md
        assert "**Proposed:** Use token" in md
        assert "**Benefit:** Consistency" in md
        assert "- Change 1" in md
    
    def test_to_summary(self):
        """Test one-line summary generation."""
        desc = BeforeAfterDescription(
            before_text="No token",
            after_text="Use token",
            benefit="Consistency",
        )
        
        summary = desc.to_summary()
        
        assert summary == "Currently: No token. Proposed: Use token. Benefit: Consistency"


class TestDesignSystemProposal:
    """Tests for DesignSystemProposal aggregate model."""
    
    def test_create_empty_proposal(self):
        """Test creating an empty proposal."""
        proposal = DesignSystemProposal()
        
        assert proposal.token_proposals == []
        assert proposal.component_proposals == []
        assert proposal.priority == Priority.MEDIUM
        assert proposal.impact_score == 0.0
        assert proposal.total_proposals() == 0
    
    def test_create_proposal_with_tokens(self):
        """Test creating a proposal with token proposals."""
        token = TokenProposal(
            token_name="--color-accent",
            token_type=TokenType.COLOR,
            proposed_value="#FF6B6B",
            rationale="Brand color",
        )
        
        proposal = DesignSystemProposal(
            token_proposals=[token],
            priority=Priority.HIGH,
            impact_score=0.75,
        )
        
        assert len(proposal.token_proposals) == 1
        assert proposal.total_proposals() == 1
        assert proposal.priority == Priority.HIGH
        assert proposal.impact_score == 0.75
    
    def test_create_proposal_with_components(self):
        """Test creating a proposal with component proposals."""
        component = ComponentProposal(
            component_type="button",
            variant_name="large",
            properties={"padding": "16px 32px"},
            rationale="Large CTA buttons",
        )
        
        proposal = DesignSystemProposal(
            component_proposals=[component],
        )
        
        assert len(proposal.component_proposals) == 1
        assert proposal.total_proposals() == 1
    
    def test_proposals_by_type(self):
        """Test proposals_by_type method."""
        token = TokenProposal(
            token_name="--color-test",
            token_type=TokenType.COLOR,
            proposed_value="#000000",
            rationale="Test",
        )
        component = ComponentProposal(
            component_type="card",
            variant_name="elevated",
            properties={},
            rationale="Test",
        )
        
        proposal = DesignSystemProposal(
            token_proposals=[token],
            component_proposals=[component],
        )
        
        by_type = proposal.proposals_by_type()
        
        assert by_type["token"] == 1
        assert by_type["component"] == 1
        assert by_type["total"] == 2
    
    def test_get_highest_impact_proposal_empty(self):
        """Test get_highest_impact_proposal returns None for empty."""
        proposal = DesignSystemProposal()
        
        assert proposal.get_highest_impact_proposal() is None
    
    def test_get_highest_impact_proposal_token(self):
        """Test get_highest_impact_proposal returns highest usage token."""
        token1 = TokenProposal(
            token_name="--color-a",
            token_type=TokenType.COLOR,
            proposed_value="#111111",
            rationale="Test",
            usage_count=3,
        )
        token2 = TokenProposal(
            token_name="--color-b",
            token_type=TokenType.COLOR,
            proposed_value="#222222",
            rationale="Test",
            usage_count=10,
        )
        
        proposal = DesignSystemProposal(
            token_proposals=[token1, token2],
        )
        
        highest = proposal.get_highest_impact_proposal()
        
        assert highest is not None
        assert highest.token_name == "--color-b"
    
    def test_get_highest_impact_proposal_component(self):
        """Test get_highest_impact_proposal can return component."""
        token = TokenProposal(
            token_name="--color-a",
            token_type=TokenType.COLOR,
            proposed_value="#111111",
            rationale="Test",
            usage_count=3,
        )
        component = ComponentProposal(
            component_type="button",
            variant_name="large",
            properties={},
            rationale="Test",
            detected_instances=15,
        )
        
        proposal = DesignSystemProposal(
            token_proposals=[token],
            component_proposals=[component],
        )
        
        highest = proposal.get_highest_impact_proposal()
        
        assert highest is not None
        assert highest.component_type == "button"
    
    def test_to_markdown(self):
        """Test markdown generation for full proposal."""
        token = TokenProposal(
            token_name="--color-accent",
            token_type=TokenType.COLOR,
            proposed_value="#FF6B6B",
            rationale="Brand color",
        )
        
        proposal = DesignSystemProposal(
            token_proposals=[token],
            priority=Priority.HIGH,
            impact_score=0.65,
            total_affected_screens=5,
        )
        
        md = proposal.to_markdown()
        
        assert "# Design System Proposal" in md
        assert "**Priority:** HIGH" in md
        assert "**Impact Score:** 0.65" in md
        assert "**Token Proposals:** 1" in md
        assert "**Total Affected Screens:** 5" in md
    
    def test_to_json_dict(self):
        """Test JSON dict export."""
        token = TokenProposal(
            token_name="--color-test",
            token_type=TokenType.COLOR,
            proposed_value="#000000",
            rationale="Test",
        )
        
        proposal = DesignSystemProposal(
            token_proposals=[token],
            priority=Priority.HIGH,
            impact_score=0.5,
        )
        
        json_dict = proposal.to_json_dict()
        
        assert json_dict["priority"] == "high"
        assert json_dict["impact_score"] == 0.5
        assert json_dict["proposals_by_type"]["token"] == 1
        assert len(json_dict["token_proposals"]) == 1
    
    def test_proposal_has_id(self):
        """Test proposal has auto-generated ID."""
        proposal = DesignSystemProposal()
        
        assert proposal.id is not None
        assert len(proposal.id) == 36  # UUID format
    
    def test_proposal_has_created_at(self):
        """Test proposal has created_at timestamp."""
        proposal = DesignSystemProposal()
        
        assert proposal.created_at is not None
        assert isinstance(proposal.created_at, datetime)


class TestModelValidation:
    """Tests for model validation."""
    
    def test_token_proposal_requires_name(self):
        """Test token proposal requires token_name."""
        with pytest.raises(Exception):
            TokenProposal(
                token_type=TokenType.COLOR,
                proposed_value="#000000",
                rationale="Test",
            )
    
    def test_token_proposal_requires_rationale(self):
        """Test token proposal requires rationale."""
        with pytest.raises(Exception):
            TokenProposal(
                token_name="--color-test",
                token_type=TokenType.COLOR,
                proposed_value="#000000",
            )
    
    def test_usage_count_minimum(self):
        """Test usage_count must be at least 1."""
        with pytest.raises(Exception):
            TokenProposal(
                token_name="--color-test",
                token_type=TokenType.COLOR,
                proposed_value="#000000",
                rationale="Test",
                usage_count=0,
            )
    
    def test_impact_score_range(self):
        """Test impact_score must be between 0 and 1."""
        # Valid range
        proposal = DesignSystemProposal(impact_score=0.5)
        assert proposal.impact_score == 0.5
        
        # Invalid high
        with pytest.raises(Exception):
            DesignSystemProposal(impact_score=1.5)
        
        # Invalid low
        with pytest.raises(Exception):
            DesignSystemProposal(impact_score=-0.5)