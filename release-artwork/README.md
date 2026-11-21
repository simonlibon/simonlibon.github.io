# Release artwork

Prepare artwork on your computer so unpublished artwork is not exposed through the public site repository.

1. Install Pillow: `python -m pip install Pillow`
2. Run: `python scripts/prepare_release_artwork.py /path/to/source.png --output-dir /path/to/output`

The script creates a square cover at 3000 × 3000 and a square shop thumbnail at 600 × 600. It center-crops non-square source images, so approve the crop before using it.

For an official release, attach `cover-square.jpg` to its Gumroad product. After the release art is ready to be public, add `thumbnail-square.jpg` under `release-artwork/<slug>/` in the repository. The Gumroad-to-site sync will use that thumbnail on both shop catalogs; until then, the Gumroad cover remains the fallback.

The source artwork itself stays local. The script prepares the two files but does not create the artwork concept, upload the cover to Gumroad, or publish a product.
