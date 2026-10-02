from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from src.config.settings import get_settings, load_brand_config
from src.content.models import GeneratedPost
from src.gemini.client import get_client
from src.gemini.content_generator import GeminiContentGenerator
from src.gemini.image_generator import GeminiImageGenerator
from src.processing.image_processor import resize_to_instagram

logger = logging.getLogger(__name__)


class DailyPipeline:
    """Generate and persist a daily batch of 9 Instagram posts."""

    def __init__(self, base_output_dir: Optional[Union[str, Path]] = None) -> None:
        self.settings = get_settings()
        self.base_output_dir = Path(base_output_dir or self.settings.output_dir)
        self.brands = load_brand_config()

    def run(self, *, dry_run: bool = False, posts_per_brand: int = 3, brand: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Generate draft content and save it under an output date directory."""
        if brand is not None and brand not in self.brands:
            raise ValueError(f"Unsupported brand '{brand}'. Allowed: {sorted(self.brands)}")

        target_brands = [brand] if brand else list(self.brands.keys())
        date_key = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        output_dir = self.base_output_dir / date_key
        output_dir.mkdir(parents=True, exist_ok=True)

        logger.info("Starting daily pipeline")
        manifest_records: List[Dict[str, Any]] = []
        successful = 0
        failed = 0

        for brand_name in target_brands:
            logger.info("Generating %s posts", brand_name)
            posts = self._create_posts_for_brand(brand_name, dry_run=dry_run, posts_per_brand=posts_per_brand)
            brand_dir = output_dir / brand_name
            brand_dir.mkdir(parents=True, exist_ok=True)

            for index, post in enumerate(posts, start=1):
                logger.info("Generating %s post %s/%s", brand_name.title(), index, len(posts))
                post_path = brand_dir / f"post_{index:02d}.json"
                json.dumps(post.model_dump(), indent=2)
                post_path.write_text(json.dumps(post.model_dump(), indent=2), encoding="utf-8")

                if dry_run:
                    logger.info("Dry run: no image generated for %s", post.content_id)
                    successful += 1
                    manifest_records.append({"content_id": post.content_id, "brand": brand_name, "status": "dry_run"})
                    continue

                image_rel_path = brand_dir / f"post_{index:02d}.jpg"
                try:
                    if not self.settings.has_api_key:
                        raise ValueError("GEMINI_API_KEY is not set. Configure it before live image generation.")
                    client = get_client(self.settings.gemini_api_key)
                    generator = GeminiImageGenerator(client=client.client, model=self.settings.gemini_image_model)
                    generator.generate(post.image_prompt, str(image_rel_path))
                    resize_to_instagram(str(image_rel_path), str(image_rel_path))
                    post.status = "generated"
                    successful += 1
                    manifest_records.append({"content_id": post.content_id, "brand": brand_name, "status": "generated", "image": str(image_rel_path)})
                except Exception as exc:  # pragma: no cover - runtime path
                    post.status = "failed"
                    post.error = str(exc)
                    failed += 1
                    logger.exception("Image generation failed for %s", post.content_id)
                    manifest_records.append({"content_id": post.content_id, "brand": brand_name, "status": "failed", "error": str(exc)})

                updated_path = brand_dir / f"post_{index:02d}.json"
                updated_path.write_text(json.dumps(post.model_dump(), indent=2), encoding="utf-8")

        manifest = {
            "date": date_key,
            "total_posts": len(manifest_records),
            "successful": successful,
            "failed": failed,
            "posts": manifest_records,
        }
        (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        logger.info("Pipeline completed")
        logger.info("Successful: %s", successful)
        logger.info("Failed: %s", failed)
        return manifest

    def _create_posts_for_brand(self, brand: str, *, dry_run: bool, posts_per_brand: int) -> List[GeneratedPost]:
        """Create a brand's daily content placeholders."""
        generator = GeminiContentGenerator(client=None if dry_run else get_client(self.settings.gemini_api_key).client)
        if dry_run:
            return generator.generate_for_brand(brand, dry_run=True)[:posts_per_brand]

        if not self.settings.has_api_key:
            raise ValueError("GEMINI_API_KEY is required for live content generation.")
        return generator.generate_for_brand(brand, dry_run=False)[:posts_per_brand]


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(message)s")
    DailyPipeline().run()
