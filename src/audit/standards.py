"""
Standards reference system for audit findings.

Provides registry of design tokens and WCAG criteria for linking findings to standards.
"""

import re
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field

from .models import DesignTokenReference, WCAGReference, StandardsReference


# =============================================================================
# WCAG 2.1 CRITERIA (AA Level)
# =============================================================================

WCAG_CRITERIA: dict[str, WCAGReference] = {
    # Perceivable
    "1.1.1": WCAGReference(
        criterion="1.1.1",
        name="Non-text Content",
        level="A",
        url="https://www.w3.org/WAI/WCAG21/Understanding/non-text-content.html"
    ),
    "1.3.1": WCAGReference(
        criterion="1.3.1",
        name="Info and Relationships",
        level="A",
        url="https://www.w3.org/WAI/WCAG21/Understanding/info-and-relationships.html"
    ),
    "1.3.2": WCAGReference(
        criterion="1.3.2",
        name="Meaningful Sequence",
        level="A",
        url="https://www.w3.org/WAI/WCAG21/Understanding/meaningful-sequence.html"
    ),
    "1.3.3": WCAGReference(
        criterion="1.3.3",
        name="Sensory Characteristics",
        level="A",
        url="https://www.w3.org/WAI/WCAG21/Understanding/sensory-characteristics.html"
    ),
    "1.4.1": WCAGReference(
        criterion="1.4.1",
        name="Use of Color",
        level="A",
        url="https://www.w3.org/WAI/WCAG21/Understanding/use-of-color.html"
    ),
    "1.4.3": WCAGReference(
        criterion="1.4.3",
        name="Contrast (Minimum)",
        level="AA",
        url="https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum.html"
    ),
    "1.4.4": WCAGReference(
        criterion="1.4.4",
        name="Resize Text",
        level="AA",
        url="https://www.w3.org/WAI/WCAG21/Understanding/resize-text.html"
    ),
    "1.4.5": WCAGReference(
        criterion="1.4.5",
        name="Images of Text",
        level="AA",
        url="https://www.w3.org/WAI/WCAG21/Understanding/images-of-text.html"
    ),
    "1.4.10": WCAGReference(
        criterion="1.4.10",
        name="Reflow",
        level="AA",
        url="https://www.w3.org/WAI/WCAG21/Understanding/reflow.html"
    ),
    "1.4.11": WCAGReference(
        criterion="1.4.11",
        name="Non-text Contrast",
        level="AA",
        url="https://www.w3.org/WAI/WCAG21/Understanding/non-text-contrast.html"
    ),
    "1.4.12": WCAGReference(
        criterion="1.4.12",
        name="Text Spacing",
        level="AA",
        url="https://www.w3.org/WAI/WCAG21/Understanding/text-spacing.html"
    ),
    "1.4.13": WCAGReference(
        criterion="1.4.13",
        name="Content on Hover or Focus",
        level="AA",
        url="https://www.w3.org/WAI/WCAG21/Understanding/content-on-hover-or-focus.html"
    ),
    
    # Operable
    "2.1.1": WCAGReference(
        criterion="2.1.1",
        name="Keyboard",
        level="A",
        url="https://www.w3.org/WAI/WCAG21/Understanding/keyboard.html"
    ),
    "2.1.2": WCAGReference(
        criterion="2.1.2",
        name="No Keyboard Trap",
        level="A",
        url="https://www.w3.org/WAI/WCAG21/Understanding/no-keyboard-trap.html"
    ),
    "2.4.1": WCAGReference(
        criterion="2.4.1",
        name="Bypass Blocks",
        level="A",
        url="https://www.w3.org/WAI/WCAG21/Understanding/bypass-blocks.html"
    ),
    "2.4.2": WCAGReference(
        criterion="2.4.2",
        name="Page Titled",
        level="A",
        url="https://www.w3.org/WAI/WCAG21/Understanding/page-titled.html"
    ),
    "2.4.3": WCAGReference(
        criterion="2.4.3",
        name="Focus Order",
        level="A",
        url="https://www.w3.org/WAI/WCAG21/Understanding/focus-order.html"
    ),
    "2.4.4": WCAGReference(
        criterion="2.4.4",
        name="Link Purpose (In Context)",
        level="A",
        url="https://www.w3.org/WAI/WCAG21/Understanding/link-purpose-in-context.html"
    ),
    "2.4.5": WCAGReference(
        criterion="2.4.5",
        name="Multiple Ways",
        level="AA",
        url="https://www.w3.org/WAI/WCAG21/Understanding/multiple-ways.html"
    ),
    "2.4.6": WCAGReference(
        criterion="2.4.6",
        name="Headings and Labels",
        level="AA",
        url="https://www.w3.org/WAI/WCAG21/Understanding/headings-and-labels.html"
    ),
    "2.4.7": WCAGReference(
        criterion="2.4.7",
        name="Focus Visible",
        level="AA",
        url="https://www.w3.org/WAI/WCAG21/Understanding/focus-visible.html"
    ),
    "2.5.1": WCAGReference(
        criterion="2.5.1",
        name="Pointer Gestures",
        level="A",
        url="https://www.w3.org/WAI/WCAG21/Understanding/pointer-gestures.html"
    ),
    "2.5.2": WCAGReference(
        criterion="2.5.2",
        name="Pointer Cancellation",
        level="A",
        url="https://www.w3.org/WAI/WCAG21/Understanding/pointer-cancellation.html"
    ),
    "2.5.3": WCAGReference(
        criterion="2.5.3",
        name="Label in Name",
        level="A",
        url="https://www.w3.org/WAI/WCAG21/Understanding/label-in-name.html"
    ),
    "2.5.4": WCAGReference(
        criterion="2.5.4",
        name="Motion Actuation",
        level="A",
        url="https://www.w3.org/WAI/WCAG21/Understanding/motion-actuation.html"
    ),
    
    # Understandable
    "3.1.1": WCAGReference(
        criterion="3.1.1",
        name="Language of Page",
        level="A",
        url="https://www.w3.org/WAI/WCAG21/Understanding/language-of-page.html"
    ),
    "3.1.2": WCAGReference(
        criterion="3.1.2",
        name="Language of Parts",
        level="AA",
        url="https://www.w3.org/WAI/WCAG21/Understanding/language-of-parts.html"
    ),
    "3.2.1": WCAGReference(
        criterion="3.2.1",
        name="On Focus",
        level="A",
        url="https://www.w3.org/WAI/WCAG21/Understanding/on-focus.html"
    ),
    "3.2.2": WCAGReference(
        criterion="3.2.2",
        name="On Input",
        level="A",
        url="https://www.w3.org/WAI/WCAG21/Understanding/on-input.html"
    ),
    "3.2.3": WCAGReference(
        criterion="3.2.3",
        name="Consistent Navigation",
        level="AA",
        url="https://www.w3.org/WAI/WCAG21/Understanding/consistent-navigation.html"
    ),
    "3.2.4": WCAGReference(
        criterion="3.2.4",
        name="Consistent Identification",
        level="AA",
        url="https://www.w3.org/WAI/WCAG21/Understanding/consistent-identification.html"
    ),
    "3.3.1": WCAGReference(
        criterion="3.3.1",
        name="Error Identification",
        level="A",
        url="https://www.w3.org/WAI/WCAG21/Understanding/error-identification.html"
    ),
    "3.3.2": WCAGReference(
        criterion="3.3.2",
        name="Labels or Instructions",
        level="A",
        url="https://www.w3.org/WAI/WCAG21/Understanding/labels-or-instructions.html"
    ),
    "3.3.3": WCAGReference(
        criterion="3.3.3",
        name="Error Suggestion",
        level="AA",
        url="https://www.w3.org/WAI/WCAG21/Understanding/error-suggestion.html"
    ),
    "3.3.4": WCAGReference(
        criterion="3.3.4",
        name="Error Prevention (Legal, Financial, Data)",
        level="AA",
        url="https://www.w3.org/WAI/WCAG21/Understanding/error-prevention-legal-financial-data.html"
    ),
    
    # Robust
    "4.1.1": WCAGReference(
        criterion="4.1.1",
        name="Parsing",
        level="A",
        url="https://www.w3.org/WAI/WCAG21/Understanding/parsing.html"
    ),
    "4.1.2": WCAGReference(
        criterion="4.1.2",
        name="Name, Role, Value",
        level="A",
        url="https://www.w3.org/WAI/WCAG21/Understanding/name-role-value.html"
    ),
    "4.1.3": WCAGReference(
        criterion="4.1.3",
        name="Status Messages",
        level="AA",
        url="https://www.w3.org/WAI/WCAG21/Understanding/status-messages.html"
    ),
}


# =============================================================================
# DESIGN TOKEN REGISTRY
# =============================================================================

class DesignToken(BaseModel):
    """Design token from design system."""
    
    name: str = Field(..., description="Token name (e.g., --color-primary)")
    token_type: str = Field(..., description="Token type (color, spacing, etc.)")
    value: Optional[str] = Field(default=None, description="Token value")
    description: Optional[str] = Field(default=None, description="Human-readable description")


class StandardsRegistry:
    """Registry of design standards for linking findings to standards.
    
    Loads design tokens from design_system/tokens.md at initialization.
    """
    
    def __init__(self, design_system_path: Optional[Path] = None):
        """Initialize standards registry.
        
        Args:
            design_system_path: Path to design_system directory
        """
        self._tokens: dict[str, DesignToken] = {}
        self._tokens_by_type: dict[str, list[DesignToken]] = {}
        self._wcag = WCAG_CRITERIA.copy()
        
        # Load design tokens if path provided
        if design_system_path:
            self.load_design_tokens(design_system_path)
        else:
            # Try default path
            default_path = Path("design_system/tokens.md")
            if default_path.exists():
                self.load_design_tokens(default_path)
    
    def load_design_tokens(self, path: Path) -> int:
        """Load design tokens from markdown file.
        
        Args:
            path: Path to tokens.md file
            
        Returns:
            Number of tokens loaded
        """
        if not path.exists():
            return 0
        
        content = path.read_text()
        tokens = self._parse_tokens_markdown(content)
        
        for token in tokens:
            self._tokens[token.name] = token
            if token.token_type not in self._tokens_by_type:
                self._tokens_by_type[token.token_type] = []
            self._tokens_by_type[token.token_type].append(token)
        
        return len(tokens)
    
    def _parse_tokens_markdown(self, content: str) -> list[DesignToken]:
        """Parse design tokens from markdown content.
        
        Expects format:
        | Token | Value | Usage |
        |-------|-------|-------|
        | `--color-primary` | TBD | Primary brand color |
        
        Args:
            content: Markdown content
            
        Returns:
            List of DesignToken objects
        """
        tokens = []
        current_type = "general"
        
        for line in content.split("\n"):
            # Check for section headers (e.g., "## Color", "### Primary")
            header_match = re.match(r"^#+\s+(\w+)", line)
            if header_match:
                current_type = header_match.group(1).lower()
                continue
            
            # Parse table rows
            row_match = re.match(r"\|\s*`?([^`|\n]+)`?\s*\|\s*([^|]*)\|\s*([^|]*)\|", line)
            if row_match:
                name = row_match.group(1).strip()
                value = row_match.group(2).strip()
                description = row_match.group(3).strip()
                
                # Skip header rows
                if name == "Token" or name.startswith("-"):
                    continue
                
                # Skip TBD values
                if value.upper() == "TBD":
                    value = None
                
                token = DesignToken(
                    name=name,
                    token_type=current_type,
                    value=value,
                    description=description if description else None,
                )
                tokens.append(token)
        
        return tokens
    
    def get_design_tokens(self, token_type: Optional[str] = None) -> list[DesignToken]:
        """Get design tokens, optionally filtered by type.
        
        Args:
            token_type: Optional token type filter (color, spacing, etc.)
            
        Returns:
            List of design tokens
        """
        if token_type:
            return self._tokens_by_type.get(token_type, [])
        return list(self._tokens.values())
    
    def get_token(self, name: str) -> Optional[DesignToken]:
        """Get a specific design token by name.
        
        Args:
            name: Token name
            
        Returns:
            DesignToken or None if not found
        """
        return self._tokens.get(name)
    
    def get_wcag_criterion(self, criterion: str) -> Optional[WCAGReference]:
        """Get a WCAG criterion by number.
        
        Args:
            criterion: Criterion number (e.g., "1.4.3")
            
        Returns:
            WCAGReference or None if not found
        """
        return self._wcag.get(criterion)
    
    def get_all_wcag_criteria(self) -> list[WCAGReference]:
        """Get all WCAG criteria.
        
        Returns:
            List of all WCAG references
        """
        return list(self._wcag.values())
    
    def link_finding_to_standard(
        self,
        token_name: Optional[str] = None,
        wcag_criterion: Optional[str] = None,
        custom: Optional[str] = None,
    ) -> StandardsReference:
        """Link a finding to a design standard.
        
        Args:
            token_name: Optional design token name
            wcag_criterion: Optional WCAG criterion number
            custom: Optional custom standard reference
            
        Returns:
            StandardsReference with linked standards
        """
        design_token = None
        wcag = None
        
        if token_name:
            token = self.get_token(token_name)
            if token:
                design_token = DesignTokenReference(
                    token_name=token.name,
                    token_type=token.token_type,
                    expected_value=token.value,
                )
        
        if wcag_criterion:
            wcag = self.get_wcag_criterion(wcag_criterion)
        
        return StandardsReference(
            design_token=design_token,
            wcag=wcag,
            custom=custom,
        )
    
    def find_tokens_by_pattern(self, pattern: str) -> list[DesignToken]:
        """Find tokens matching a pattern.
        
        Args:
            pattern: Regex pattern to match token names
            
        Returns:
            List of matching tokens
        """
        try:
            regex = re.compile(pattern, re.IGNORECASE)
            return [
                token for token in self._tokens.values()
                if regex.search(token.name)
            ]
        except re.error:
            return []
    
    def register_token(self, token: DesignToken) -> None:
        """Register a new design token.
        
        Args:
            token: DesignToken to register
        """
        self._tokens[token.name] = token
        if token.token_type not in self._tokens_by_type:
            self._tokens_by_type[token.token_type] = []
        self._tokens_by_type[token.token_type].append(token)
    
    def register_wcag_criterion(self, reference: WCAGReference) -> None:
        """Register a custom WCAG criterion.
        
        Args:
            reference: WCAGReference to register
        """
        self._wcag[reference.criterion] = reference
    
    @property
    def token_count(self) -> int:
        """Return number of registered tokens."""
        return len(self._tokens)
    
    @property
    def wcag_count(self) -> int:
        """Return number of registered WCAG criteria."""
        return len(self._wcag)