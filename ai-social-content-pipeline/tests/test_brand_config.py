import json
from pathlib import Path

from src.config.settings import load_brand_config


def test_brand_config_loads_three_brands():
    config_path = Path(__file__).resolve().parents[1] / "config" / "brands.json"
    brands = load_brand_config(config_path)

    assert isinstance(brands, dict)
    assert len(brands) == 3
    assert {"home_decor", "girls_apparel", "mens_style"}.issubset(set(brands.keys()))

    for brand_name, brand in brands.items():
        assert "niche" in brand
        assert "content_categories" in brand
        assert "visual_style" in brand
        assert brand["instagram_format"]["aspect_ratio"] == "4:5"
