"""
Persistence bridge for M2 detection and token extraction results.

Provides high-level functions to persist vision detection results to the database,
handling the conversion between M2 models and database models.
"""

from pathlib import Path
from typing import Optional

from .crud import (
    batch_create_components,
    batch_create_tokens,
    batch_link_components_tokens,
    get_all_tokens,
    get_components_by_screen,
)
from .database import connection
from .models import Component, SystemToken


def persist_detection_result(
    screen_id: str,
    detection_result: "DetectionResult",
    db_path: Optional[Path] = None,
) -> list[Component]:
    """Persist components from a vision detection result.
    
    Args:
        screen_id: UUID of the parent screen
        detection_result: DetectionResult from VisionClient.detect_components()
        db_path: Optional database path
        
    Returns:
        List of persisted Component models
        
    Example:
        >>> from src.vision.client import VisionClient
        >>> from src.db.persistence import persist_detection_result
        >>> client = VisionClient()
        >>> result = client.detect_components("screenshot.png")
        >>> components = persist_detection_result(screen_id, result)
    """
    if not detection_result.components:
        return []
    
    return batch_create_components(
        screen_id=screen_id,
        components=detection_result.components,
        db_path=db_path,
    )


def persist_token_extraction(
    tokens: list["DesignToken"],
    db_path: Optional[Path] = None,
) -> list[SystemToken]:
    """Persist design tokens from token extraction.
    
    Args:
        tokens: List of DesignToken from token extraction
        db_path: Optional database path
        
    Returns:
        List of persisted SystemToken models (may include existing tokens)
        
    Example:
        >>> from src.vision.tokens import extract_tokens_from_image
        >>> from src.db.persistence import persist_token_extraction
        >>> tokens = extract_tokens_from_image("screenshot.png")
        >>> persisted = persist_token_extraction(tokens)
    """
    if not tokens:
        return []
    
    return batch_create_tokens(tokens=tokens, db_path=db_path)


def link_component_tokens_by_match(
    component_id: str,
    token_matches: list["TokenMatch"],
    db_path: Optional[Path] = None,
) -> int:
    """Link a component to tokens based on TokenMatch results.
    
    Args:
        component_id: UUID of the component
        token_matches: List of TokenMatch results from token matching
        db_path: Optional database path
        
    Returns:
        Number of links created
        
    Note:
        Only links tokens that were successfully matched (matched=True)
    """
    from .crud import get_all_tokens
    
    # Get all tokens to find IDs by name
    all_tokens = get_all_tokens(db_path)
    token_name_to_id = {t.name: t.id for t in all_tokens}
    
    links = []
    for match in token_matches:
        if match.matched and match.token_name:
            token_id = token_name_to_id.get(match.token_name)
            if token_id:
                links.append((component_id, token_id))
    
    if not links:
        return 0
    
    return batch_link_components_tokens(links=links, db_path=db_path)


def persist_full_analysis(
    screen_id: str,
    detection_result: "DetectionResult",
    design_tokens: Optional[list["DesignToken"]] = None,
    token_match_results: Optional[list["TokenMatchResult"]] = None,
    db_path: Optional[Path] = None,
) -> dict:
    """Persist complete analysis results for a screen.
    
    This is a convenience function that:
    1. Persists detected components
    2. Persists extracted design tokens
    3. Links components to matched tokens
    
    Args:
        screen_id: UUID of the parent screen
        detection_result: DetectionResult from vision detection
        design_tokens: Optional list of DesignToken from extraction
        token_match_results: Optional list of TokenMatchResult per component
        db_path: Optional database path
        
    Returns:
        Dict with 'components', 'tokens', and 'links_created' keys
        
    Example:
        >>> result = persist_full_analysis(
        ...     screen_id=screen.id,
        ...     detection_result=detection,
        ...     design_tokens=tokens,
        ...     token_match_results=matches,
        ... )
        >>> print(f"Created {len(result['components'])} components")
    """
    result = {
        "components": [],
        "tokens": [],
        "links_created": 0,
    }
    
    # 1. Persist components
    result["components"] = persist_detection_result(
        screen_id=screen_id,
        detection_result=detection_result,
        db_path=db_path,
    )
    
    # 2. Persist tokens if provided
    if design_tokens:
        result["tokens"] = persist_token_extraction(
            tokens=design_tokens,
            db_path=db_path,
        )
    
    # 3. Link components to tokens if match results provided
    if token_match_results and result["components"]:
        # Build a map of component index to match result
        # Assumes token_match_results aligns with components
        for i, component in enumerate(result["components"]):
            if i < len(token_match_results):
                match_result = token_match_results[i]
                
                # Collect all matches (color + spacing + typography)
                all_matches = list(match_result.color_matches)
                if match_result.spacing_match:
                    all_matches.append(match_result.spacing_match)
                if match_result.typography_match:
                    all_matches.append(match_result.typography_match)
                
                links = link_component_tokens_by_match(
                    component_id=component.id,
                    token_matches=all_matches,
                    db_path=db_path,
                )
                result["links_created"] += links
    
    return result


def get_screen_analysis(
    screen_id: str,
    db_path: Optional[Path] = None,
) -> dict:
    """Retrieve complete analysis for a screen.
    
    Args:
        screen_id: UUID of the screen
        db_path: Optional database path
        
    Returns:
        Dict with 'components' and 'tokens' keys
    """
    components = get_components_by_screen(screen_id=screen_id, db_path=db_path)
    tokens = get_all_tokens(db_path=db_path)
    
    return {
        "components": components,
        "tokens": tokens,
        "component_count": len(components),
        "token_count": len(tokens),
    }