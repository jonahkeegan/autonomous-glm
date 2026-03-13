"""UI templates for synthetic screenshot generation.

Provides base template classes and concrete implementations for common UI patterns.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from PIL import Image, ImageDraw, ImageFont


class ComponentType(Enum):
    """Component types for synthetic UI elements."""
    BUTTON = "button"
    INPUT = "input"
    TEXT = "text"
    HEADER = "header"
    CARD = "card"
    IMAGE = "image"
    NAVIGATION = "navigation"
    CONTAINER = "container"
    LABEL = "label"
    ICON = "icon"


@dataclass
class Component:
    """Represents a UI component in the synthetic screenshot."""
    type: ComponentType
    bbox: tuple[int, int, int, int]  # (x, y, width, height)
    label: Optional[str] = None
    color: Optional[str] = None
    text_color: Optional[str] = None
    font_size: Optional[int] = None
    is_issue: bool = False
    issue_type: Optional[str] = None
    

@dataclass
class TemplateResult:
    """Result of template rendering."""
    image: Image.Image
    components: list[Component]
    width: int
    height: int


class UITemplate(ABC):
    """Abstract base class for UI templates."""
    
    # Default colors
    BACKGROUND_COLOR = "#FFFFFF"
    PRIMARY_COLOR = "#3B82F6"  # Blue
    SECONDARY_COLOR = "#6B7280"  # Gray
    TEXT_COLOR = "#1F2937"  # Dark gray
    BORDER_COLOR = "#E5E7EB"  # Light gray
    ERROR_COLOR = "#EF4444"  # Red
    SUCCESS_COLOR = "#10B981"  # Green
    
    # Default dimensions
    DEFAULT_WIDTH = 400
    DEFAULT_HEIGHT = 600
    
    def __init__(
        self,
        width: int = DEFAULT_WIDTH,
        height: int = DEFAULT_HEIGHT,
        background_color: str = BACKGROUND_COLOR,
    ):
        self.width = width
        self.height = height
        self.background_color = background_color
        self.components: list[Component] = []
        
    @abstractmethod
    def render(self) -> TemplateResult:
        """Render the template and return image with components."""
        pass
    
    def create_image(self) -> Image.Image:
        """Create a new image with background color."""
        return Image.new("RGB", (self.width, self.height), self.background_color)
    
    def get_font(self, size: int = 14) -> ImageFont.FreeTypeFont:
        """Get a font for text rendering. Falls back to default if no font available."""
        try:
            # Try to use a system font
            return ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", size)
        except (OSError, IOError):
            try:
                return ImageFont.truetype("Arial", size)
            except (OSError, IOError):
                return ImageFont.load_default()
    
    def draw_rounded_rect(
        self,
        draw: ImageDraw.ImageDraw,
        bbox: tuple[int, int, int, int],
        fill: str,
        radius: int = 8,
        outline: Optional[str] = None,
        width: int = 1,
    ):
        """Draw a rounded rectangle."""
        x, y, w, h = bbox
        # Draw rectangle with rounded corners using circles
        draw.rounded_rectangle(
            [x, y, x + w, y + h],
            radius=radius,
            fill=fill,
            outline=outline,
            width=width,
        )
    
    def draw_button(
        self,
        draw: ImageDraw.ImageDraw,
        x: int,
        y: int,
        width: int,
        height: int,
        label: str,
        color: str = PRIMARY_COLOR,
        text_color: str = "#FFFFFF",
        is_issue: bool = False,
        issue_type: Optional[str] = None,
    ) -> Component:
        """Draw a button component."""
        self.draw_rounded_rect(draw, (x, y, width, height), fill=color, radius=8)
        
        # Center text
        font = self.get_font(14)
        bbox = draw.textbbox((0, 0), label, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        text_x = x + (width - text_width) // 2
        text_y = y + (height - text_height) // 2 - 2
        draw.text((text_x, text_y), label, fill=text_color, font=font)
        
        component = Component(
            type=ComponentType.BUTTON,
            bbox=(x, y, width, height),
            label=label,
            color=color,
            text_color=text_color,
            is_issue=is_issue,
            issue_type=issue_type,
        )
        self.components.append(component)
        return component
    
    def draw_input(
        self,
        draw: ImageDraw.ImageDraw,
        x: int,
        y: int,
        width: int,
        height: int,
        placeholder: str = "",
        value: str = "",
        is_issue: bool = False,
        issue_type: Optional[str] = None,
    ) -> Component:
        """Draw an input field component."""
        # Draw border
        self.draw_rounded_rect(
            draw, (x, y, width, height),
            fill="#FFFFFF",
            radius=6,
            outline=self.BORDER_COLOR,
            width=1,
        )
        
        # Draw placeholder or value text
        font = self.get_font(14)
        text = value if value else placeholder
        color = self.TEXT_COLOR if value else self.SECONDARY_COLOR
        draw.text((x + 12, y + (height - 16) // 2), text, fill=color, font=font)
        
        component = Component(
            type=ComponentType.INPUT,
            bbox=(x, y, width, height),
            label=placeholder or value,
            is_issue=is_issue,
            issue_type=issue_type,
        )
        self.components.append(component)
        return component
    
    def draw_text(
        self,
        draw: ImageDraw.ImageDraw,
        x: int,
        y: int,
        text: str,
        font_size: int = 14,
        color: str = TEXT_COLOR,
        is_issue: bool = False,
        issue_type: Optional[str] = None,
    ) -> Component:
        """Draw a text component and return its bounding box."""
        font = self.get_font(font_size)
        bbox = draw.textbbox((x, y), text, font=font)
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
        draw.text((x, y), text, fill=color, font=font)
        
        component = Component(
            type=ComponentType.TEXT,
            bbox=(x, y, width, height),
            label=text,
            text_color=color,
            font_size=font_size,
            is_issue=is_issue,
            issue_type=issue_type,
        )
        self.components.append(component)
        return component
    
    def draw_header(
        self,
        draw: ImageDraw.ImageDraw,
        x: int,
        y: int,
        width: int,
        height: int,
        title: str,
        is_issue: bool = False,
        issue_type: Optional[str] = None,
    ) -> Component:
        """Draw a header component."""
        # Draw header background
        draw.rectangle([x, y, x + width, y + height], fill=self.PRIMARY_COLOR)
        
        # Draw title
        font = self.get_font(18)
        draw.text((x + 16, y + (height - 20) // 2), title, fill="#FFFFFF", font=font)
        
        component = Component(
            type=ComponentType.HEADER,
            bbox=(x, y, width, height),
            label=title,
            color=self.PRIMARY_COLOR,
            is_issue=is_issue,
            issue_type=issue_type,
        )
        self.components.append(component)
        return component
    
    def draw_card(
        self,
        draw: ImageDraw.ImageDraw,
        x: int,
        y: int,
        width: int,
        height: int,
        is_issue: bool = False,
        issue_type: Optional[str] = None,
    ) -> Component:
        """Draw a card container component."""
        self.draw_rounded_rect(
            draw, (x, y, width, height),
            fill="#FFFFFF",
            radius=12,
            outline=self.BORDER_COLOR,
            width=1,
        )
        
        component = Component(
            type=ComponentType.CARD,
            bbox=(x, y, width, height),
            is_issue=is_issue,
            issue_type=issue_type,
        )
        self.components.append(component)
        return component


class LoginTemplate(UITemplate):
    """Login form template with inputs and buttons."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = "Sign In"
        
    def render(self) -> TemplateResult:
        """Render login form."""
        self.components = []
        image = self.create_image()
        draw = ImageDraw.Draw(image)
        
        # Header
        self.draw_header(draw, 0, 0, self.width, 60, self.title)
        
        # Welcome text
        self.draw_text(draw, 24, 80, "Welcome back!", font_size=24)
        self.draw_text(draw, 24, 115, "Please enter your credentials", font_size=14, color=self.SECONDARY_COLOR)
        
        # Email input
        self.draw_text(draw, 24, 160, "Email", font_size=12, color=self.SECONDARY_COLOR)
        self.draw_input(draw, 24, 180, self.width - 48, 44, placeholder="Enter your email")
        
        # Password input
        self.draw_text(draw, 24, 250, "Password", font_size=12, color=self.SECONDARY_COLOR)
        self.draw_input(draw, 24, 270, self.width - 48, 44, placeholder="Enter your password")
        
        # Sign in button
        self.draw_button(draw, 24, 340, self.width - 48, 48, "Sign In")
        
        # Forgot password link
        self.draw_text(
            draw, self.width // 2 - 50, 410,
            "Forgot password?",
            font_size=12,
            color=self.PRIMARY_COLOR,
        )
        
        # Sign up link
        self.draw_text(draw, 24, 460, "Don't have an account?", font_size=14, color=self.SECONDARY_COLOR)
        self.draw_text(draw, 200, 460, "Sign up", font_size=14, color=self.PRIMARY_COLOR)
        
        return TemplateResult(
            image=image,
            components=self.components,
            width=self.width,
            height=self.height,
        )


class DashboardTemplate(UITemplate):
    """Dashboard template with stats cards."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
    def render(self) -> TemplateResult:
        """Render dashboard with stats cards."""
        self.components = []
        image = self.create_image()
        draw = ImageDraw.Draw(image)
        
        # Header
        self.draw_header(draw, 0, 0, self.width, 60, "Dashboard")
        
        # Stats cards row 1
        card_width = (self.width - 48) // 2
        card_height = 80
        
        # Card 1
        self.draw_card(draw, 16, 80, card_width, card_height)
        self.draw_text(draw, 28, 92, "Total Users", font_size=12, color=self.SECONDARY_COLOR)
        self.draw_text(draw, 28, 115, "1,234", font_size=24)
        
        # Card 2
        self.draw_card(draw, 32 + card_width, 80, card_width, card_height)
        self.draw_text(draw, 44 + card_width, 92, "Revenue", font_size=12, color=self.SECONDARY_COLOR)
        self.draw_text(draw, 44 + card_width, 115, "$12.4K", font_size=24)
        
        # Stats cards row 2
        self.draw_card(draw, 16, 180, card_width, card_height)
        self.draw_text(draw, 28, 192, "Orders", font_size=12, color=self.SECONDARY_COLOR)
        self.draw_text(draw, 28, 215, "567", font_size=24)
        
        self.draw_card(draw, 32 + card_width, 180, card_width, card_height)
        self.draw_text(draw, 44 + card_width, 192, "Growth", font_size=12, color=self.SECONDARY_COLOR)
        self.draw_text(draw, 44 + card_width, 215, "+23%", font_size=24, color=self.SUCCESS_COLOR)
        
        # Recent activity section
        self.draw_text(draw, 16, 290, "Recent Activity", font_size=18)
        
        # Activity items
        activities = [
            ("John Doe", "Created new account", "2m ago"),
            ("Jane Smith", "Completed purchase", "5m ago"),
            ("Bob Wilson", "Updated profile", "10m ago"),
        ]
        
        y_offset = 320
        for name, action, time in activities:
            self.draw_card(draw, 16, y_offset, self.width - 32, 50)
            self.draw_text(draw, 28, y_offset + 8, name, font_size=14)
            self.draw_text(draw, 28, y_offset + 28, action, font_size=12, color=self.SECONDARY_COLOR)
            self.draw_text(draw, self.width - 60, y_offset + 16, time, font_size=12, color=self.SECONDARY_COLOR)
            y_offset += 60
        
        return TemplateResult(
            image=image,
            components=self.components,
            width=self.width,
            height=self.height,
        )


class FormTemplate(UITemplate):
    """Settings form template with multiple inputs."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
    def render(self) -> TemplateResult:
        """Render settings form."""
        self.components = []
        image = self.create_image()
        draw = ImageDraw.Draw(image)
        
        # Header
        self.draw_header(draw, 0, 0, self.width, 60, "Settings")
        
        # Profile section
        self.draw_text(draw, 16, 80, "Profile Settings", font_size=18)
        
        # Name input
        self.draw_text(draw, 16, 115, "Full Name", font_size=12, color=self.SECONDARY_COLOR)
        self.draw_input(draw, 16, 135, self.width - 32, 44, value="John Doe")
        
        # Email input
        self.draw_text(draw, 16, 195, "Email Address", font_size=12, color=self.SECONDARY_COLOR)
        self.draw_input(draw, 16, 215, self.width - 32, 44, value="john@example.com")
        
        # Phone input
        self.draw_text(draw, 16, 275, "Phone Number", font_size=12, color=self.SECONDARY_COLOR)
        self.draw_input(draw, 16, 295, self.width - 32, 44, placeholder="Enter phone number")
        
        # Preferences section
        self.draw_text(draw, 16, 365, "Preferences", font_size=18)
        
        # Notification toggle
        self.draw_card(draw, 16, 395, self.width - 32, 50)
        self.draw_text(draw, 28, 407, "Email Notifications", font_size=14)
        self.draw_text(draw, 28, 425, "Receive updates via email", font_size=12, color=self.SECONDARY_COLOR)
        
        # Save button
        self.draw_button(draw, 16, 470, self.width - 32, 48, "Save Changes")
        
        # Cancel button (secondary)
        self.draw_button(
            draw, 16, 530, self.width - 32, 48,
            "Cancel",
            color=self.BORDER_COLOR,
            text_color=self.TEXT_COLOR,
        )
        
        return TemplateResult(
            image=image,
            components=self.components,
            width=self.width,
            height=self.height,
        )


class ListTemplate(UITemplate):
    """List template with navigation sidebar."""
    
    def __init__(self, sidebar_width: int = 80, **kwargs):
        super().__init__(**kwargs)
        self.sidebar_width = sidebar_width
        
    def render(self) -> TemplateResult:
        """Render list with sidebar navigation."""
        self.components = []
        image = self.create_image()
        draw = ImageDraw.Draw(image)
        
        # Sidebar background
        draw.rectangle([0, 0, self.sidebar_width, self.height], fill="#1F2937")
        
        # Sidebar navigation items
        nav_items = ["Home", "Users", "Reports", "Settings"]
        y_offset = 20
        for item in nav_items:
            is_active = item == "Users"
            if is_active:
                draw.rectangle(
                    [0, y_offset - 5, self.sidebar_width, y_offset + 25],
                    fill=self.PRIMARY_COLOR,
                )
            self.draw_text(
                draw, 12, y_offset, item,
                font_size=12,
                color="#FFFFFF" if is_active else "#9CA3AF",
            )
            y_offset += 40
        
        # Main content area header
        self.draw_header(draw, self.sidebar_width, 0, self.width - self.sidebar_width, 60, "Users")
        
        # User list
        users = [
            ("John Doe", "john@example.com", "Admin"),
            ("Jane Smith", "jane@example.com", "User"),
            ("Bob Wilson", "bob@example.com", "User"),
            ("Alice Brown", "alice@example.com", "Editor"),
        ]
        
        content_x = self.sidebar_width + 16
        content_width = self.width - self.sidebar_width - 32
        
        y_offset = 80
        for name, email, role in users:
            self.draw_card(draw, content_x, y_offset, content_width, 60)
            
            # Avatar placeholder
            draw.ellipse(
                [content_x + 12, y_offset + 12, content_x + 48, y_offset + 48],
                fill=self.SECONDARY_COLOR,
            )
            
            # Name and email
            self.draw_text(draw, content_x + 60, y_offset + 12, name, font_size=14)
            self.draw_text(draw, content_x + 60, y_offset + 32, email, font_size=12, color=self.SECONDARY_COLOR)
            
            # Role badge
            badge_x = content_x + content_width - 60
            self.draw_rounded_rect(draw, (badge_x, y_offset + 18, 50, 24), fill=self.BORDER_COLOR, radius=12)
            font = self.get_font(10)
            draw.text((badge_x + 8, y_offset + 22), role, fill=self.TEXT_COLOR, font=font)
            
            y_offset += 72
        
        return TemplateResult(
            image=image,
            components=self.components,
            width=self.width,
            height=self.height,
        )