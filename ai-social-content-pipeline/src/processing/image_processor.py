from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageOps

TARGET_WIDTH = 1080
TARGET_HEIGHT = 1350


def resize_to_instagram(input_path: str, output_path: str, width: int = TARGET_WIDTH, height: int = TARGET_HEIGHT) -> str:
    """Resize an image to Instagram 4:5 and save as JPEG in RGB mode."""
    source = Path(input_path)
    destination = Path(output_path)

    with Image.open(source) as image:
        rgb_image = image.convert("RGB")
        cropped = ImageOps.fit(rgb_image, (width, height), method=Image.Resampling.LANCZOS)
        destination.parent.mkdir(parents=True, exist_ok=True)
        cropped.save(destination, format="JPEG", quality=90, optimize=True)

    return str(destination)
