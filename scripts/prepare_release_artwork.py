#!/usr/bin/env python3
"""Create square release artwork locally without publishing unreleased files."""
import argparse
from pathlib import Path

from PIL import Image, ImageOps


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path, help="Approved source artwork (PNG, JPEG, or WebP)")
    parser.add_argument("--output-dir", type=Path, help="Output folder (defaults to the source folder)")
    args = parser.parse_args()

    source = args.source.expanduser().resolve()
    if not source.is_file():
        raise SystemExit(f"Source artwork not found: {source}")
    folder = (args.output_dir.expanduser().resolve() if args.output_dir else source.parent)
    folder.mkdir(parents=True, exist_ok=True)

    try:
        with Image.open(source) as opened:
            artwork = ImageOps.exif_transpose(opened).convert("RGB")
    except Exception as error:
        raise SystemExit(f"Cannot read source artwork: {error}") from error

    cover = ImageOps.fit(artwork, (3000, 3000), method=Image.Resampling.LANCZOS)
    thumb = ImageOps.fit(artwork, (600, 600), method=Image.Resampling.LANCZOS)
    cover_path = folder / "cover-square.jpg"
    thumb_path = folder / "thumbnail-square.jpg"
    cover.save(cover_path, "JPEG", quality=94, optimize=True, progressive=True)
    thumb.save(thumb_path, "JPEG", quality=90, optimize=True, progressive=True)

    print(f"Cover: {cover_path} — 3000 × 3000")
    print(f"Thumbnail: {thumb_path} — 600 × 600")


if __name__ == "__main__":
    main()
