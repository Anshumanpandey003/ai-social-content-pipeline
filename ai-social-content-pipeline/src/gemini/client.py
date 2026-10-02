from __future__ import annotations

import os
from typing import Any, Optional

from google import genai


class GeminiClient:
    """Thin wrapper around the official Google GenAI SDK."""

    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is required to use Gemini clients.")
        self._client = genai.Client(api_key=self.api_key)

    @property
    def client(self) -> Any:
        return self._client


def get_client(api_key: Optional[str] = None) -> GeminiClient:
    """Create a configured Gemini client."""
    return GeminiClient(api_key=api_key)
