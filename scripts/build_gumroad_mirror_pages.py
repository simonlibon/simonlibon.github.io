#!/usr/bin/env python3
"""Build the official public site sections for Gumroad standalone HTML pages."""
import argparse
from pathlib import Path
from mirror_gumroad import PAGE_SOURCES, mirror_standalone
from render_gumroad_catalog import load_catalog
from render_gumroad_products import product_pages, detail_page

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    target = Path(args.output_dir)
    target.mkdir(parents=True, exist_ok=True)
    for slug in PAGE_SOURCES:
        body = mirror_standalone(slug)
        path = target / (slug + ".html")
        path.write_text(body, encoding="utf-8")
        print(slug + ": " + str(len(body)) + " characters, mirrored from official website")
    # Every published product format gets its own styled Gumroad detail page.
    # Separate static pages keep the Tab/Track selector functional without JS.
    product_slugs = []
    for slug, group, selected in product_pages(load_catalog()):
        page = detail_page(group, selected)
        (target / (slug + ".html")).write_text(page, encoding="utf-8")
        product_slugs.append(slug)
        print(slug + ": " + str(len(page)) + " characters, mirrored from official product.html")
    (target / "product-slugs.txt").write_text("\n".join(product_slugs) + ("\n" if product_slugs else ""), encoding="utf-8")


if __name__ == "__main__":
    main()
