#!/usr/bin/env python3
"""One design source for the Simon Libon website and Gumroad custom HTML.

Copies the CURRENT official HTML/CSS, not a second hand-maintained theme.
The Gumroad checkout, receipt and delivery are still Gumroad-owned.
"""
import html
import re
from pathlib import Path
from urllib.parse import unquote
if __package__:
    from .render_gumroad_catalog import load_catalog, render_shop
else:
    from render_gumroad_catalog import load_catalog, render_shop

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

def _store_navigation(document):
    """Keep the canonical visual design but link to verified Gumroad page slugs."""
    pages = {
        "index.html": "",
        "music.html": "music",
        "concerts.html": "concerts",
        "tabs.html": "tabs",
        "merch.html": "merch",
        "press.html": "press",
        "privacy.html": "privacy",
    }
    for filename, slug in pages.items():
        old = 'href="' + SITE + filename
        # Preserve query and hash components while changing only the route.
        document = document.replace(old + '"', 'href="' + STORE + slug + '"')
        document = document.replace(old + '?', 'href="' + STORE + slug + '?')
        document = document.replace(old + '#', 'href="' + STORE + slug + '#')
    document = document.replace('href="' + SITE + '"', 'href="' + STORE + '"')
    return document

def _functional_newsletter(document):
    """Gumroad strips EmailOctopus' form script: never show an empty dialog.

    Link to the real matching newsletter popup hosted on the official site.
    The subscriber still sees Simon Libon's design and actual signup fields.
    """
    url = SITE + "?newsletter=1"
    def fix_link(m):
        tag = m.group(0)
        tag = re.sub(r'\sdata-newsletter-open(?:="[^"]*")?', '', tag)
        tag = re.sub(r'\saria-haspopup="dialog"', '', tag)
        if not re.search(r'\bhref="[^"]*"', tag):
            raise ValueError("Newsletter link without href")
        return re.sub(r'\bhref="[^"]*"', 'href="' + url + '"', tag, count=1)
    document = re.sub(r'<a\b[^>]*\bdata-newsletter-open\b[^>]*>', fix_link,
                      document, flags=re.I)
    # The embedded signup script isn't permitted on native Gumroad custom HTML.
    # Removing the now-unreachable dialog also removes the blank Gumroad popup.
    document = re.sub(r'<dialog\b[^>]*\bid="newsletter-dialog"[^>]*>.*?</dialog>',
                      '', document, count=1, flags=re.S | re.I)
    return document


def _remove_gumroad_catalog_loader(document):
    """Only Gumroad uses build-time cards; remove the obsolete async error UI."""
    if "const catalog = document.createElement('script')" not in document:
        raise ValueError("Official shop loader changed; update mirrored loader stripping")
    document, count = re.subn(
        r'<script>\s*\(function\(\)\{\s*// On Gumroad the official product cards.*?</script>',
        '', document, count=1, flags=re.S
    )
    if count != 1 or "SHOP TEMPORARILY UNAVAILABLE" in document:
        raise ValueError("Obsolete script can still blank the Gumroad store")
    return document


def mirror_profile():
    source = (ROOT / "index.html").read_text(encoding="utf-8")
    out = _functional_newsletter(_store_navigation(_inline_assets(source)))
    # The page is a visual clone; this marker is a deployment assertion.
    out = out.replace("<body data-page=\"home\">",
                      '<body data-page="home" data-sl-mirror="official-home-v2">', 1)
    if 'data-sl-mirror="official-home-v2"' not in out or 'data-sl-mirror-css="style.css"' not in out:
        raise ValueError("Cannot mirror canonical homepage")
    return out

def mirror_product(p, cover_html, type_label, price_fallback, includes):
    out = (ROOT / "product.html").read_text(encoding="utf-8")
    out = _functional_newsletter(_store_navigation(_inline_assets(out, product=True)))
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
    # Keep Gumroad's required native action, but do not use it as the visible
    # Buy Now link. Gumroad's own click handler can open the product page again
    # instead of checkout (especially for pay-what-you-want products).
    old_buy = '<a id="product-buy" class="sl-buy-button" href="#" target="_blank" rel="noopener noreferrer">BUY NOW · SECURE CHECKOUT</a>'
    amount = p.get("price")
    if isinstance(amount, bool) or not isinstance(amount, (int, float)):
        amount = p.get("price_cents")
    zero_price = amount == 0 and not isinstance(amount, bool)
    buy_options = ' data-gumroad-price="0"' if zero_price else ""
    slug = p.get("permalink") or p.get("custom_permalink")
    native = '<a class="sl-gumroad-native-fallback" data-gumroad-action="buy"' + buy_options + ' style="display:none!important" aria-hidden="true" tabindex="-1">NATIVE CHECKOUT</a>'
    if isinstance(slug, str) and re.fullmatch(r"[A-Za-z0-9_-]+", slug):
        direct = "https://simonlibonstore.gumroad.com/l/" + slug
        direct += "?price=0&amp;wanted=true" if zero_price else "?wanted=true"
        visible = ('<a id="product-buy" class="sl-buy-button" href="' + direct +
                   '" target="_blank" rel="noopener noreferrer">BUY NOW · SECURE CHECKOUT</a>')
        once(old_buy, visible + native)
    else:
        # Native checkout fallback only when there is no validated permalink.
        once(old_buy, '<a id="product-buy" class="sl-buy-button" data-gumroad-action="buy"' + buy_options + '>BUY NOW · SECURE CHECKOUT</a>')
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


def _compatible_music_images(document):
    """Preserve logos but avoid SVG/large-image data URIs rejected by Gumroad."""
    png_names = iter(("qobuz", "yandex-music"))
    def replace_png(match):
        try:
            name = next(png_names)
        except StopIteration:
            raise ValueError("Unexpected number of embedded PNG logos") from None
        src = SITE + "assets/music-logos/" + name + ".png"
        return re.sub(r'src="data:image/png;base64,[^"]+"',
                      'src="' + src + '"', match.group(0), count=1)
    document, count = re.subn(r'<img\b[^>]*\bsrc="data:image/png;base64,[^"]+"[^>]*>',
                             replace_png, document)
    if count != 2:
        raise ValueError("Expected exactly two PNG logos from the official music page")
    def decode_svg(encoded):
        decoded = unquote(encoded).strip()
        if not decoded.startswith("<svg ") or not decoded.endswith("</svg>"):
            raise ValueError("Invalid official SVG logo")
        if "<script" in decoded.lower() or "onload=" in decoded.lower():
            raise ValueError("Unexpected script in logo")
        return decoded.replace("<svg ", '<svg class="sl-logo-inline" ', 1)
    def embedded_svg(match):
        return decode_svg(match.group(1))
    document = re.sub(r'<img\b[^>]*\bsrc="data:image/svg\+xml,([^"]+)"[^>]*>',
                      embedded_svg, document)
    # Some external SVGs have an inline fallback of the same icon; reuse it as
    # real inline SVG to avoid loading an unreviewable external SVG resource.
    def remote_svg(match):
        return decode_svg(match.group(1))
    document = re.sub(
        r'<img\b[^>]*\bsrc="https://[^"]+\.svg"[^>]*\bdata-fallback="data:image/svg\+xml,([^"]+)"[^>]*>',
        remote_svg, document)
    if "data:image/svg+xml" in document or "data:image/png;base64" in document:
        raise ValueError("Embedded image URL remains in mirrored music page")
    document = document.replace(
        "</head>",
        '<style>.music-service-mark svg.sl-logo-inline{width:42px;height:42px;position:absolute;inset:3px;'
        'background:#fdfcfb;object-fit:contain}</style></head>', 1)
    return document

# Standalone pages use exactly the official DOM and the same shared styles.
PAGE_SOURCES = {
    "music": "music.html",
    "concerts": "concerts.html",
    "tabs": "tabs.html",
    "merch": "merch.html",
    "press": "press.html",
    "privacy": "privacy.html",
}

def mirror_standalone(slug):
    if slug not in PAGE_SOURCES:
        raise ValueError("Unknown Simon Libon page")
    source = (ROOT / PAGE_SOURCES[slug]).read_text(encoding="utf-8")
    out = _functional_newsletter(_store_navigation(_inline_assets(source)))
    if slug == "tabs":
        out = _remove_gumroad_catalog_loader(out)
    if slug == "tabs":
        # Two separate direct-buy links can wrap naturally on small phones.
        out = out.replace("</head>", '<style>body[data-page="tabs"] .shop-item-actions{flex-wrap:wrap;row-gap:10px}'
                          'body[data-page="tabs"] .shop-item-actions [aria-disabled="true"]{'
                          'pointer-events:none;opacity:.55}</style></head>', 1)
    if slug == "music":
        out = _compatible_music_images(out)
    # The catalogue and schedule scripts fetch public data from the official
    # host, never from Gumroad's unrelated /catalog.js path.
    for filename in ("catalog.js", "shop-model.js", "shop.js",
                     "concerts-data.json", "releases.json"):
        out = out.replace("'" + filename + "?", "'" + SITE + filename + "?")
        out = out.replace('"' + filename + '?', '"' + SITE + filename + '?')
        out = out.replace("'" + filename + "'", "'" + SITE + filename + "'")
        out = out.replace('"' + filename + '"', '"' + SITE + filename + '"')
    out = out.replace("<body ", '<body data-sl-mirror="official-page-' + slug + '" ', 1)
    if slug == "tabs":
        # Essential product cards must be server-rendered into Gumroad's HTML.
        # Remote scripts may be blocked, and should never make the shop empty.
        out = render_shop(out, load_catalog())
    if ('data-sl-mirror="official-page-' + slug + '"') not in out:
        raise ValueError("Cannot mirror the " + slug + " page")
    if 'data-sl-mirror-css="style.css"' not in out:
        raise ValueError("No canonical stylesheet for " + slug)
    return out
