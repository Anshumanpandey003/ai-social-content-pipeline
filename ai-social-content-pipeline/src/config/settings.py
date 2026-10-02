from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional, Union

from dotenv import load_dotenv
from pydantic import BaseModel, Field

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BRAND_CONFIG_PATH = PROJECT_ROOT / "config" / "brands.json"

load_dotenv(dotenv_path=PROJECT_ROOT / ".env")


class Settings(BaseModel):
    """Environment-driven settings for the pipeline."""

    gemini_api_key: Optional[str] = Field(default_factory=lambda: os.getenv("GEMINI_API_KEY"))
    gemini_text_model: str = Field(default_factory=lambda: os.getenv("GEMINI_TEXT_MODEL", "gemini-2.5-flash"))
    gemini_image_model: str = Field(default_factory=lambda: os.getenv("GEMINI_IMAGE_MODEL", "gemini-3.1-flash-image"))
    output_dir: str = Field(default_factory=lambda: os.getenv("OUTPUT_DIR", "output"))
    request_delay_seconds: float = Field(default_factory=lambda: float(os.getenv("REQUEST_DELAY_SECONDS", "1.0")))

    @property
    def has_api_key(self) -> bool:
        return bool(self.gemini_api_key)


def get_settings() -> Settings:
    """Load settings from environment variables."""
    return Settings()


def load_brand_config(config_path: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
    """Load brand metadata from JSON."""
    target_path = Path(config_path) if config_path else DEFAULT_BRAND_CONFIG_PATH
    with target_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)
