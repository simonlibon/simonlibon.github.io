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



def stamp_mirror_revision(document):
    """Stamp the generated route with an invisible hash of its canonical HTML/CSS."""
    import hashlib
    source_sha = hashlib.sha256(document.encode("utf-8")).hexdigest()[:20]
    document, count = re.subn(
        r"<main\b", '<main data-sl-mirror-sha="' + source_sha + '"',
        document, count=1, flags=re.I
    )
    if count != 1:
        raise ValueError("Cannot find a single main region for Gumroad revision")
    return document

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
    return stamp_mirror_revision(out)

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
    if count not in (0, 2):
        raise ValueError("Unexpected embedded PNG logos in canonical music page")
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
        '<style>.music-card-icon svg.sl-logo-inline{display:block;width:48px;height:48px;max-width:100%;max-height:100%;object-fit:contain}'
        '.music-card[data-platform="Amazon Music"] .music-card-icon svg.sl-logo-inline{width:62px;max-width:88px}'
        '@media(max-width:650px){.music-card-icon svg.sl-logo-inline{width:41px;height:41px}}</style></head>', 1)
    return document


def _static_music_profiles(document):
    """Make verified artist links work on Gumroad without relying on JavaScript.

    Gumroad may strip inline scripts, so the music cards must be functional
    in the delivered HTML. The canonical site uses the same configuration.
    """
    import json
    from urllib.parse import urlparse
    profiles = json.loads((ROOT / "streaming-profiles.json").read_text(encoding="utf-8")).get("profiles", {})
    allowed = {
        "Spotify": ("open.spotify.com",),
        "Apple Music": ("music.apple.com",),
        "YouTube Music": ("music.youtube.com",),
        "Deezer": ("www.deezer.com", "deezer.com"),
        "Amazon Music": ("music.amazon.com",),
        "YouTube": ("www.youtube.com", "youtube.com"),
        "TIDAL": ("tidal.com", "listen.tidal.com"),
        "Qobuz": ("qobuz.com", "www.qobuz.com"),
        "SoundCloud": ("soundcloud.com", "www.soundcloud.com"),
        "Bandcamp": ("bandcamp.com", "www.bandcamp.com"),
        "Audiomack": ("audiomack.com", "www.audiomack.com"),
        "Napster": ("napster.com", "www.napster.com"),
        "Anghami": ("anghami.com", "www.anghami.com"),
        "Pandora": ("pandora.com", "www.pandora.com"),
        "iHeartRadio": ("iheart.com", "www.iheart.com"),
        "JioSaavn": ("jiosaavn.com", "www.jiosaavn.com"),
        "KKBOX": ("kkbox.com", "www.kkbox.com"),
        "Gaana": ("gaana.com", "www.gaana.com"),
        "Mixcloud": ("mixcloud.com", "www.mixcloud.com"),
        "Audius": ("audius.co",),
        "NetEase Cloud Music": ("music.163.com",),
        "Yandex Music": ("music.yandex.com",),
        "LINE MUSIC": ("music.line.me",),
    }
    for name, candidate in profiles.items():
        if name not in allowed or not isinstance(candidate, str):
            continue
        url = urlparse(candidate)
        if url.scheme != "https" or url.hostname not in allowed[name] or not url.path.strip("/") or url.username or url.password:
            continue
        # Only rewrite exact disabled cards. Do not replace other navigation links.
        pattern = (r'<div class="music-card(?P<extra> music-extra-card)?" data-platform="' +
                   re.escape(html.escape(name, quote=True)) +
                   r'" aria-disabled="true">(?P<body>.*?)</div>')
        def activate(match):
            body = match.group("body").replace("COMING SOON", "OPEN PROFILE")
            classes = "music-card" + (match.group("extra") or "") + " is-ready"
            return ('<a class="' + classes + '" data-platform="' + html.escape(name, quote=True) +
                    '" href="' + html.escape(candidate, quote=True) +
                    '" rel="noopener noreferrer">' + body + '</a>')
        document = re.sub(pattern, activate, document, count=1, flags=re.S)
    # On Gumroad, do not depend on scripts or remote JSON for these links.
    document = re.sub(r'<script id="music-profile-links">.*?</script>', '',
                      document, flags=re.S)
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
        out = _static_music_profiles(out)
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
    return stamp_mirror_revision(out)
