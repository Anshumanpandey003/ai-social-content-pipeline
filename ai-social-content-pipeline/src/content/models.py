from __future__ import annotations

import re
import uuid
from typing import List, Literal, Optional, Set

from pydantic import BaseModel, Field, field_validator

BrandName = Literal["home_decor", "girls_apparel", "mens_style"]


class GeneratedPost(BaseModel):
    """Structured Instagram post metadata."""

    content_id: str = Field(..., description="Unique identifier for the generated post.")
    brand: BrandName
    topic: str
    hook: str
    image_prompt: str
    caption: str
    hashtags: List[str]
    alt_text: str
    created_at: str
    status: Literal["generated", "failed", "dry_run"] = "generated"
    error: Optional[str] = None

    @field_validator("content_id")
    @classmethod
    def validate_content_id(cls, value: str) -> str:
        if not re.fullmatch(r"[a-z0-9_-]+", value):
            raise ValueError("content_id must contain only lowercase letters, numbers, underscores, or hyphens.")
        return value

    @field_validator("hashtags")
    @classmethod
    def validate_hashtags(cls, value: List[str]) -> List[str]:
        normalized = []
        for tag in value:
            cleaned = str(tag).strip()
            if not cleaned:
                continue
            final_tag = cleaned if cleaned.startswith("#") else f"#{cleaned.lstrip('#')}"
            normalized.append(final_tag)

        unique = []
        seen: Set[str] = set()
        for tag in normalized:
            lower = tag.lower()
            if lower not in seen:
                seen.add(lower)
                unique.append(tag)

        if not 10 <= len(unique) <= 15:
            raise ValueError("hashtags must include between 10 and 15 unique entries.")
        return unique[:15]


def generate_content_id(brand: str) -> str:
    """Create a deterministic human-safe content ID."""
    return f"{brand}-{uuid.uuid4().hex[:10]}"


def validate_hashtags(hashtags: List[str]) -> List[str]:
    """Normalize and validate a hashtag list."""
    normalized = []
    for tag in hashtags:
        cleaned = str(tag).strip()
        if not cleaned:
            continue
        normalized.append(cleaned if cleaned.startswith("#") else f"#{cleaned.lstrip('#')}")

    unique = []
    seen: Set[str] = set()
    for tag in normalized:
        lowered = tag.lower()
        if lowered not in seen:
            seen.add(lowered)
            unique.append(tag)

    if not 10 <= len(unique) <= 15:
        raise ValueError("Hashtags must contain between 10 and 15 unique entries.")
    return unique[:15]
