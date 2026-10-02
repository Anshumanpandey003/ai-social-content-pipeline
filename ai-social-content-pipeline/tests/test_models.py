from src.content.models import GeneratedPost, validate_hashtags


def test_generated_post_model_validation():
    post = GeneratedPost(
        content_id="test-123",
        brand="home_decor",
        topic="Cozy bedroom refresh",
        hook="Small changes, big mood.",
        image_prompt="A warm bedroom ...",
        caption="A calm bedroom upgrade for slow mornings.",
        hashtags=["#home", "#decor", "#interior", "#cozy", "#design", "#bedroom", "#warmth", "#minimalism", "#livingroom", "#inspiration"],
        alt_text="A cozy bedroom with soft textures and natural light.",
        created_at="2026-01-01T00:00:00Z",
        status="generated",
    )

    assert post.content_id == "test-123"
    assert len(post.hashtags) == 10


def test_hashtags_must_be_relevant_and_valid():
    hashtags = [
        "#home",
        "#decor",
        "#interior",
        "#cozy",
        "#design",
        "#bedroom",
        "#warmth",
        "#minimalism",
        "#livingroom",
        "#inspiration",
        "#buynow",
        "#viral",
        "#foryou",
        "#trending",
        "#sale",
    ]

    validated = validate_hashtags(hashtags)
    assert len(validated) == 15
    assert all(tag.startswith("#") for tag in validated)
    assert "#sale" in validated
