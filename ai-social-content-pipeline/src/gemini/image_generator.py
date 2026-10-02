from __future__ import annotations

import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Optional

from google.genai import types

from src.config.settings import get_settings


class ImageGenerator(ABC):
    """Abstract interface for image generation providers."""

    @abstractmethod
    def generate(self, prompt: str, output_path: str) -> str:
        """Generate an image for the prompt and persist it at output_path."""


class GeminiImageGenerator(ImageGenerator):
    """Gemini-backed image generation adapter with a provider abstraction."""

    def __init__(self, client: Optional[Any] = None, model: Optional[str] = None, *, max_retries: int = 3) -> None:
        self.client = client
        self.model = model or get_settings().gemini_image_model
        self.max_retries = max_retries

    def generate(self, prompt: str, output_path: str) -> str:
        """Generate and save a 4:5 portrait image from a Gemini image model if available."""
        if self.client is None:
            raise ValueError("A Gemini client is required for image generation.")

        last_error: Optional[Exception] = None
        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.client.models.generate_images(
                    model=self.model,
                    prompt=prompt,
                    config=types.GenerateImagesConfig(
                        number_of_images=1,
                        output_mime_type="image/jpeg",
                        include_rai_reason=True,
                    ),
                )
                if not response.generated_images:
                    raise RuntimeError("Gemini image API returned no images.")

                generated = response.generated_images[0]
                image_bytes = generated.image.image_bytes if hasattr(generated.image, "image_bytes") else None
                if image_bytes is None:
                    raise RuntimeError("Generated image payload is missing image bytes.")

                output = Path(output_path)
                output.parent.mkdir(parents=True, exist_ok=True)
                with output.open("wb") as handle:
                    handle.write(image_bytes)
                return str(output)
            except Exception as exc:  # pragma: no cover - runtime API path
                last_error = exc
                if attempt < self.max_retries:
                    time.sleep(2 ** attempt)
                    continue
                raise RuntimeError(f"Image generation failed after {self.max_retries} attempts: {exc}") from last_error

        if last_error is not None:
            raise RuntimeError(f"Image generation failed: {last_error}")
        raise RuntimeError("Image generation failed without an error.")
