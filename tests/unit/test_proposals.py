"""
Unit tests for proposal generator module.
"""

import pytest

from src.plan.proposals import (
    ProposalGenerator,
    calculate_impact_score,
    determine_priority,
    generate_design_system_proposals,
)
from src.plan.proposal_models import (
    TokenProposal,
    ComponentProposal,
    Priority,
    TokenType,
)


class TestCalculateImpactScore:
    """Tests for impact score calculation."""
    
    def test_impact_score_token_proposal(self):
        """Test impact score for token proposal."""
        proposal = TokenProposal(
            token_name="--color-test",
            token_type=TokenType.COLOR,
            proposed_value="#FF6B6B",
            rationale="Test",
            usage_count=5,
            affected_screens=["s1", "s2", "s3"],
        )
        
        score = calculate_impact_score(proposal, total_screens=10)
        
        assert 0.0 <= score <= 1.0
    
    def test_impact_score_component_proposal(self):
        """Test impact score for component proposal."""
        proposal = ComponentProposal(
            component_type="button",
            variant_name="large",
            properties={},
            rationale="Test",
            detected_instances=8,
            affected_screens=["s1", "s2", "s3", "s4"],
        )
        
        score = calculate_impact_score(proposal, total_screens=10)
        
        assert 0.0 <= score <= 1.0
    
    def test_impact_score_high_usage(self):
        """Test impact score with high usage."""
        proposal = TokenProposal(
            token_name="--color-test",
            token_type=TokenType.COLOR,
            proposed_value="#FF6B6B",
            rationale="Test",
            usage_count=100,
            affected_screens=["s1"],
        )
        
        score = calculate_impact_score(proposal, total_screens=1)
        
        # High usage should produce higher score
        assert score > 0.3
    
    def test_impact_score_low_usage(self):
        """Test impact score with low usage."""
        proposal = TokenProposal(
            token_name="--color-test",
            token_type=TokenType.COLOR,
            proposed_value="#FF6B6B",
            rationale="Test",
            usage_count=1,
            affected_screens=["s1"],
        )
        
        score = calculate_impact_score(proposal, total_screens=100)
        
        # Low usage relative to screens should produce lower score
        assert score < 0.5


class TestDeterminePriority:
    """Tests for priority determination."""
    
    def test_priority_critical(self):
        """Test critical priority for high impact."""
        assert determine_priority(0.8) == Priority.CRITICAL
        assert determine_priority(0.75) == Priority.CRITICAL
    
    def test_priority_high(self):
        """Test high priority."""
        assert determine_priority(0.6) == Priority.HIGH
        assert determine_priority(0.55) == Priority.HIGH
    
    def test_priority_medium(self):
        """Test medium priority."""
        assert determine_priority(0.4) == Priority.MEDIUM
        assert determine_priority(0.35) == Priority.MEDIUM
    
    def test_priority_low(self):
        """Test low priority."""
        assert determine_priority(0.2) == Priority.LOW
        assert determine_priority(0.1) == Priority.LOW


class TestProposalGenerator:
    """Tests for ProposalGenerator class."""
    
    def test_create_generator_default(self):
        """Test creating generator with defaults."""
        generator = ProposalGenerator()
        
        assert generator.usage_threshold == 3
        assert generator.token_analyzer is not None
    
    def test_create_generator_custom(self):
        """Test creating generator with custom settings."""
        generator = ProposalGenerator(usage_threshold=5)
        
        assert generator.usage_threshold == 5
    
    def test_create_token_proposal_color(self):
        """Test creating token proposal for color."""
        generator = ProposalGenerator()
        
        pattern = {
            "token_type": "color",
            "value": "#FF6B6B",
            "count": 5,
            "screens": ["s1", "s2"],
        }
        
        proposal = generator.create_token_proposal(pattern)
        
        assert proposal.token_type == TokenType.COLOR
        assert proposal.proposed_value == "#FF6B6B"
        assert proposal.usage_count == 5
    
    def test_create_token_proposal_spacing(self):
        """Test creating token proposal for spacing."""
        generator = ProposalGenerator()
        
        pattern = {
            "token_type": "spacing",
            "value": "28px",
            "count": 3,
            "screens": ["s1"],
        }
        
        proposal = generator.create_token_proposal(pattern)
        
        assert proposal.token_type == TokenType.SPACING
        assert proposal.proposed_value == "28px"
    
    def test_create_component_proposal(self):
        """Test creating component proposal."""
        generator = ProposalGenerator()
        
        findings = [
            {"entity_id": "screen-1", "issue": "Inconsistent padding"},
            {"entity_id": "screen-2", "issue": "Inconsistent padding"},
        ]
        
        proposal = generator.create_component_proposal(
            component_type="button",
            variant_name="large",
            properties={"padding": "16px 32px"},
            findings=findings,
        )
        
        assert proposal.component_type == "button"
        assert proposal.variant_name == "large"
        assert proposal.detected_instances == 2
    
    def test_prioritize_proposals(self):
        """Test prioritizing proposals."""
        generator = ProposalGenerator()
        
        low_usage = TokenProposal(
            token_name="--color-low",
            token_type=TokenType.COLOR,
            proposed_value="#111111",
            rationale="Low usage",
            usage_count=3,
            affected_screens=["s1"],
        )
        
        high_usage = TokenProposal(
            token_name="--color-high",
            token_type=TokenType.COLOR,
            proposed_value="#222222",
            rationale="High usage",
            usage_count=50,
            affected_screens=["s1", "s2", "s3", "s4", "s5"],
        )
        
        prioritized = generator.prioritize_proposals(
            [low_usage, high_usage],
            total_screens=5,
        )
        
        # High usage should be first
        assert prioritized[0].token_name == "--color-high"
        assert prioritized[1].token_name == "--color-low"
    
    def test_generate_proposals_empty(self):
        """Test generating proposals from empty findings."""
        generator = ProposalGenerator()
        
        proposal = generator.generate_proposals([])
        
        assert proposal.total_proposals() == 0
        # Empty proposals have 0.0 impact score, which is LOW priority
        assert proposal.priority == Priority.LOW
    
    def test_generate_proposals_with_findings(self):
        """Test generating proposals from findings."""
        generator = ProposalGenerator(usage_threshold=2)
        
        findings = [
            {"dimension": "color", "metadata": {"color": "#ABCDEF"}, "entity_id": "s1"},
            {"dimension": "color", "metadata": {"color": "#ABCDEF"}, "entity_id": "s2"},
        ]
        
        proposal = generator.generate_proposals(
            findings=findings,
            screen_ids=["s1", "s2"],
            audit_session_id="session-123",
        )
        
        assert proposal.total_proposals() >= 1
        assert proposal.audit_session_id == "session-123"
    
    def test_generate_proposals_with_before_after(self):
        """Test generating proposals includes before/after."""
        generator = ProposalGenerator(usage_threshold=2)
        
        findings = [
            {"dimension": "color", "metadata": {"color": "#ABCDEF"}, "entity_id": "s1"},
            {"dimension": "color", "metadata": {"color": "#ABCDEF"}, "entity_id": "s2"},
        ]
        
        proposal = generator.generate_proposals(findings)
        
        # Should have before/after summaries for top proposals
        assert isinstance(proposal.before_after_summaries, dict)


class TestGenerateDesignSystemProposals:
    """Tests for convenience function."""
    
    def test_generate_design_system_proposals(self):
        """Test convenience function."""
        findings = [
            {"dimension": "color", "metadata": {"color": "#ABCDEF"}, "entity_id": "s1"},
            {"dimension": "color", "metadata": {"color": "#ABCDEF"}, "entity_id": "s2"},
            {"dimension": "color", "metadata": {"color": "#ABCDEF"}, "entity_id": "s3"},
        ]
        
        proposal = generate_design_system_proposals(
            findings=findings,
            usage_threshold=3,
        )
        
        assert proposal is not None
        assert isinstance(proposal.total_proposals(), int)


class TestAnalyzeComponentPatterns:
    """Tests for component pattern analysis."""
    
    def test_analyze_size_variants(self):
        """Test detecting size variants."""
        generator = ProposalGenerator()
        
        findings = [
            {"metadata": {"component_type": "button", "size": 14}},
            {"metadata": {"component_type": "button", "size": 14}},
            {"metadata": {"component_type": "button", "size": 18}},
            {"metadata": {"component_type": "button", "size": 18}},
        ]
        
        proposals = generator._analyze_component_patterns(findings)
        
        # Should detect multiple size variants
        assert len(proposals) >= 2
    
    def test_analyze_style_variants(self):
        """Test detecting style variants."""
        generator = ProposalGenerator()
        
        findings = [
            {"metadata": {"component_type": "card", "style": "elevated"}},
            {"metadata": {"component_type": "card", "style": "elevated"}},
            {"metadata": {"component_type": "card", "style": "outlined"}},
            {"metadata": {"component_type": "card", "style": "outlined"}},
        ]
        
        proposals = generator._analyze_component_patterns(findings)
        
        # Should detect style variants
        assert len(proposals) >= 2