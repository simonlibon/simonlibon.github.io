#!/usr/bin/env python3
"""Static Gumroad product-detail mirror of the actual official product.html.

Each published SKU has a branded entry URL. Format choices switch in place
using CSS radio controls (no reload or JavaScript required), while BUY NOW
opens the selected real Gumroad checkout.
"""
import html
import re
from pathlib import Path
from urllib.parse import urlparse
if __package__:
    from .mirror_gumroad import ROOT, _inline_assets, _store_navigation, _functional_newsletter, stamp_mirror_revision
    from .render_gumroad_catalog import detail_slug, detail_url, group_products
else:
    from mirror_gumroad import ROOT, _inline_assets, _store_navigation, _functional_newsletter, stamp_mirror_revision
    from render_gumroad_catalog import detail_slug, detail_url, group_products

LABELS = {"tabs": "Guitar Tab (PDF)", "pack": "Tab + Backing Track", "bundle": "Complete EP Bundle"}
INCLUDES = {
    "tabs": ["Guitar tab (PDF)"],
    "pack": ["Guitar tab (PDF)", "Backing track (audio)"],
    "bundle": ["Tabs and backing tracks"],
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
    variants = group["options"]
    if len(variants) > 1:
        # Radios are direct siblings of price, selector, button and description.
        # CSS general-sibling selectors switch these panels without JavaScript,
        # redirecting, scrolling to an anchor, or changing the browser URL.
        def token(option):
            kind = option["kind"]
            if not re.fullmatch(r"[a-z]+", kind):
                raise ValueError("Invalid download format")
            return kind

        inputs, choices, prices, buttons, descriptions, details = [], [], [], [], [], []
        for option in variants:
            kind = token(option)
            selected = option["checkout"] == current["checkout"]
            radio_id = "sl-format-" + kind
            checked = ' checked="checked"' if selected else ""
            inputs.append('<input class="sl-format-radio" type="radio" id="' +
                          radio_id + '" name="sl-download-format" value="' +
                          kind + '"' + checked + '>')
            choices.append('<label class="shop-option" for="' + radio_id + '">' +
                           '<span class="sl-option-dot" aria-hidden="true"></span>' +
                           '<span class="shop-option-name">' + escaped(LABELS.get(kind, "Digital Download")) + '</span>' +
                           '<strong class="shop-option-price">€{:.2f}</strong>'.format(option["price"]) +
                           '</label>')
            prices.append('<span class="sl-variant-price" data-sl-kind="' + kind +
                          '">€{:.2f}</span>'.format(option["price"]))
            # This is the ONLY link that opens Gumroad checkout for this format.
            button_id = ' id="product-buy"' if selected else ""
            buttons.append('<a' + button_id + ' class="sl-buy-button sl-variant-buy" ' +
                           'data-sl-kind="' + kind + '" href="' + escaped(option["checkout"]) +
                           '" target="_blank" rel="noopener noreferrer">BUY NOW · SECURE CHECKOUT</a>')
            descriptions.append('<span class="sl-variant-description" data-sl-kind="' + kind +
                                '">' + escaped(option["description"].strip() or
                                "Official digital download by Simon Libon.") + '</span>')
            details.append('<ul class="sl-variant-includes" data-sl-kind="' + kind + '">' +
                           ''.join('<li>' + escaped(v) + '</li>' for v in
                                   (option.get("includes") or INCLUDES.get(kind, ["Digital download"]))) + '</ul>')
        once('<div id="product-price" class="sl-product-price"></div>',
             ''.join(inputs) +
             '<div id="product-price" class="sl-product-price">' + ''.join(prices) + '</div>' +
             '<fieldset class="shop-purchase-options"><legend>CHOOSE YOUR DOWNLOAD</legend>' +
             ''.join(choices) + '</fieldset>')
        once('<a id="product-buy" class="sl-buy-button" href="#" target="_blank" rel="noopener noreferrer">BUY NOW · SECURE CHECKOUT</a>',
             '<div class="sl-buy-variants">' + ''.join(buttons) + '</div>')
        once('<p id="product-description"></p>',
             '<p id="product-description" class="sl-variant-description-wrap">' +
             ''.join(descriptions) + '</p>')
        once('id="product-included-section" class="sl-product-details" hidden',
             'id="product-included-section" class="sl-product-details"')
        once('<ul id="product-included"></ul>',
             '<div id="product-included">' + ''.join(details) + '</div>')
    else:
        once('<div id="product-price" class="sl-product-price"></div>',
             '<div id="product-price" class="sl-product-price">' + escaped(price) + '</div>')
        once('<p id="product-description"></p>',
             '<p id="product-description" style="white-space:pre-line">' + escaped(description) + '</p>')
        once('id="product-included-section" class="sl-product-details" hidden',
             'id="product-included-section" class="sl-product-details"')
        once('<ul id="product-included"></ul>',
             '<ul id="product-included">' + ''.join('<li>' + escaped(v) + '</li>'
                                                  for v in (current.get("includes") or INCLUDES.get(current["kind"], ["Digital download"]))) + '</ul>')
        once('<a id="product-buy" class="sl-buy-button" href="#" target="_blank" rel="noopener noreferrer">BUY NOW · SECURE CHECKOUT</a>',
             '<a id="product-buy" class="sl-buy-button" href="' + escaped(current["checkout"]) +
             '" target="_blank" rel="noopener noreferrer">BUY NOW · SECURE CHECKOUT</a>')
    # Keep the same small delivery/security line across all three product routes.
    # The product description now has its own spacing and subtle divider.
    page, removed = re.subn(
        r'<div id="product-error" class="sl-product-unknown" hidden>.*?</div>',
        '', page, count=1, flags=re.S,
    )
    if removed != 1:
        raise ValueError("Could not remove dynamic-only product error placeholder")
    # The selector works on Gumroad even when inline scripts are blocked.
    # CSS :checked and general siblings update the highlighted choice, price,
    # description, included downloads and checkout link on this SAME page.
    css = """
<style data-sl-inline-formats="v3">
.sl-product-page .sl-product-cover img{object-fit:cover}
.sl-product-page .sl-format-radio{position:absolute!important;width:1px!important;height:1px!important;opacity:0!important;clip-path:inset(50%)!important}
.sl-product-page .shop-purchase-options .shop-option{cursor:pointer}
.sl-product-page .shop-purchase-options .sl-option-dot{width:14px;height:14px;border:1px solid #28282c;border-radius:50%;flex:0 0 14px;display:inline-flex;align-items:center;justify-content:center}
.sl-product-page .sl-variant-price,
.sl-product-page .sl-variant-buy,
.sl-product-page .sl-variant-description,
.sl-product-page .sl-variant-includes{display:none!important}
.sl-product-page .sl-variant-description-wrap{white-space:pre-line}
.sl-product-page .sl-buy-variants .sl-buy-button{display:none}
"""
    if len(variants) > 1:
        for option in variants:
            kind = token(option)
            selector = '#sl-format-' + kind + ':checked ~ '
            css += (selector + '#product-price .sl-variant-price[data-sl-kind="' + kind + '"],\n' +
                    selector + '.sl-buy-variants .sl-variant-buy[data-sl-kind="' + kind + '"],\n' +
                    selector + '#product-description .sl-variant-description[data-sl-kind="' + kind + '"],\n' +
                    selector + '#product-included-section .sl-variant-includes[data-sl-kind="' + kind +
                    '"]{display:block!important}\n')
            css += (selector + '.shop-purchase-options label[for="sl-format-' + kind +
                    '"]{border-color:#19191e!important;background:#f0eeeb!important}\n')
            css += (selector + '.shop-purchase-options label[for="sl-format-' + kind +
                    '"] .sl-option-dot:after{content:"";width:7px;height:7px;background:#19191e;border-radius:50%}\n')
            css += ('#sl-format-' + kind + ':focus-visible ~ .shop-purchase-options label[for="sl-format-' +
                    kind + '"]{outline:2px solid #917cb1;outline-offset:3px}\n')
    css += '</style>'
    page = page.replace('</head>', css + '</head>', 1)
    required = ('data-sl-mirror="official-page-' + slug + '"', 'data-sl-mirror-css="style.css"',
                'data-sl-mirror-css="shop.css"', 'id="product-buy"', 'id="product-title"',
                'class="sl-product-layout"', current["checkout"].split("?")[0])
    if any(token not in page for token in required) or len(page) > 150000:
        raise ValueError("Product detail is incomplete or too large for Gumroad")
    return stamp_mirror_revision(page)


if __name__ == "__main__":
    for slug, group, product in product_pages([]):
        print(slug)
