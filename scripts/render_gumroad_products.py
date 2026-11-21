#!/usr/bin/env python3
"""Static Gumroad product-detail mirror of the actual official product.html.

One page per published SKU. Clicking another format changes to its matching
branded detail page, while BUY NOW alone opens the real Gumroad checkout.
No remote catalog script or purchase side effect is necessary.
"""
import html
import re
from pathlib import Path
from urllib.parse import urlparse
if __package__:
    from .mirror_gumroad import ROOT, _inline_assets, _store_navigation, _functional_newsletter
    from .render_gumroad_catalog import detail_slug, detail_url, group_products
else:
    from mirror_gumroad import ROOT, _inline_assets, _store_navigation, _functional_newsletter
    from render_gumroad_catalog import detail_slug, detail_url, group_products

LABELS = {"tabs": "Guitar Tab (PDF)", "pack": "Tab + Backing Track", "bundle": "Complete EP Bundle"}
INCLUDES = {
    "tabs": ["Guitar tab (PDF)", "Digital download"],
    "pack": ["Guitar tab (PDF)", "Backing track without lead guitar", "Digital download"],
    "bundle": ["Tabs and backing tracks", "Digital download"],
}


def product_pages(products):
    """Yield (Gumroad page slug, group, selected purchase option)."""
    bundles, tracks = group_products(products)
    used = set()
    for group in bundles + tracks:
        for option in group["options"]:
            slug = detail_slug(group, option)
            if slug in used:
                raise ValueError("Duplicate product detail page slug " + slug)
            used.add(slug)
            yield slug, group, option


def detail_page(group, current):
    slug = detail_slug(group, current)
    page = (ROOT / "product.html").read_text(encoding="utf-8")
    page = _functional_newsletter(_store_navigation(_inline_assets(page, product=True)))
    escaped = lambda x: html.escape(str(x), quote=True)

    def once(old, new):
        nonlocal page
        if page.count(old) != 1:
            raise ValueError("Canonical product.html markup changed: " + old[:72])
        page = page.replace(old, new, 1)

    price = "€{:.2f}".format(current["price"])
    title = group["title"]
    description = current["description"].strip() or "Official digital download by Simon Libon."
    image = group.get("image") or ""
    if image and re.fullmatch(r"https://[^\s\"<>]+", image):
        cover = '<img src="' + escaped(image) + '" alt="Cover art for ' + escaped(title) + '" loading="eager">'
    else:
        cover = '<div class="cover-fallback">' + escaped(title) + '</div>'

    once('<title>Digital Product | Simon Libon</title>',
         '<title>' + escaped(title) + ' | Simon Libon</title>')
    once('<body data-page="product">',
         '<body data-page="product" data-sl-mirror="official-page-' + slug + '">')
    once('id="product-layout" class="sl-product-layout" hidden',
         'id="product-layout" class="sl-product-layout"')
    once('<div id="product-cover" class="sl-product-cover"></div>',
         '<div id="product-cover" class="sl-product-cover">' + cover + '</div>')
    once('<p id="product-type" class="sl-product-kicker">DIGITAL RELEASE</p>',
         '<p id="product-type" class="sl-product-kicker">' +
         ("EP COLLECTION" if group["kind"] == "bundle" else "INDIVIDUAL TRACK") + '</p>')
    once('<h1 id="product-title"></h1>', '<h1 id="product-title">' + escaped(title) + '</h1>')
    once('<div id="product-price" class="sl-product-price"></div>',
         '<div id="product-price" class="sl-product-price">' + escaped(price) + '</div>')
    once('<p id="product-description"></p>',
         '<p id="product-description" style="white-space:pre-line">' + escaped(description) + '</p>')
    once('id="product-included-section" class="sl-product-details" hidden',
         'id="product-included-section" class="sl-product-details"')
    once('<ul id="product-included"></ul>',
         '<ul id="product-included">' + ''.join('<li>' + escaped(v) + '</li>'
                                             for v in INCLUDES.get(current["kind"], ["Digital download"])) + '</ul>')
    # This matches the official selector's CSS and layout. Each format opens
    # its own static product detail, so no JavaScript is needed to switch.
    if len(group["options"]) > 1:
        rows = ['<fieldset class="shop-purchase-options"><legend>CHOOSE YOUR DOWNLOAD</legend>']
        for option in group["options"]:
            selected = option["checkout"] == current["checkout"]
            start = '<span class="shop-option selected" aria-current="true">' if selected else (
                '<a class="shop-option" href="' + escaped(detail_url(group, option)) + '">')
            marker = '◉' if selected else '◯'
            rows.append(start + '<span aria-hidden="true" class="sl-option-mark">' + marker + '</span>'
                        '<span class="shop-option-name">' +
                        escaped(LABELS.get(option["kind"], "Digital Download")) + '</span>'
                        '<strong class="shop-option-price">€{:.2f}</strong>'.format(option["price"]) +
                        ('</span>' if selected else '</a>'))
        rows.append('</fieldset>')
        tag = '<div id="product-price" class="sl-product-price">' + escaped(price) + '</div>'
        once(tag, tag + ''.join(rows))
    old_buy = '<a id="product-buy" class="sl-buy-button" href="#" target="_blank" rel="noopener noreferrer">BUY NOW · SECURE CHECKOUT</a>'
    once(old_buy, '<a id="product-buy" class="sl-buy-button" href="' +
         escaped(current["checkout"]) +
         '" target="_blank" rel="noopener noreferrer">BUY NOW · SECURE CHECKOUT</a>')
    # An official site duplicate on Gumroad does not need to repeatedly
    # explain that Gumroad manages the transaction.
    page = re.sub(r'<p class="sl-payment-copy">.*?</p>', '', page, count=1, flags=re.S)
    page, removed = re.subn(
        r'<div id="product-error" class="sl-product-unknown" hidden>.*?</div>',
        '', page, count=1, flags=re.S,
    )
    if removed != 1:
        raise ValueError("Could not remove dynamic-only product error placeholder")
    page = page.replace('</head>',
                        '<style>.sl-product-page .shop-option .sl-option-mark{font-size:16px;width:18px;flex:none}'
                        '.sl-product-page .shop-option:hover{text-decoration:none}'
                        '.sl-product-page .sl-product-cover img{object-fit:cover}'
                        '</style></head>', 1)
    required = ('data-sl-mirror="official-page-' + slug + '"', 'data-sl-mirror-css="style.css"',
                'data-sl-mirror-css="shop.css"', 'id="product-buy"', 'id="product-title"',
                'class="sl-product-layout"', current["checkout"].split("?")[0])
    if any(token not in page for token in required) or len(page) > 150000:
        raise ValueError("Product detail is incomplete or too large for Gumroad")
    return page


if __name__ == "__main__":
    for slug, group, product in product_pages([]):
        print(slug)
