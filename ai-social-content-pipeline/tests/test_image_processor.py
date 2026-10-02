from pathlib import Path

from PIL import Image

from src.processing.image_processor import resize_to_instagram


def test_resize_to_instagram_creates_1080x1350_jpeg(tmp_path: Path):
    source = tmp_path / "source.jpg"
    image = Image.new("RGB", (2000, 3000), color=(255, 255, 255))
    image.save(source)

    target = tmp_path / "output.jpg"
    final_path = resize_to_instagram(str(source), str(target))

    assert final_path == str(target)
    result = Image.open(target)
    assert result.size == (1080, 1350)
    assert result.mode == "RGB"
