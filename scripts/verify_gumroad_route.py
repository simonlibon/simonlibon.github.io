#!/usr/bin/env python3
"""Read-only website-to-Gumroad route integrity and revision verification."""
import argparse
import re
from pathlib import Path
try:
    from .render_gumroad_catalog import detail_url, group_products, load_catalog
except ImportError:
    from render_gumroad_catalog import detail_url, group_products, load_catalog

STAMP = re.compile(r'<main\b[^>]*\bdata-sl-mirror-sha="([0-9a-f]{20})"', re.I)
SECTIONS = {"music", "concerts", "tabs", "merch", "press", "privacy"}

def revision(document):
    found = STAMP.findall(document)
    if len(found) != 1:
        raise ValueError("Missing or duplicated Gumroad route revision on main")
    return found[0]

def check(slug, document, generated=True):
    revision(document)
    for required in ("SIMON LIBON", 'class="header"', 'class="footer"',
                     'data-sl-mirror-css="style.css"'):
        if required not in document:
            raise ValueError("Gumroad "+slug+" missing "+required)
    if slug in SECTIONS:
        # Gumroad strips data attributes on <body> but preserves the
        # current fingerprint on <main>. Only the generated HTML must
        # carry the unsanitized body identity.
        if generated and f'data-sl-mirror="official-page-{slug}"' not in document:
            raise ValueError("Incorrect official page identity: "+slug)
        if 'href="https://simonlibon.github.io/?newsletter=1"' not in document:
            raise ValueError("Missing newsletter signup on "+slug)
        if slug == "tabs":
            bundles, tracks = group_products(load_catalog())
            groups = bundles + tracks
            if document.count('class="shop-item"') != len(groups):
                raise ValueError("Missing Gumroad product cards")
            if any(detail_url(g) not in document for g in groups):
                raise ValueError("Wrong Gumroad product details route")
            # Gumroad strips custom <body> attributes; product cards and
            # canonical revision on <main> are the published-page checks.
            if generated and 'data-sl-static-catalog="1"' not in document:
                raise ValueError("Gumroad static catalogue removed")
            if 'class="shop-cart-link"' not in document:
                raise ValueError("Gumroad shop cart shortcut removed")
        return
    if re.fullmatch(r"product-[A-Za-z0-9_-]+", slug):
        if generated and f'data-sl-mirror="official-page-{slug}"' not in document:
            raise ValueError("Incorrect product page identity: "+slug)
        for required in ('data-sl-mirror-css="shop.css"', 'class="sl-product-layout"',
                         'id="product-buy"', 'id="product-price"', 'id="product-cover"',
                         'simonlibonstore.gumroad.com/l/'):
            if required not in document:
                raise ValueError("Gumroad "+slug+" missing "+required)
        for tag in re.findall(r"<a\b[^>]*>", document, flags=re.I):
            if re.search(r"shop-cart-link|sl-product-cart-link|gumroad\.com/checkout", tag, re.I):
                raise ValueError("Product route has unwanted cart")
        return
    raise ValueError("Unexpected Gumroad slug: "+slug)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--slug",required=True)
    parser.add_argument("--generated",required=True)
    parser.add_argument("--published")
    opts=parser.parse_args()
    source=Path(opts.generated).read_text(encoding="utf-8")
    check(opts.slug,source)
    if opts.published:
        published=Path(opts.published).read_text(encoding="utf-8")
        check(opts.slug,published,generated=False)
        if revision(published)!=revision(source):
            raise SystemExit("GUMROAD STALE: "+opts.slug+"; version does not match official website")
        print("MATCHING PUBLISHED GUMROAD ROUTE",opts.slug,revision(published))
    else:
        print("VALID GENERATED GUMROAD ROUTE",opts.slug,revision(source))

if __name__=="__main__":
    main()
