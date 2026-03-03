#!/usr/bin/env python3
"""
Generate synthetic UI screenshots with known component layouts for validation.

Creates minimal UI screenshots with programmatically-known components for
testing the persistence layer and detection accuracy validation.
"""

import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


# Output directory
OUTPUT_DIR = Path(__file__).parent

# Color palette (simple, high contrast)
COLORS = {
    "background": "#FFFFFF",
    "button": "#3B82F6",
    "button_text": "#FFFFFF",
    "input_bg": "#F3F4F6",
    "input_border": "#D1D5DB",
    "text": "#1F2937",
    "header": "#111827",
    "card_bg": "#F9FAFB",
    "card_border": "#E5E7EB",
}


def create_button(draw, x, y, width, height, label):
    """Draw a button with known bounding box."""
    draw.rectangle([x, y, x + width, y + height], fill=COLORS["button"])
    # Center text (simplified)
    text_y = y + (height - 12) // 2
    draw.text((x + 10, text_y), label, fill=COLORS["button_text"])
    return {
        "type": "button",
        "label": label,
        "bbox": {"x": x, "y": y, "width": width, "height": height},
    }


def create_input(draw, x, y, width, height, placeholder=""):
    """Draw an input field with known bounding box."""
    draw.rectangle([x, y, x + width, y + height], fill=COLORS["input_bg"], outline=COLORS["input_border"], width=1)
    if placeholder:
        draw.text((x + 8, y + 8), placeholder, fill="#9CA3AF")
    return {
        "type": "input",
        "label": placeholder,
        "bbox": {"x": x, "y": y, "width": width, "height": height},
    }


def create_text(draw, x, y, text, font_size=14, bold=False):
    """Draw text with known bounding box."""
    color = COLORS["header"] if bold else COLORS["text"]
    draw.text((x, y), text, fill=color)
    # Approximate text width
    text_width = len(text) * 7
    text_height = font_size + 4
    return {
        "type": "text",
        "label": text,
        "bbox": {"x": x, "y": y, "width": text_width, "height": text_height},
    }


def create_header(draw, x, y, text, width):
    """Draw a header with known bounding box."""
    draw.text((x, y), text, fill=COLORS["header"])
    text_width = len(text) * 10
    text_height = 28
    return {
        "type": "header",
        "label": text,
        "bbox": {"x": x, "y": y, "width": text_width, "height": text_height},
    }


def create_card(draw, x, y, width, height):
    """Draw a card container with known bounding box."""
    draw.rectangle([x, y, x + width, y + height], fill=COLORS["card_bg"], outline=COLORS["card_border"], width=1)
    return {
        "type": "card",
        "label": None,
        "bbox": {"x": x, "y": y, "width": width, "height": height},
    }


def create_image_placeholder(draw, x, y, width, height, label="image"):
    """Draw an image placeholder with known bounding box."""
    draw.rectangle([x, y, x + width, y + height], fill="#E5E7EB", outline="#D1D5DB", width=1)
    draw.text((x + width // 2 - 20, y + height // 2 - 6), label, fill="#6B7280")
    return {
        "type": "image",
        "label": label,
        "bbox": {"x": x, "y": y, "width": width, "height": height},
    }


def normalize_bbox(bbox, img_width, img_height):
    """Convert pixel bbox to normalized coordinates (0.0-1.0)."""
    return {
        "x": round(bbox["x"] / img_width, 4),
        "y": round(bbox["y"] / img_height, 4),
        "width": round(bbox["width"] / img_width, 4),
        "height": round(bbox["height"] / img_height, 4),
    }


def generate_screenshot_001():
    """Generate login form screenshot."""
    width, height = 400, 600
    img = Image.new("RGB", (width, height), COLORS["background"])
    draw = ImageDraw.Draw(img)
    
    components = []
    
    # Header
    comp = create_header(draw, 40, 40, "Sign In", width - 80)
    components.append(comp)
    
    # Email input
    comp = create_input(draw, 40, 100, 320, 40, "Email address")
    components.append(comp)
    
    # Password input
    comp = create_input(draw, 40, 160, 320, 40, "Password")
    components.append(comp)
    
    # Sign in button
    comp = create_button(draw, 40, 220, 320, 44, "Sign In")
    components.append(comp)
    
    # Forgot password link
    comp = create_text(draw, 40, 280, "Forgot password?")
    components.append(comp)
    
    # Divider text
    comp = create_text(draw, 160, 320, "or continue with")
    components.append(comp)
    
    # Google button
    comp = create_button(draw, 40, 360, 320, 44, "Continue with Google")
    components.append(comp)
    
    # Sign up text
    comp = create_text(draw, 40, 420, "Don't have an account? Sign up")
    components.append(comp)
    
    # Normalize bboxes
    for comp in components:
        comp["bbox_normalized"] = normalize_bbox(comp["bbox"], width, height)
    
    return img, components, {"width": width, "height": height}


def generate_screenshot_002():
    """Generate dashboard with cards screenshot."""
    width, height = 800, 600
    img = Image.new("RGB", (width, height), COLORS["background"])
    draw = ImageDraw.Draw(img)
    
    components = []
    
    # Header
    comp = create_header(draw, 40, 20, "Dashboard", width - 80)
    components.append(comp)
    
    # Stats cards row
    card_width = 170
    card_spacing = 20
    
    for i, label in enumerate(["Total Users", "Revenue", "Orders", "Conversion"]):
        x = 40 + i * (card_width + card_spacing)
        comp = create_card(draw, x, 80, card_width, 100)
        components.append(comp)
        
        # Card title
        comp2 = create_text(draw, x + 16, 96, label)
        components.append(comp2)
        
        # Card value
        comp3 = create_text(draw, x + 16, 130, "1,234", font_size=14, bold=True)
        components.append(comp3)
    
    # Main content card
    comp = create_card(draw, 40, 200, 720, 360)
    components.append(comp)
    
    # Card header
    comp = create_text(draw, 56, 216, "Recent Activity", font_size=14, bold=True)
    components.append(comp)
    
    # Activity items
    for i in range(5):
        y = 260 + i * 60
        comp = create_text(draw, 56, y, f"User action {i + 1}")
        components.append(comp)
    
    return img, components, {"width": width, "height": height}


def generate_screenshot_003():
    """Generate e-commerce product card screenshot."""
    width, height = 400, 500
    img = Image.new("RGB", (width, height), COLORS["background"])
    draw = ImageDraw.Draw(img)
    
    components = []
    
    # Product card
    comp = create_card(draw, 20, 20, 360, 460)
    components.append(comp)
    
    # Product image
    comp = create_image_placeholder(draw, 40, 40, 320, 200, "product")
    components.append(comp)
    
    # Product title
    comp = create_text(draw, 40, 260, "Premium Widget Pro", font_size=14, bold=True)
    components.append(comp)
    
    # Price
    comp = create_text(draw, 40, 290, "$99.99")
    components.append(comp)
    
    # Description
    comp = create_text(draw, 40, 320, "High-quality widget for professionals")
    components.append(comp)
    
    # Add to cart button
    comp = create_button(draw, 40, 380, 320, 44, "Add to Cart")
    components.append(comp)
    
    # Buy now button
    comp = create_button(draw, 40, 436, 320, 44, "Buy Now")
    components.append(comp)
    
    return img, components, {"width": width, "height": height}


def generate_screenshot_004():
    """Generate settings form screenshot."""
    width, height = 600, 500
    img = Image.new("RGB", (width, height), COLORS["background"])
    draw = ImageDraw.Draw(img)
    
    components = []
    
    # Header
    comp = create_header(draw, 40, 20, "Settings", width - 80)
    components.append(comp)
    
    # Section: Profile
    comp = create_text(draw, 40, 70, "Profile Settings", font_size=14, bold=True)
    components.append(comp)
    
    # Name input
    comp = create_input(draw, 40, 100, 520, 36, "Full name")
    components.append(comp)
    
    # Email input
    comp = create_input(draw, 40, 150, 520, 36, "Email")
    components.append(comp)
    
    # Section: Notifications
    comp = create_text(draw, 40, 210, "Notifications", font_size=14, bold=True)
    components.append(comp)
    
    # Checkbox placeholders (as text for simplicity)
    comp = create_text(draw, 40, 240, "☐ Email notifications")
    components.append(comp)
    
    comp = create_text(draw, 40, 270, "☐ Push notifications")
    components.append(comp)
    
    comp = create_text(draw, 40, 300, "☑ Marketing emails")
    components.append(comp)
    
    # Section: Theme
    comp = create_text(draw, 40, 340, "Theme", font_size=14, bold=True)
    components.append(comp)
    
    # Theme buttons
    comp = create_button(draw, 40, 370, 160, 36, "Light")
    components.append(comp)
    
    comp = create_button(draw, 220, 370, 160, 36, "Dark")
    components.append(comp)
    
    comp = create_button(draw, 400, 370, 160, 36, "System")
    components.append(comp)
    
    # Save button
    comp = create_button(draw, 40, 440, 520, 44, "Save Changes")
    components.append(comp)
    
    return img, components, {"width": width, "height": height}


def generate_screenshot_005():
    """Generate navigation sidebar screenshot."""
    width, height = 800, 600
    img = Image.new("RGB", (width, height), COLORS["background"])
    draw = ImageDraw.Draw(img)
    
    components = []
    
    # Sidebar
    draw.rectangle([0, 0, 200, height], fill="#1F2937")
    
    # Sidebar header
    comp = create_text(draw, 20, 20, "MyApp")
    comp["type"] = "text"
    components.append(comp)
    
    # Nav items
    nav_items = ["Dashboard", "Projects", "Team", "Settings", "Help"]
    for i, item in enumerate(nav_items):
        y = 70 + i * 44
        comp = create_text(draw, 20, y, item)
        comp["type"] = "navigation"
        components.append(comp)
    
    # Main content area
    comp = create_header(draw, 240, 20, "Dashboard", width - 260)
    components.append(comp)
    
    # Content cards
    comp = create_card(draw, 240, 70, 520, 200)
    components.append(comp)
    
    comp = create_card(draw, 240, 290, 250, 200)
    components.append(comp)
    
    comp = create_card(draw, 510, 290, 250, 200)
    components.append(comp)
    
    return img, components, {"width": width, "height": height}


def main():
    """Generate all validation screenshots."""
    generators = [
        ("screenshot_001", generate_screenshot_001, "Login form with inputs and buttons"),
        ("screenshot_002", generate_screenshot_002, "Dashboard with stats cards"),
        ("screenshot_003", generate_screenshot_003, "E-commerce product card"),
        ("screenshot_004", generate_screenshot_004, "Settings form with inputs"),
        ("screenshot_005", generate_screenshot_005, "Navigation sidebar layout"),
    ]
    
    manifest = {
        "description": "Minimal validation dataset for M3-1 persistence testing",
        "created": "2026-03-02",
        "screenshots": [],
    }
    
    for name, generator, description in generators:
        img, components, dimensions = generator()
        
        # Save image
        img_path = OUTPUT_DIR / f"{name}.png"
        img.save(img_path, "PNG")
        print(f"Created {img_path}")
        
        # Save metadata JSON
        metadata = {
            "name": name,
            "description": description,
            "dimensions": dimensions,
            "components": components,
            "component_count": len(components),
            "component_types": list(set(c["type"] for c in components)),
        }
        
        json_path = OUTPUT_DIR / f"{name}.json"
        with open(json_path, "w") as f:
            json.dump(metadata, f, indent=2)
        print(f"Created {json_path}")
        
        manifest["screenshots"].append({
            "name": name,
            "description": description,
            "image": f"{name}.png",
            "metadata": f"{name}.json",
            "component_count": len(components),
        })
    
    # Save manifest
    manifest_path = OUTPUT_DIR / "manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"Created {manifest_path}")
    
    print(f"\nGenerated {len(generators)} validation screenshots")
    total_components = sum(s["component_count"] for s in manifest["screenshots"])
    print(f"Total components across all screenshots: {total_components}")


if __name__ == "__main__":
    main()
+++++++ REPLACE