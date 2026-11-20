#!/usr/bin/env python3
"""One design source for the Simon Libon website and Gumroad custom HTML.

Copies the CURRENT official HTML/CSS, not a second hand-maintained theme.
The Gumroad checkout, receipt and delivery are still Gumroad-owned.
"""
import html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = "https://simonlibon.github.io/"
STORE = "https://simonlibonstore.gumroad.com/"

def _inline_assets(document, product=False):
    """Inlining shared CSS is important: Gumroad may strip external stylesheets."""
    for filename in ("style.css", "shop.css"):
        stylesheet = re.compile(r'<link\b(?=[^>]*\bhref=["\x27]' + re.escape(filename) +
                                r'(?:\?[^"\x27]*)?["\x27])[^>]*>', re.I)
        if stylesheet.search(document):
            css = (ROOT / filename).read_text(encoding="utf-8")
            # A namespaced mirror tag makes source drift easy to verify.
            document = stylesheet.sub(lambda _: '<style data-sl-mirror-css="' + filename + '">\n' +
                                       css + '\n</style>', document)
    site_script = re.compile(r'<script\s+src=["\x27]site\.js(?:\?[^"\x27]*)?["\x27]\s*></script>', re.I)
    document = site_script.sub(lambda _: '<script data-sl-mirror-js="site.js">\n' +
                               (ROOT / "site.js").read_text(encoding="utf-8") +
                               '\n</script>', document)
    if product:
        document = re.sub(r'<script\s+src=["\x27]product\.js(?:\?[^"\x27]*)?["\x27][^>]*></script>',
                          '', document, flags=re.I)
    # Convert local assets and internal links to real, absolute URLs. If the
    # Gumroad standalone pages don't exist, navigation still works on the
    # real official website, and the original DOM/CSS stays exactly the same.
    def absolute(match):
        attr, path = match.group(1), match.group(2)
        if path.startswith(("#", "mailto:", "tel:", "https:", "http:", "data:", "javascript:")):
            return match.group(0)
        if path.startswith("/"):
            return attr + '="' + SITE.rstrip("/") + path + '"'
        return attr + '="' + SITE + path + '"'
    document = re.sub(r'\b(href|src)="([^"]+)"', absolute, document)
    return document

def mirror_profile():
    source = (ROOT / "index.html").read_text(encoding="utf-8")
    out = _inline_assets(source)
    # The page is a visual clone; this marker is a deployment assertion.
    out = out.replace("<body data-page=\"home\">",
                      '<body data-page="home" data-sl-mirror="official-home-v2">', 1)
    if 'data-sl-mirror="official-home-v2"' not in out or 'data-sl-mirror-css="style.css"' not in out:
        raise ValueError("Cannot mirror canonical homepage")
    return out

def mirror_product(p, cover_html, type_label, price_fallback, includes):
    out = (ROOT / "product.html").read_text(encoding="utf-8")
    out = _inline_assets(out, product=True)
    def once(old, new):
        nonlocal out
        if out.count(old) != 1:
            raise ValueError("Canonical product template changed: " + old[:80])
        out = out.replace(old, new, 1)
    once('id="main-content" class="sl-shop sl-product-page"',
         'id="main-content" class="sl-shop sl-product-page" data-sl-product-template="v2"')
    once('id="product-layout" class="sl-product-layout" hidden',
         'id="product-layout" class="sl-product-layout"')
    once('<div id="product-cover" class="sl-product-cover"></div>',
         '<div id="product-cover" class="sl-product-cover">' + cover_html + '</div>')
    once('<p id="product-type" class="sl-product-kicker">DIGITAL RELEASE</p>',
         '<p id="product-type" class="sl-product-kicker">' + html.escape(type_label) + '</p>')
    once('<h1 id="product-title"></h1>',
         '<h1 id="product-title" data-gumroad-field="name">' +
         html.escape(str(p.get("name") or "Digital Download")) + '</h1>')
    once('<div id="product-price" class="sl-product-price"></div>',
         '<div id="product-price" class="sl-product-price" data-gumroad-field="price">' +
         html.escape(str(price_fallback)) + '</div>')
    # A native Gumroad action is required on its own product landing page.
    old_buy = '<a id="product-buy" class="sl-buy-button" href="#" target="_blank" rel="noopener noreferrer">BUY NOW · SECURE CHECKOUT</a>'
    once(old_buy, '<a id="product-buy" class="sl-buy-button" data-gumroad-action="buy">BUY NOW · SECURE CHECKOUT</a>')
    once('<p id="product-description"></p>',
         '<div id="product-description" data-gumroad-field="description"><p>Official digital download by Simon Libon.</p></div>')
    once('id="product-included-section" class="sl-product-details" hidden',
         'id="product-included-section" class="sl-product-details"')
    once('<ul id="product-included"></ul>',
         '<ul id="product-included">' + ''.join('<li>' + html.escape(x) + '</li>' for x in includes) + '</ul>')
    # No "product unavailable" flash or dynamic query resolver on a real Gumroad page.
    out = re.sub(r'<div id="product-error" class="sl-product-unknown" hidden>.*?</div>', '',
                 out, count=1, flags=re.S)
    out = out.replace('</head>',
                      '<style>#product-description{font-size:16px;line-height:1.65;color:#333038}'
                      '#product-description p{margin:0 0 14px}'
                      '#product-description a{text-decoration:underline}'
                      '.sl-product-page [data-gumroad-action="buy"]{cursor:pointer}'
                      '</style></head>', 1)
    required = ('data-sl-product-template="v2"', 'data-gumroad-field="name"',
                'data-gumroad-field="price"', 'data-gumroad-field="description"',
                'data-gumroad-action="buy"', 'data-sl-mirror-css="style.css"',
                'data-sl-mirror-css="shop.css"')
    if any(marker not in out for marker in required) or len(out) > 150000:
        raise ValueError("Missing essential native product field or page too large")
    return out
