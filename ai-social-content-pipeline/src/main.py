from __future__ import annotations

import argparse
import logging
from pathlib import Path

from src.pipeline.daily_pipeline import DailyPipeline

logger = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    """Define the command-line interface for content generation."""
    parser = argparse.ArgumentParser(description="Generate AI Instagram content drafts for daily posting.")
    parser.add_argument("--brand", choices=["home_decor", "girls_apparel", "mens_style"], help="Generate content for one specific brand only.")
    parser.add_argument("--posts", type=int, default=3, help="Number of posts to generate per brand for testing; default is 3.")
    parser.add_argument("--dry-run", action="store_true", help="Generate metadata only without calling Gemini image generation.")
    return parser


def main() -> None:
    """Entry point for the CLI."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    parser = build_parser()
    args = parser.parse_args()

    pipeline = DailyPipeline(base_output_dir=Path("output"))
    pipeline.run(dry_run=args.dry_run, posts_per_brand=args.posts, brand=args.brand)


if __name__ == "__main__":
    main()
