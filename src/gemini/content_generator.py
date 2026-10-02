from __future__ import annotations

import json
import logging
import time
from datetime import datetime, timezone
from typing import Any, List, Optional

from pydantic import BaseModel, Field

from src.config.settings import get_settings
from src.content.models import GeneratedPost, generate_content_id, validate_hashtags

logger = logging.getLogger(__name__)


class GeneratedContentPayload(BaseModel):
    """Structured Gemini output contract for one content concept."""

    topic: str = Field(..., min_length=10)
    hook: str = Field(..., min_length=10)
    image_prompt: str = Field(..., min_length=20)
    caption: str = Field(..., min_length=20)
    hashtags: List[str] = Field(..., min_length=5, max_length=15)
    alt_text: str = Field(..., min_length=10)


class GeminiContentGenerator:
    """
    Generate post concepts via the Gemini text API with exponential backoff retries.
    
    Produces structured content metadata (topic, hook, caption, etc.) ready for
    image generation and publishing workflows.
    """

    def __init__(
        self,
        client: Optional[Any] = None,
        model: Optional[str] = None,
        max_retries: int = 3,
    ) -> None:
        """
        Initialize content generator.
        
        Args:
            client: Optional genai.Client instance. Required for live generation.
            model: Gemini text model name. Defaults to GEMINI_TEXT_MODEL env var.
            max_retries: Max retry attempts with exponential backoff.
        """
        self.client = client
        self.model = model or get_settings().gemini_text_model
        self.max_retries = max_retries

    def generate_for_brand(self, brand: str, *, dry_run: bool = False, posts_per_brand: int = 3) -> List[GeneratedPost]:
        """
        Generate content items for a single brand.
        
        Args:
            brand: Brand name (home_decor, girls_apparel, or mens_style).
            dry_run: If True, generate mock content without API calls.
            posts_per_brand: Number of posts to generate (default 3).
        
        Returns:
            List of GeneratedPost objects.
        
        Raises:
            ValueError: If live generation requested but client is None.
        """
        if dry_run:
            return self._dry_run_posts(brand, count=posts_per_brand)

        if self.client is None:
            raise ValueError("A Gemini client is required for live content generation.")

        results: List[GeneratedPost] = []
        for index in range(1, posts_per_brand + 1):
            try:
                payload = self._request_content_payload(brand, index)
                hashtags = validate_hashtags(payload.hashtags)
                created_at = datetime.now(timezone.utc).isoformat()
                post = GeneratedPost(
                    content_id=generate_content_id(brand),
                    brand=brand,
                    topic=payload.topic,
                    hook=payload.hook,
                    image_prompt=payload.image_prompt,
                    caption=payload.caption,
                    hashtags=hashtags,
                    alt_text=payload.alt_text,
                    created_at=created_at,
                    status="generated",
                )
                results.append(post)
                logger.info("Generated post %d/%d for %s", index, posts_per_brand, brand)
            except Exception as exc:
                logger.error("Failed to generate post %d/%d for %s: %s", index, posts_per_brand, brand, exc)
                # Continue with next post instead of failing entirely
                continue

        return results

    def _dry_run_posts(self, brand: str, count: int = 3) -> List[GeneratedPost]:
        """Generate mock posts for testing without API calls."""
        generated: List[GeneratedPost] = []
        for index in range(1, count + 1):
            text_suffix = f"{brand} concept {index}"
            created_at = datetime.now(timezone.utc).isoformat()
            generated.append(
                GeneratedPost(
                    content_id=generate_content_id(brand),
                    brand=brand,
                    topic=f"{brand.replace('_', ' ').title()} idea {index}",
                    hook="Inspiring you to transform your space with thoughtful details.",
                    image_prompt=(
                        f"A polished, premium, photorealistic {brand.replace('_', ' ')} scene "
                        "with soft natural light, tasteful styling, modern composition, 4:5 portrait, "
                        "no text, no watermarks, clean background, editorial quality."
                    ),
                    caption=(
                        f"Curated inspiration for {brand.replace('_', ' ')} lovers. "
                        "Thoughtful details, elevated styling, and a refreshed mood for everyday living. "
                        "Save this for your next project. What would you change first? 👇"
                    ),
                    hashtags=[
                        "home",
                        "decor",
                        "interior",
                        "design",
                        "styling",
                        "inspiration",
                        "minimalism",
                        "modernhome",
                    ],
                    alt_text=f"Editorial styled {brand.replace('_', ' ')} scene with natural light and clean design.",
                    created_at=created_at,
                    status="dry_run",
                )
            )
        return generated

    def _request_content_payload(self, brand: str, index: int) -> GeneratedContentPayload:
        """
        Request structured content from Gemini with exponential backoff retries.
        
        Args:
            brand: Brand name.
            index: Post index (1-based).
        
        Returns:
            GeneratedContentPayload with validated schema.
        
        Raises:
            RuntimeError: After max retries exhausted.
        """
        prompt = self._build_prompt(brand, index)
        last_error: Optional[Exception] = None

        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                    config={
                        "response_mime_type": "application/json",
                        "response_schema": GeneratedContentPayload,
                    },
                )
                data = json.loads(response.text)
                return GeneratedContentPayload.model_validate(data)
            except Exception as exc:
                last_error = exc
                if attempt < self.max_retries:
                    wait_time = 2**attempt
                    logger.warning(
                        "Content generation attempt %d/%d failed for %s. Retrying in %ds: %s",
                        attempt,
                        self.max_retries,
                        brand,
                        wait_time,
                        exc,
                    )
                    time.sleep(wait_time)
                    continue
                break

        raise RuntimeError(
            f"Content generation failed for {brand} post {index} after {self.max_retries} attempts: {last_error}"
        ) from last_error

    @staticmethod
    def _build_prompt(brand: str, index: int) -> str:
        """Build a detailed prompt for Gemini content generation."""
        return (
            f"Create a concise JSON object for Instagram content for the brand '{brand}'. "
            f"Generate exactly one unique post concept for index {index}. "
            "Required fields: topic, hook, image_prompt, caption, hashtags, alt_text. "
            "Make the output valid JSON only, no markdown fences. "
            "The topic should be specific and relevant to the brand niche. "
            "The hook should be short and compelling (scroll-stopping). "
            "The image_prompt should contain detailed visual direction for a photorealistic Instagram 4:5 portrait render. "
            "The caption should sound authentic and use a Hook+Value+CTA structure. "
            "Do not claim fake discounts, partnerships, or guaranteed virality. "
            "The hashtags list should include 5 to 15 relevant hashtags (without # prefix). "
            "The alt_text should describe the visual clearly for accessibility."
        )
