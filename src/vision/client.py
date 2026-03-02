"""
GPT-4 Vision API client for UI component detection.

Provides the VisionClient class for detecting UI components in screenshots.
"""

import asyncio
import base64
import json
import logging
import os
import time
from pathlib import Path
from typing import Optional

from PIL import Image

from .models import (
    ComponentType,
    DetectedComponent,
    DetectionResult,
    DetectionConfig,
)
from .prompts import SYSTEM_PROMPT, build_detection_prompt

logger = logging.getLogger(__name__)


class VisionClientError(Exception):
    """Base exception for VisionClient errors."""
    pass


class RateLimitError(VisionClientError):
    """Raised when rate limit is exceeded."""
    pass


class APIResponseError(VisionClientError):
    """Raised when API response is invalid."""
    pass


class VisionClient:
    """Client for detecting UI components using GPT-4 Vision API.
    
    Features:
    - Async API calls with retry logic
    - Rate limiting to prevent quota exhaustion
    - Exponential backoff on failures
    - Automatic image encoding
    
    Example:
        ```python
        client = VisionClient()
        result = await client.detect_components("screenshot.png")
        for component in result.components:
            print(f"{component.type}: {component.confidence:.2f}")
        ```
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        config: Optional[DetectionConfig] = None,
    ):
        """Initialize the VisionClient.
        
        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            config: Detection configuration (uses defaults if not provided)
        """
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OpenAI API key required. Set OPENAI_API_KEY environment variable "
                "or pass api_key parameter."
            )
        
        self.config = config or DetectionConfig()
        self._client = None
        self._last_request_time: float = 0.0
        self._request_count: int = 0
        
    def _get_client(self):
        """Lazy-load the OpenAI client."""
        if self._client is None:
            try:
                from openai import OpenAI
                self._client = OpenAI(api_key=self.api_key)
            except ImportError:
                raise ImportError(
                    "openai package required. Install with: pip install openai>=1.0.0"
                )
        return self._client
    
    def _encode_image(self, image_path: str) -> str:
        """Encode an image file to base64.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Base64-encoded image string
        """
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")
        
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    
    def _get_image_dimensions(self, image_path: str) -> tuple[int, int]:
        """Get image dimensions.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Tuple of (width, height)
        """
        with Image.open(image_path) as img:
            return img.size
    
    def _get_media_type(self, image_path: str) -> str:
        """Determine the media type from file extension.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Media type string (e.g., "image/png")
        """
        ext = Path(image_path).suffix.lower()
        media_types = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".webp": "image/webp",
        }
        return media_types.get(ext, "image/png")
    
    def _check_rate_limit(self) -> None:
        """Check and enforce rate limiting.
        
        Raises:
            RateLimitError: If rate limit would be exceeded
        """
        min_interval = 60.0 / self.config.rate_limit_per_minute
        elapsed = time.time() - self._last_request_time
        
        if elapsed < min_interval:
            wait_time = min_interval - elapsed
            logger.debug(f"Rate limit: waiting {wait_time:.2f}s")
            time.sleep(wait_time)
    
    def _parse_response(self, response_text: str) -> list[DetectedComponent]:
        """Parse the API response into DetectedComponent objects.
        
        Args:
            response_text: Raw text response from API
            
        Returns:
            List of DetectedComponent objects
        """
        try:
            # Clean up potential markdown code blocks
            text = response_text.strip()
            if text.startswith("```"):
                # Remove markdown code block markers
                lines = text.split("\n")
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                text = "\n".join(lines)
            
            data = json.loads(text)
            components = []
            
            for item in data.get("components", []):
                try:
                    # Map string type to enum
                    type_str = item.get("type", "unknown").lower()
                    try:
                        component_type = ComponentType(type_str)
                    except ValueError:
                        component_type = ComponentType.UNKNOWN
                    
                    component = DetectedComponent(
                        type=component_type,
                        label=item.get("label"),
                        confidence=float(item.get("confidence", 1.0)),
                        bbox_x=float(item.get("bbox_x", 0)),
                        bbox_y=float(item.get("bbox_y", 0)),
                        bbox_width=float(item.get("bbox_width", 0.1)),
                        bbox_height=float(item.get("bbox_height", 0.1)),
                        properties=item.get("properties"),
                    )
                    components.append(component)
                except (KeyError, ValueError, TypeError) as e:
                    logger.warning(f"Skipping invalid component: {e}")
                    continue
            
            return components
            
        except json.JSONDecodeError as e:
            raise APIResponseError(f"Failed to parse JSON response: {e}")
    
    def _retry_with_backoff(self, func, *args, **kwargs):
        """Execute a function with exponential backoff retry.
        
        Args:
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Function result
            
        Raises:
            VisionClientError: If all retries fail
        """
        last_error = None
        
        for attempt in range(self.config.retry_attempts + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_error = e
                
                if attempt < self.config.retry_attempts:
                    # Calculate backoff delay with exponential increase
                    delay = min(
                        self.config.retry_base_delay_ms * (2 ** attempt) / 1000,
                        self.config.retry_max_delay_ms / 1000,
                    )
                    logger.warning(
                        f"Attempt {attempt + 1} failed: {e}. "
                        f"Retrying in {delay:.2f}s"
                    )
                    time.sleep(delay)
                else:
                    logger.error(f"All {self.config.retry_attempts + 1} attempts failed")
        
        raise VisionClientError(f"Failed after {self.config.retry_attempts + 1} attempts: {last_error}")
    
    def detect_components(
        self,
        image_path: str,
        additional_context: Optional[str] = None,
    ) -> DetectionResult:
        """Detect UI components in an image.
        
        Args:
            image_path: Path to the screenshot/image file
            additional_context: Optional context about the image
            
        Returns:
            DetectionResult with detected components
            
        Raises:
            VisionClientError: If detection fails
            FileNotFoundError: If image file doesn't exist
        """
        start_time = time.time()
        
        # Validate image exists
        path = Path(image_path)
        if not path.exists():
            return DetectionResult(
                image_id=None,
                error=f"Image not found: {image_path}",
            )
        
        # Get image dimensions
        try:
            width, height = self._get_image_dimensions(image_path)
        except Exception as e:
            return DetectionResult(
                image_id=None,
                error=f"Failed to read image dimensions: {e}",
            )
        
        def _call_api():
            return self._call_api_internal(image_path, additional_context)
        
        try:
            # Check rate limit
            self._check_rate_limit()
            
            # Call API with retry
            response_text = self._retry_with_backoff(_call_api)
            
            # Parse response
            components = self._parse_response(response_text)
            
            # Filter by confidence threshold
            filtered_components = [
                c for c in components
                if c.confidence >= self.config.confidence_threshold
            ]
            
            # Update rate limit tracking
            self._last_request_time = time.time()
            self._request_count += 1
            
            processing_time = (time.time() - start_time) * 1000
            
            return DetectionResult(
                components=filtered_components,
                image_id=path.stem,
                image_width=width,
                image_height=height,
                processing_time_ms=processing_time,
                model_version=self.config.model,
            )
            
        except VisionClientError as e:
            return DetectionResult(
                image_id=path.stem,
                image_width=width if 'width' in dir() else None,
                image_height=height if 'height' in dir() else None,
                error=str(e),
            )
        except Exception as e:
            logger.exception(f"Unexpected error during detection: {e}")
            return DetectionResult(
                image_id=path.stem,
                error=f"Unexpected error: {e}",
            )
    
    def _call_api_internal(
        self,
        image_path: str,
        additional_context: Optional[str] = None,
    ) -> str:
        """Internal method to call the OpenAI API.
        
        Args:
            image_path: Path to the image file
            additional_context: Optional context about the image
            
        Returns:
            Raw text response from API
        """
        client = self._get_client()
        
        # Encode image
        base64_image = self._encode_image(image_path)
        media_type = self._get_media_type(image_path)
        
        # Build prompt
        user_prompt = build_detection_prompt(image_path, additional_context)
        
        # Call API
        response = client.chat.completions.create(
            model=self.config.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{media_type};base64,{base64_image}",
                                "detail": "high",
                            },
                        },
                    ],
                },
            ],
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
        )
        
        return response.choices[0].message.content
    
    async def detect_components_async(
        self,
        image_path: str,
        additional_context: Optional[str] = None,
    ) -> DetectionResult:
        """Async version of detect_components.
        
        Args:
            image_path: Path to the screenshot/image file
            additional_context: Optional context about the image
            
        Returns:
            DetectionResult with detected components
        """
        # Run sync version in thread pool for now
        # A fully async implementation would use httpx directly
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.detect_components(image_path, additional_context),
        )
    
    @property
    def request_count(self) -> int:
        """Return the number of API requests made by this client."""
        return self._request_count