"""
Jobs/Ive design philosophy filter for audit findings.

Implements the "Jobs Filter" from SOUL.md to evaluate findings against
Steve Jobs and Jony Ive's design principles.
"""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# =============================================================================
# FILTER QUESTIONS
# =============================================================================

class FilterQuestion(str, Enum):
    """The Jobs Filter questions from SOUL.md."""
    
    OBVIOUS = "obvious"  # "Would a user need to be told this exists?"
    REMOVABLE = "removable"  # "Can this be removed without losing meaning?"
    INEVITABLE = "inevitable"  # "Does this feel inevitable?"
    REFINED = "refined"  # "Is this detail as refined as the details users will never see?"


# =============================================================================
# FILTER RESULT
# =============================================================================

class FilterResult(BaseModel):
    """Result of applying the Jobs filter to a finding."""
    
    passes: bool = Field(..., description="Whether the finding passes the filter")
    score: float = Field(..., ge=0.0, le=1.0, description="Filter score (0.0-1.0)")
    failed_questions: list[FilterQuestion] = Field(
        default_factory=list,
        description="Questions that failed"
    )
    rationale: Optional[str] = Field(
        default=None,
        description="Explanation of filter result"
    )
    
    def to_metadata(self) -> dict:
        """Convert to metadata dict for storage."""
        return {
            "passes": self.passes,
            "score": self.score,
            "failed_questions": [q.value for q in self.failed_questions],
            "rationale": self.rationale,
        }


# =============================================================================
# JOBS FILTER
# =============================================================================

class JobsFilter:
    """Filter for evaluating findings against Jobs/Ive design principles.
    
    The filter asks:
    1. "Would a user need to be told this exists?" — if yes, redesign
    2. "Can this be removed without losing meaning?" — if yes, remove
    3. "Does this feel inevitable?" — if no, it's not done
    4. "Is this detail as refined as details users will never see?" — back of fence
    
    Findings that fail the filter are flagged, NOT discarded.
    This allows human review of all findings including filtered ones.
    """
    
    def __init__(
        self,
        enabled: bool = True,
        pass_threshold: float = 0.5,
        question_weights: Optional[dict[FilterQuestion, float]] = None,
    ):
        """Initialize Jobs filter.
        
        Args:
            enabled: Whether the filter is enabled
            pass_threshold: Minimum score to pass (0.0-1.0)
            question_weights: Optional custom weights for questions
        """
        self.enabled = enabled
        self.pass_threshold = pass_threshold
        self.question_weights = question_weights or {
            FilterQuestion.OBVIOUS: 0.3,
            FilterQuestion.REMOVABLE: 0.3,
            FilterQuestion.INEVITABLE: 0.25,
            FilterQuestion.REFINED: 0.15,
        }
    
    def apply_filter(
        self,
        finding_description: str,
        obvious: Optional[bool] = None,
        removable: Optional[bool] = None,
        inevitable: Optional[bool] = None,
        refined: Optional[bool] = None,
    ) -> FilterResult:
        """Apply the Jobs filter to a finding.
        
        Args:
            finding_description: Description of the finding
            obvious: Would a user need to be told this exists? (True = needs telling = bad)
            removable: Can this be removed without losing meaning? (True = removable = bad)
            inevitable: Does this feel inevitable? (True = inevitable = good)
            refined: Is this detail as refined as hidden details? (True = refined = good)
            
        Returns:
            FilterResult with pass/fail and score
            
        Note:
            - For obvious/removable: False = passes (good)
            - For inevitable/refined: True = passes (good)
        """
        if not self.enabled:
            return FilterResult(
                passes=True,
                score=1.0,
                failed_questions=[],
                rationale="Filter disabled",
            )
        
        # Calculate scores for each question
        scores: dict[FilterQuestion, bool] = {
            FilterQuestion.OBVIOUS: not obvious if obvious is not None else True,
            FilterQuestion.REMOVABLE: not removable if removable is not None else True,
            FilterQuestion.INEVITABLE: inevitable if inevitable is not None else True,
            FilterQuestion.REFINED: refined if refined is not None else True,
        }
        
        # Identify failed questions
        failed = [q for q, passed in scores.items() if not passed]
        
        # Calculate weighted score
        total_score = 0.0
        for question, passed in scores.items():
            weight = self.question_weights.get(question, 0.25)
            if passed:
                total_score += weight
        
        # Normalize to 0.0-1.0
        max_possible = sum(self.question_weights.values())
        normalized_score = total_score / max_possible if max_possible > 0 else 1.0
        
        # Determine pass/fail
        passes = normalized_score >= self.pass_threshold
        
        # Generate rationale
        rationale = self._generate_rationale(failed, normalized_score, finding_description)
        
        return FilterResult(
            passes=passes,
            score=normalized_score,
            failed_questions=failed,
            rationale=rationale,
        )
    
    def apply_filter_from_dict(
        self,
        finding_description: str,
        answers: dict[str, bool],
    ) -> FilterResult:
        """Apply filter from a dictionary of answers.
        
        Args:
            finding_description: Description of the finding
            answers: Dict with keys 'obvious', 'removable', 'inevitable', 'refined'
            
        Returns:
            FilterResult
        """
        return self.apply_filter(
            finding_description=finding_description,
            obvious=answers.get("obvious"),
            removable=answers.get("removable"),
            inevitable=answers.get("inevitable"),
            refined=answers.get("refined"),
        )
    
    def _generate_rationale(
        self,
        failed: list[FilterQuestion],
        score: float,
        description: str,
    ) -> str:
        """Generate a rationale for the filter result."""
        if not failed:
            return f"Finding passes Jobs filter with score {score:.2f}"
        
        failed_names = {
            FilterQuestion.OBVIOUS: "not obvious to users",
            FilterQuestion.REMOVABLE: "removable without losing meaning",
            FilterQuestion.INEVITABLE: "does not feel inevitable",
            FilterQuestion.REFINED: "lacks refinement in details",
        }
        
        issues = [failed_names.get(q, q.value) for q in failed]
        
        return (
            f"Finding flagged ({score:.2f}): {description[:50]}... "
            f"- Issues: {', '.join(issues)}"
        )
    
    def evaluate_obvious(self, finding_description: str) -> bool:
        """Evaluate: Would a user need to be told this exists?
        
        Args:
            finding_description: Description of the issue
            
        Returns:
            True if user would need to be told (fails this question)
        """
        # Heuristic: Issues about discoverability, affordance, or clarity
        # typically fail this question
        keywords = [
            "hidden", "unclear", "confusing", "not obvious",
            "hard to find", "discoverability", "affordance",
            "user needs to know", "not intuitive",
        ]
        
        desc_lower = finding_description.lower()
        return any(kw in desc_lower for kw in keywords)
    
    def evaluate_removable(self, finding_description: str) -> bool:
        """Evaluate: Can this be removed without losing meaning?
        
        Args:
            finding_description: Description of the issue
            
        Returns:
            True if removable (fails this question)
        """
        # Heuristic: Issues about redundancy, clutter, or excess
        keywords = [
            "redundant", "duplicate", "unnecessary", "clutter",
            "excessive", "too many", "extra", "superfluous",
            "repetitive", "waste",
        ]
        
        desc_lower = finding_description.lower()
        return any(kw in desc_lower for kw in keywords)
    
    def evaluate_inevitable(self, finding_description: str) -> bool:
        """Evaluate: Does this feel inevitable?
        
        Args:
            finding_description: Description of the issue
            
        Returns:
            True if inevitable (passes this question)
        """
        # Heuristic: Issues about inconsistency, broken patterns, or
        # arbitrary choices typically fail this question
        fail_keywords = [
            "inconsistent", "arbitrary", "random", "broken",
            "mismatched", "doesn't match", "wrong", "error",
            "bug", "incorrect",
        ]
        
        desc_lower = finding_description.lower()
        return not any(kw in desc_lower for kw in fail_keywords)
    
    def evaluate_refined(self, finding_description: str) -> bool:
        """Evaluate: Is this detail as refined as details users will never see?
        
        Args:
            finding_description: Description of the issue
            
        Returns:
            True if refined (passes this question)
        """
        # Heuristic: Issues about polish, attention to detail, precision
        fail_keywords = [
            "misaligned", "off by", "rough", "unfinished",
            "sloppy", "imprecise", "pixel", "alignment",
            "spacing issue", "inconsistent spacing",
        ]
        
        desc_lower = finding_description.lower()
        return not any(kw in desc_lower for kw in fail_keywords)
    
    def auto_evaluate(self, finding_description: str) -> FilterResult:
        """Automatically evaluate a finding using heuristics.
        
        WARNING: This uses simple keyword matching and is not a replacement
        for human judgment. Use for initial filtering only.
        
        Args:
            finding_description: Description of the finding
            
        Returns:
            FilterResult based on heuristic evaluation
        """
        if not self.enabled:
            return FilterResult(
                passes=True,
                score=1.0,
                failed_questions=[],
                rationale="Filter disabled",
            )
        
        # Use heuristics to evaluate each question
        obvious = self.evaluate_obvious(finding_description)
        removable = self.evaluate_removable(finding_description)
        inevitable = self.evaluate_inevitable(finding_description)
        refined = self.evaluate_refined(finding_description)
        
        return self.apply_filter(
            finding_description=finding_description,
            obvious=obvious,
            removable=removable,
            inevitable=inevitable,
            refined=refined,
        )
    
    def configure(
        self,
        enabled: Optional[bool] = None,
        pass_threshold: Optional[float] = None,
    ) -> None:
        """Update filter configuration.
        
        Args:
            enabled: Enable/disable filter
            pass_threshold: New pass threshold
        """
        if enabled is not None:
            self.enabled = enabled
        if pass_threshold is not None:
            self.pass_threshold = pass_threshold