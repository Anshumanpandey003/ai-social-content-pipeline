import argparse

from src.main import build_parser


def test_parser_supports_brand_and_dry_run():
    parser = build_parser()
    args = parser.parse_args(["--brand", "home_decor", "--posts", "1", "--dry-run"])

    assert args.brand == "home_decor"
    assert args.posts == 1
    assert args.dry_run is True
