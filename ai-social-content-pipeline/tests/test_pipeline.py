import json
from pathlib import Path

from src.pipeline.daily_pipeline import DailyPipeline


def test_manifest_creation_and_dry_run(tmp_path: Path):
    pipeline = DailyPipeline(base_output_dir=tmp_path)
    manifest = pipeline.run(dry_run=True, posts_per_brand=1)

    assert manifest is not None
    assert manifest["total_posts"] == 3
    assert manifest["successful"] == 3
    assert manifest["failed"] == 0

    date_dir = tmp_path / manifest["date"]
    assert date_dir.exists()
    assert (date_dir / "manifest.json").exists()

    for brand in ["home_decor", "girls_apparel", "mens_style"]:
        brand_dir = date_dir / brand
        assert brand_dir.exists()
        assert len(list(brand_dir.glob("*.json"))) == 1
