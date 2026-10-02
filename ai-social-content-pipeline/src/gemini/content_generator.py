from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, List, Optional

from pydantic import BaseModel, Field

from src.config.settings import get_settings
from src.content.models import GeneratedPost, generate_content_id, validate_hashtags


class GeneratedContentPayload(BaseModel):
    """Structured Gemini output contract for one content concept."""

    topic: str = Field(..., min_length=10)
    hook: str = Field(..., min_length=10)
    image_prompt: str = Field(..., min_length=20)
    caption: str = Field(..., min_length=20)
    hashtags: List[str] = Field(..., min_length=10, max_length=15)
    alt_text: str = Field(..., min_length=10)


class GeminiContentGenerator:
    """Generate post concepts via the Gemini text API."""

    def __init__(self, client: Optional[Any] = None, model: Optional[str] = None) -> None:
        self.client = client
        self.model = model or get_settings().gemini_text_model

    def generate_for_brand(self, brand: str, *, dry_run: bool = False) -> List[GeneratedPost]:
        """Generate 3 content items for a single brand."""
        if dry_run:
            return self._dry_run_posts(brand)

        if self.client is None:
            raise ValueError("A Gemini client is required for live generation.")

        results: List[GeneratedPost] = []
        for index in range(1, 4):
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
        return results

    def _dry_run_posts(self, brand: str) -> List[GeneratedPost]:
        generated: List[GeneratedPost] = []
        for index in range(1, 4):
            text_suffix = f"{brand} concept {index}"
            created_at = datetime.now(timezone.utc).isoformat()
            generated.append(
                GeneratedPost(
                    content_id=generate_content_id(brand),
                    brand=brand,
                    topic=f"{brand.replace('_', ' ').title()} idea {index}",
                    hook=f"Small touches that make a big difference in {text_suffix}.",
                    image_prompt=f"A polished, premium, photorealistic {brand.replace('_', ' ')} scene with soft natural light, tasteful styling, modern composition, 4:5 portrait, no text, no watermark.",
                    caption=f"Curated inspiration for {brand.replace('_', ' ')} lovers. Thoughtful details, elevated styling, and a refreshed mood for everyday living.",
                    hashtags=[
                        "#home",
                        "#decor",
                        "#interior",
                        "#design",
                        "#styling",
                        "#inspiration",
                        "#minimalism",
                        "#modernhome",
                        "#roomideas",
                        "#detailsmatter",
                    ],
                    alt_text=f"Editorial styled {brand.replace('_', ' ')} scene with natural light and clean design.",
                    created_at=created_at,
                    status="dry_run",
                )
            )
        return generated

    def _request_content_payload(self, brand: str, index: int) -> GeneratedContentPayload:
        prompt = self._build_prompt(brand, index)
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

    @staticmethod
    def _build_prompt(brand: str, index: int) -> str:
        return (
            f"Create a concise JSON object for Instagram content for the brand '{brand}'. "
            f"Generate exactly one unique post concept for index {index}. "
            "Required fields: topic, hook, image_prompt, caption, hashtags, alt_text. "
            "Make the output valid JSON only, no markdown fences. "
            "The topic should be specific and relevant to the brand niche. "
            "The hook should be short and compelling. "
            "The image_prompt should contain detailed visual direction for a photorealistic Instagram 4:5 portrait render. "
            "The caption should sound authentic and not claim fake discounts or partnerships. "
            "The hashtags list should include 10 to 15 relevant hashtags only. "
            "The alt_text should describe the visual clearly."
        )
