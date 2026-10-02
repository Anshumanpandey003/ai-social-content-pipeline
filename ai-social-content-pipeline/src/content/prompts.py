from __future__ import annotations

from src.config.settings import get_settings


def build_brand_prompt(brand: str, topic: str) -> str:
    """Build a brand-specific text-generation prompt for the content model."""
    settings = get_settings()
    return (
        f"You are generating Instagram-ready content for the brand '{brand}'. "
        f"Use the topic: '{topic}'. "
        "Return a concise JSON object with keys: topic, hook, image_prompt, caption, hashtags, alt_text. "
        "The hook should be compelling and short. "
        "The image_prompt should be detailed, brand-appropriate, and optimized for a 4:5 Instagram portrait. "
        "Do not claim fake partnerships, discounts, or guaranteed virality. "
        "The caption should feel natural and useful to an audience scrolling on Instagram. "
        "Use 10 to 15 relevant hashtags only. "
        f"The Gemini model using this request is '{settings.gemini_text_model}'."
    )
