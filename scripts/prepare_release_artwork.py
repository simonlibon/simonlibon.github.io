#!/usr/bin/env python3
"""Create the square Gumroad cover and small square storefront thumbnail."""
import argparse
from pathlib import Path
import re

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://raw.githubusercontent.com/simonlibon/simonlibon.github.io/main"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("slug", help="Lowercase release slug, for example new-single")
    args = parser.parse_args()
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", args.slug):
        raise SystemExit("Slug must use lowercase letters, digits, and single hyphens.")

    folder = ROOT / "release-artwork" / args.slug
    candidates = [folder / "source.png", folder / "source.jpg", folder / "source.jpeg", folder / "source.webp"]
    source = next((path for path in candidates if path.is_file()), None)
    if source is None:
        raise SystemExit("Add release-artwork/<slug>/source.png (or .jpg/.webp) first.")

    with Image.open(source) as opened:
        artwork = ImageOps.exif_transpose(opened).convert("RGB")
        # Keep the art square and center-crop any non-square source consistently.
        cover = ImageOps.fit(artwork, (3000, 3000), method=Image.Resampling.LANCZOS)
        thumb = ImageOps.fit(artwork, (600, 600), method=Image.Resampling.LANCZOS)
        cover_path = folder / "cover-square.jpg"
        thumb_path = folder / "thumbnail-square.jpg"
        cover.save(cover_path, "JPEG", quality=94, optimize=True, progressive=True)
        thumb.save(thumb_path, "JPEG", quality=90, optimize=True, progressive=True)

    print(f"Cover: {cover_path.relative_to(ROOT)} (3000x3000)")
    print(f"Thumbnail: {thumb_path.relative_to(ROOT)} (600x600)")
    print(f"Cover URL: {BASE}/release-artwork/{args.slug}/cover-square.jpg")
    print(f"Thumbnail URL: {BASE}/release-artwork/{args.slug}/thumbnail-square.jpg")


if __name__ == "__main__":
    main()
