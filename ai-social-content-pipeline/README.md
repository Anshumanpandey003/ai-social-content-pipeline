# AI Social Content Pipeline

A production-ready V1 content-generation pipeline for creating Instagram-ready social content drafts locally without automatic publishing.

## Purpose

This project generates daily batch content for three brand pages:

- Home Decor
- Girls Apparel
- Men's Style

Each run creates a batch of 9 content drafts (3 per brand), saves the metadata locally, and optionally generates placeholder or final images when the Gemini API is available.

## Architecture

The codebase is split into focused modules:

- `config/brands.json` stores brand-specific positioning and visual guidance.
- `src/config/settings.py` reads environment configuration.
- `src/gemini/client.py` wraps the official `google-genai` client.
- `src/gemini/content_generator.py` creates content concepts via Gemini text generation.
- `src/gemini/image_generator.py` isolates the provider for image generation.
- `src/processing/image_processor.py` resizes and prepares images to Instagram 4:5 format.
- `src/pipeline/daily_pipeline.py` orchestrates the full run.
- `src/main.py` exposes the CLI.

## Folder structure

```text
ai-social-content-pipeline/
├── config/
│   └── brands.json
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py
│   ├── gemini/
│   │   ├── __init__.py
│   │   ├── client.py
│   │   ├── content_generator.py
│   │   └── image_generator.py
│   ├── content/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   └── prompts.py
│   ├── processing/
│   │   ├── __init__.py
│   │   └── image_processor.py
│   └── pipeline/
│       ├── __init__.py
│       └── daily_pipeline.py
├── output/
├── tests/
├── .env.example
├── .gitignore
├── requirements.txt
├── README.md
├── run.py
└── .env
```

## Python version

This project targets Python 3.11+.

## Installation

1. Create a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Gemini API key

1. Go to Google AI Studio.
2. Create an API key.
3. Save it in a local `.env` file based on `.env.example`.

Example:

```bash
GEMINI_API_KEY=your_api_key_here
GEMINI_TEXT_MODEL=gemini-2.5-flash
GEMINI_IMAGE_MODEL=gemini-3.1-flash-image
OUTPUT_DIR=output
REQUEST_DELAY_SECONDS=1.0
```

> Do not hard-code API keys in source files. The key must come from the environment variable `GEMINI_API_KEY`.

## Environment configuration

The project reads settings from `.env` via `python-dotenv`.

## Running the pipeline

### Generate a full daily batch

```bash
python run.py
```

This creates a date-based output folder and saves all content metadata and generated images.

### Generate one brand only

```bash
python run.py --brand home_decor
python run.py --brand girls_apparel
python run.py --brand mens_style
```

### Generate a small test batch

```bash
python run.py --posts 1
```

This creates one post per brand (3 total).

### Dry run

```bash
python run.py --dry-run
```

Dry run generates the JSON metadata and prompt structure without calling the Gemini image-generation API or consuming image-generation quota.

## Output organization

Each daily run is saved in a date-based folder such as:

```text
output/
└── 2026-10-03/
    ├── home_decor/
    │   ├── post_01.json
    │   ├── post_01.jpg
    │   ├── post_02.json
    │   ├── post_02.jpg
    │   ├── post_03.json
    │   └── post_03.jpg
    ├── girls_apparel/
    ├── mens_style/
    └── manifest.json
```

The manifest contains the post-level status and records.

## Troubleshooting

- If `GEMINI_API_KEY` is missing, live generation fails fast with a clear message.
- If Gemini image generation is unavailable on the configured model, the code raises a clear provider error rather than silently switching providers.
- If the pipeline fails on one image, it continues with other posts and marks the failed item as `failed` with an error description.
- If rate limiting occurs, use `REQUEST_DELAY_SECONDS` to introduce a pause between requests.

## API quota and cost considerations

Gemini image generation may not be free for the selected model or tier. This project intentionally does not claim free usage. Always check the current model pricing for the account and tier before running full live batches.

## Future Instagram API integration

This V1 stores generated content locally and is designed so a future V2 can add Instagram Graph API publishing without rewriting the core pipeline structure.

## Security

The repository includes `.env` in `.gitignore` and does not commit secrets or tokens.
