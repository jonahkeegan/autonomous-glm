"""
Prompt templates for GPT-4 Vision component detection.

Provides system prompts and user prompt templates for UI component detection.
"""

from typing import Optional


# System prompt for UI component detection
SYSTEM_PROMPT = """You are an expert UI/UX analyzer specialized in detecting and classifying UI components in screenshots.

Your task is to identify ALL UI components in the given screenshot and return them as a structured JSON array.

## Component Types

Classify each component as one of these types:
- **button**: Clickable buttons, CTAs, action triggers
- **input**: Text inputs, search boxes, text areas
- **modal**: Overlay dialogs, popups, modals
- **label**: Text labels, form labels, captions
- **icon**: Icons, symbols, small graphics
- **image**: Photos, illustrations, graphics (non-icon)
- **text**: Body text, headings, paragraphs (not labels)
- **container**: Generic containers, divs, sections
- **card**: Card components, list items with content
- **navigation**: Nav bars, breadcrumbs, menus
- **checkbox**: Checkbox inputs
- **radio**: Radio button inputs
- **select**: Dropdown selects, combo boxes
- **slider**: Range sliders, progress bars
- **switch**: Toggle switches
- **tab**: Tab items, tab headers
- **table**: Data tables, grids
- **header**: Page headers, titles areas
- **footer**: Page footers
- **sidebar**: Sidebar panels
- **unknown**: Unclassifiable components

## Bounding Box Format

Return bounding boxes as NORMALIZED coordinates (0.0 to 1.0):
- **x**: Left edge position (0.0 = left, 1.0 = right)
- **y**: Top edge position (0.0 = top, 1.0 = bottom)
- **width**: Component width (0.0 to 1.0)
- **height**: Component height (0.0 to 1.0)

## Response Format

Return a JSON object with this exact structure:
```json
{
  "components": [
    {
      "type": "button",
      "label": "Submit",
      "confidence": 0.95,
      "bbox_x": 0.4,
      "bbox_y": 0.8,
      "bbox_width": 0.2,
      "bbox_height": 0.05,
      "properties": {
        "variant": "primary",
        "state": "default"
      }
    }
  ]
}
```

## Guidelines

1. Detect ALL visible components, including nested ones
2. Be precise with bounding boxes - they should tightly fit the component
3. Confidence should reflect how certain you are (0.0-1.0)
4. Include visible text as the "label" field
5. For properties, include relevant attributes like:
   - variant (primary, secondary, outline, etc.)
   - state (default, hover, disabled, etc.)
   - style (rounded, flat, elevated, etc.)
6. If uncertain about type, use "unknown"
7. Return ONLY valid JSON - no markdown, no explanation"""

USER_PROMPT_TEMPLATE = """Analyze this UI screenshot and detect all components.

Return the results as JSON with the structure specified in the system prompt.

Image: {image_path}

Focus on accuracy and completeness. Detect all visible UI elements."""


def build_detection_prompt(image_path: str, additional_context: Optional[str] = None) -> str:
    """Build the user prompt for component detection.
    
    Args:
        image_path: Path to the image being analyzed
        additional_context: Optional additional context about the image
        
    Returns:
        Formatted user prompt string
    """
    prompt = USER_PROMPT_TEMPLATE.format(image_path=image_path)
    
    if additional_context:
        prompt += f"\n\nAdditional context: {additional_context}"
    
    return prompt


def get_component_type_descriptions() -> dict[str, str]:
    """Return descriptions for each component type.
    
    Useful for documentation and validation.
    """
    return {
        "button": "Clickable buttons, CTAs, action triggers",
        "input": "Text inputs, search boxes, text areas",
        "modal": "Overlay dialogs, popups, modals",
        "label": "Text labels, form labels, captions",
        "icon": "Icons, symbols, small graphics",
        "image": "Photos, illustrations, graphics (non-icon)",
        "text": "Body text, headings, paragraphs (not labels)",
        "container": "Generic containers, divs, sections",
        "card": "Card components, list items with content",
        "navigation": "Nav bars, breadcrumbs, menus",
        "checkbox": "Checkbox inputs",
        "radio": "Radio button inputs",
        "select": "Dropdown selects, combo boxes",
        "slider": "Range sliders, progress bars",
        "switch": "Toggle switches",
        "tab": "Tab items, tab headers",
        "table": "Data tables, grids",
        "header": "Page headers, title areas",
        "footer": "Page footers",
        "sidebar": "Sidebar panels",
        "unknown": "Unclassifiable components",
    }