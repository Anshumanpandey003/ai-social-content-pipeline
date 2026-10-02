#!/usr/bin/env python3
"""
AI Social Content Pipeline - Single Script Version

Generates Instagram-ready social content (captions, topics, hashtags, and images)
for 3 brands using Google Gemini 2.5 Flash for text and Imagen 3.0 for images.
"""

import os
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import google.genai
from PIL import Image
from io import BytesIO


# Configuration
BRANDS = ["home_decor", "girls_apparel", "mens_style"]
POSTS_PER_BRAND = 3

# Brand positioning and visual guidance
BRAND_CONFIG = {
    "home_decor": {
        "positioning": "Premium, modern home aesthetics with focus on minimalism and functionality.",
        "visual_style": "Bright, clean spaces with neutral tones and natural light.",
        "target_audience": "Design-conscious millennials and young professionals.",
    },
    "girls_apparel": {
        "positioning": "Trendy, inclusive fashion for young women emphasizing confidence and self-expression.",
        "visual_style": "Vibrant colors, dynamic poses, lifestyle moments with friends.",
        "target_audience": "Teen girls and young women aged 14-25.",
    },
    "mens_style": {
        "positioning": "Smart casual and formal menswear focusing on quality and versatility.",
        "visual_style": "Clean, professional styling with warm tones and confident poses.",
        "target_audience": "Young professionals and style-conscious men aged 20-40.",
    },
}


def get_api_key() -> str:
    """Read GEMINI_API_KEY from environment variables."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY not set. Please set the environment variable: export GEMINI_API_KEY=your_key_here"
        )
    return api_key


def initialize_client() -> google.genai.Client:
    """Initialize Google Genai client."""
    api_key = get_api_key()
    return google.genai.Client(api_key=api_key)


def generate_content(
    client: google.genai.Client, brand: str, post_index: int
) -> dict:
    """
    Generate content (topic, caption, hashtags) using Gemini 2.5 Flash.
    
    Args:
        client: Google Genai client
        brand: Brand name (home_decor, girls_apparel, or mens_style)
        post_index: Post number (1-3)
    
    Returns:
        Dictionary with topic, caption, hashtags, and image_prompt
    """
    brand_info = BRAND_CONFIG[brand]
    
    prompt = f"""You are a social media content strategist for a {brand.replace('_', ' ')} brand.

Brand Positioning: {brand_info['positioning']}
Visual Style: {brand_info['visual_style']}
Target Audience: {brand_info['target_audience']}

Generate Instagram content for post #{post_index}. Respond with valid JSON only (no markdown, no code blocks):
{{
    "topic": "A specific, engaging topic or trend (max 50 characters)",
    "caption": "An engaging Instagram caption (max 150 characters) with personality and call-to-action",
    "hashtags": "10-15 relevant hashtags as a space-separated string",
    "image_prompt": "A detailed, vivid 4:5 aspect ratio image prompt for Imagen (max 200 characters)"
}}

Respond ONLY with the JSON object, no other text."""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )
    
    # Parse the response
    content_text = response.text.strip()
    content_data = json.loads(content_text)
    
    return content_data


def generate_image(
    client: google.genai.Client, prompt: str, brand: str, post_index: int
) -> Optional[Image.Image]:
    """
    Generate a 4:5 aspect ratio image using Imagen 3.0.
    
    Args:
        client: Google Genai client
        prompt: Image generation prompt
        brand: Brand name (for logging)
        post_index: Post number (for logging)
    
    Returns:
        PIL Image object resized to 1080x1350, or None if generation fails
    """
    try:
        print(f"  Generating image for {brand} post #{post_index}...")
        
        # Generate image using Imagen 3.0
        image_response = client.models.generate_images(
            model="imagen-3.0-generate-002",
            prompt=prompt,
            config={
                "aspect_ratio": "4:5",
                "safety_filter_level": "block_none",
            }
        )
        
        if not image_response or not image_response.generated_images:
            print(f"    ⚠ No image generated for {brand} post #{post_index}")
            return None
        
        # Get the first generated image
        image_data = image_response.generated_images[0]
        
        # Convert bytes to PIL Image
        img = Image.open(BytesIO(image_data.image_bytes))
        
        # Resize to exact Instagram size (1080x1350 for 4:5)
        img_resized = img.resize((1080, 1350), Image.Resampling.LANCZOS)
        
        print(f"    ✓ Image generated and resized to 1080x1350")
        return img_resized
        
    except Exception as e:
        print(f"    ✗ Image generation failed: {e}")
        return None


def save_output(
    brand: str,
    post_index: int,
    content: dict,
    image: Optional[Image.Image],
    output_dir: str,
) -> None:
    """
    Save content JSON and image to output directory.
    
    Args:
        brand: Brand name
        post_index: Post number
        content: Content dictionary
        image: PIL Image object or None
        output_dir: Output directory path
    """
    # Create brand-specific output directory
    brand_dir = Path(output_dir) / brand
    brand_dir.mkdir(parents=True, exist_ok=True)
    
    # Save JSON metadata
    json_path = brand_dir / f"post_{post_index:02d}.json"
    with open(json_path, "w") as f:
        json.dump(content, f, indent=2)
    print(f"  Saved metadata: {json_path}")
    
    # Save image if generated
    if image:
        jpg_path = brand_dir / f"post_{post_index:02d}.jpg"
        image.save(jpg_path, "JPEG", quality=95)
        print(f"  Saved image: {jpg_path}")


def run_pipeline(posts_per_brand: int = 3) -> None:
    """
    Run the full content generation pipeline.
    
    Args:
        posts_per_brand: Number of posts to generate per brand (default 3)
    """
    # Initialize client
    client = initialize_client()
    
    # Create dated output directory
    today = datetime.now().strftime("%Y-%m-%d")
    output_dir = Path("output") / today
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"🚀 Starting AI Social Content Pipeline")
    print(f"📅 Date: {today}")
    print(f"📊 Brands: {len(BRANDS)}, Posts per brand: {posts_per_brand}")
    print(f"📁 Output directory: {output_dir}\n")
    
    manifest = {
        "date": today,
        "timestamp": datetime.now().isoformat(),
        "brands": BRANDS,
        "posts_per_brand": posts_per_brand,
        "posts": [],
    }
    
    # Generate content for each brand
    for brand in BRANDS:
        print(f"📝 Processing brand: {brand}")
        
        for post_index in range(1, posts_per_brand + 1):
            print(f"  Post #{post_index}...")
            
            try:
                # Generate content
                content = generate_content(client, brand, post_index)
                
                # Generate image
                image = generate_image(client, content["image_prompt"], brand, post_index)
                
                # Save output
                save_output(brand, post_index, content, image, output_dir)
                
                # Add to manifest
                manifest["posts"].append({
                    "brand": brand,
                    "post_number": post_index,
                    "status": "success",
                    "topic": content.get("topic"),
                    "image_generated": image is not None,
                })
                
            except Exception as e:
                print(f"    ✗ Error processing {brand} post #{post_index}: {e}")
                manifest["posts"].append({
                    "brand": brand,
                    "post_number": post_index,
                    "status": "failed",
                    "error": str(e),
                })
        
        print()
    
    # Save manifest
    manifest_path = output_dir / "manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    
    print(f"✅ Pipeline complete!")
    print(f"📄 Manifest: {manifest_path}")
    print(f"📂 All outputs saved to: {output_dir}")


def main():
    """Main entry point."""
    try:
        run_pipeline(posts_per_brand=POSTS_PER_BRAND)
    except KeyboardInterrupt:
        print("\n⚠ Pipeline interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Pipeline failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
