#!/usr/bin/env python3
"""Safely preview/publish the official visual theme on Gumroad product pages.

Only the product's custom_html field is changed. Prices, descriptions, downloads,
publication state, and checkout settings remain Gumroad-managed. Never overwrite
an unrelated pre-existing custom product landing page.
"""
import argparse
import html
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
if __package__:
    from .mirror_gumroad import mirror_product
else:
    from mirror_gumroad import mirror_product

API = "https://api.gumroad.com/v2/"
MARKER = 'data-sl-product-template="v2"'
OWN_MARKERS = (MARKER, 'data-sl-product-template="v1"')
TEMPLATE = Path(__file__).with_name("gumroad-product-template.html")
FALLBACK_COVERS = {
    "zvxja": "https://public-files.gumroad.com/w3h3lhnhymirnqdzb1xls0h7nb28",
}


def request(token, route, method="GET", values=None):
    payload = {"access_token": token}
    payload.update(values or {})
    if method == "GET":
        uri = API + route + "?" + urllib.parse.urlencode(payload)
        req = urllib.request.Request(uri, method="GET")
    else:
        data = urllib.parse.urlencode(payload).encode("utf-8")
        req = urllib.request.Request(API + route, data=data, method=method)
    try:
        with urllib.request.urlopen(req, timeout=40) as resp:
            result = json.load(resp)
    except urllib.error.HTTPError as err:
        message = err.read().decode("utf-8", "replace")
        raise RuntimeError(f"Gumroad HTTP {err.code} at {route}: {message[:800]}") from None
    if result.get("success") is False:
        raise RuntimeError(f"Gumroad rejected {route}: {result.get('message','unknown error')}")
    return result


def published_products(token):
    all_products = []
    page = None
    seen = set()
    for _ in range(30):
        params = {"page_key": page} if page else {}
        data = request(token, "products", values=params)
        entries = data.get("products") or []
        all_products += [p for p in entries if p.get("published") is True]
        page = data.get("next_page_key") or data.get("page_key")
        if not page or page in seen or not entries:
            break
        seen.add(page)
    return all_products


def cover_url(p, permalink):
    candidates = p.get("covers") or p.get("cover_images") or []
    if isinstance(candidates, list):
        for entry in candidates:
            url = entry.get("url") if isinstance(entry, dict) else entry
            if isinstance(url, str) and url.startswith("https://"):
                return url
    for key in ("thumbnail_url", "cover_image_url", "cover_url"):
        url = p.get(key)
        if isinstance(url, str) and url.startswith("https://"):
            return url
    return FALLBACK_COVERS.get(permalink)


def product_type(p):
    name = (p.get("name") or "").lower()
    if p.get("is_bundle") or "bundle" in name:
        return "EP / ALBUM BUNDLE"
    if "backing" in name or "track" in name:
        return "BACKING TRACK"
    return "GUITAR TAB"



def tab_format(name):
    """A tab and the corresponding tab+track share one canonical song title."""
    if not isinstance(name, str) or re.search(r"\b(ep|album|bundle)\b", name, flags=re.I):
        return None
    suffix = re.search(
        r"\s*[-—–:]\s*(?:guitar\s+)?tabs?"
        r"(?:\s*(?:\+|&|and)\s*backing\s+tracks?)?\s*$",
        name, flags=re.I,
    )
    if not suffix:
        return None
    title = name[:suffix.start()].strip().casefold()
    if not title:
        return None
    kind = "pack" if re.search(r"\bbacking\s+tracks?\b", suffix.group(), re.I) else "tabs"
    return title, kind


def options_html(current, catalog):
    """Match only verified published sibling products; never synthesize checkout."""
    own = tab_format(current.get("name"))
    if own is None:
        return ""
    candidates = {}
    for row in catalog:
        if not isinstance(row, dict) or row.get("published") is not True:
            continue
        match = tab_format(row.get("name"))
        if match is None or match[0] != own[0] or match[1] in candidates:
            continue
        code = row.get("permalink") or row.get("custom_permalink")
        if not isinstance(code, str) or not re.fullmatch(r"[a-zA-Z0-9_-]+", code):
            url = str(row.get("url") or row.get("short_url") or "")
            parsed = urllib.parse.urlparse(url)
            parts = parsed.path.split("/")
            if parsed.scheme != "https" or parsed.netloc != "simonlibonstore.gumroad.com" or len(parts) < 3 or parts[1] != "l":
                continue
            code = parts[2]
        if not re.fullmatch(r"[a-zA-Z0-9_-]+", code):
            continue
        cents = row.get("price_cents", row.get("price"))
        if isinstance(cents, bool) or not isinstance(cents, (int, float)) or cents < 0:
            continue
        candidates[match[1]] = {
            "code": code,
            "price": f"€{cents / 100:.2f}",
        }
    if not all(kind in candidates for kind in ("tabs", "pack")):
        return ""
    own_id = current.get("permalink") or current.get("custom_permalink")
    if not own_id:
        own_id = next((x["code"] for k,x in candidates.items() if k == own[1]), "")
    labels = {"tabs": "Guitar Tab (PDF)", "pack": "Tab + Backing Track"}
    fields = ['<fieldset class="shop-purchase-options"><legend>CHOOSE YOUR DOWNLOAD</legend>']
    for kind in ("tabs", "pack"):
        option = candidates[kind]
        selected = own[1] == kind and option["code"] == own_id
        tag = "span" if selected else "a"
        cls = "shop-option selected" if selected else "shop-option"
        href = "" if selected else ' href="https://simonlibonstore.gumroad.com/l/' + option["code"] + '"'
        fields.append(
            f'<{tag} class="{cls}"{href}>'
            f'<span class="shop-option-name">{html.escape(labels[kind])}</span>'
            f'<strong class="shop-option-price">{option["price"]}</strong>'
            f'</{tag}>'
        )
    fields.append("</fieldset>")
    return "".join(fields)


def build(p, catalog=None):
    permalink = p.get("permalink") or p.get("custom_permalink") or ""
    name = p.get("name") or "Digital product"
    url = cover_url(p, permalink)
    if url:
        cover = f'<img alt="Cover art for {html.escape(name, quote=True)}" src="{html.escape(url, quote=True)}" loading="eager">'
    else:
        cover = '<div class="cover-fallback">SIMON LIBON</div>'
    amount = p.get("price")
    fallback = p.get("formatted_price") or p.get("price_formatted") or "VIEW PRICE AT CHECKOUT"
    if isinstance(amount, (float, int)) and not p.get("formatted_price"):
        fallback = f"€{amount / 100:,.2f}" if p.get("price_currency_type") == "eur" else "VIEW PRICE AT CHECKOUT"
    name_lower = str(name).lower()
    if "ep" in name_lower or "album" in name_lower or "bundle" in name_lower:
        includes = ["Official tablatures (PDF)", "Backing tracks (audio)", "Digital download"]
        label = "EP COLLECTION"
    elif "tab" in name_lower and "backing" in name_lower:
        includes = ["Guitar tab (PDF)", "Backing track without lead guitar", "Digital download"]
        label = "INDIVIDUAL TRACK"
    else:
        includes = ["Guitar tab (PDF)", "Digital download"]
        label = "INDIVIDUAL TRACK"
    result = mirror_product(p, cover, label, fallback, includes)
    options = options_html(p, catalog or [])
    if options:
        anchor = '<a id="product-buy" class="sl-buy-button" data-gumroad-action="buy">'
        if result.count(anchor) != 1:
            raise ValueError("Missing Gumroad buy button for format selector")
        result = result.replace(anchor, options + anchor, 1)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--publish", action="store_true", help="Publish validated pages; otherwise preview only")
    args = parser.parse_args()
    token = os.environ.get("GUMROAD_ACCESS_TOKEN", "").strip()
    if not token:
        raise SystemExit("Missing GUMROAD_ACCESS_TOKEN; no pages touched")
    pages = published_products(token)
    print("Published Gumroad products:", len(pages))
    for entry in pages:
        identifier = entry.get("id")
        if not identifier:
            print("Skipping product without an ID")
            continue
        key = urllib.parse.quote(str(identifier), safe="")
        product = request(token, "products/" + key).get("product") or {}
        permalink = product.get("custom_permalink") or product.get("permalink") or entry.get("custom_permalink") or entry.get("permalink")
        if not permalink:
            for url in (product.get("short_url"), product.get("url"), entry.get("short_url"), entry.get("url")):
                if isinstance(url, str) and "/l/" in url:
                    permalink = urllib.parse.urlsplit(url).path.rsplit("/l/", 1)[-1].split("/")[0]
                    if permalink:
                        break
        if not permalink:
            print("WARNING: product permalink could not be identified; skipping to protect cover art")
            continue
        name = product.get("name") or entry.get("name")
        old = request(token, "products/" + key + "/custom_html").get("custom_html") or ""
        if old and not any(marker in old for marker in OWN_MARKERS):
            # The DEMO EP page predates our marker. It is an explicit test fixture
            # that the creator asked to harmonize, not an unrelated custom page.
            known_demo_bundle = (permalink == "jghmyd" and str(name).startswith("DEMO EP"))
            if not known_demo_bundle:
                print(f"SKIP {permalink}: independently customized page; no changes")
                continue
            print("Replacing the known legacy DEMO EP page with the canonical layout.")
        if not product.get("permalink") and not product.get("custom_permalink"):
            product["permalink"] = permalink
        new_page = build(product, pages)
        if permalink in FALLBACK_COVERS and "<img " not in new_page:
            raise RuntimeError("Expected an image cover for the known test product")
        print(f"COVER CHECK {permalink}: image={'<img ' in new_page}")
        if len(new_page) > 150000:
            raise RuntimeError("Product HTML unexpectedly large")
        preview = request(token, "products/" + key + "/preview_custom_html", "POST", {"custom_html": new_page})
        sanitized = preview.get("custom_html") or ""
        needed = [MARKER, 'data-gumroad-action="buy"', 'data-gumroad-field="name"',
                  'data-gumroad-field="price"', 'data-gumroad-field="description"', "site-head"]
        missing = [x for x in needed if x not in sanitized]
        if missing or preview.get("warning"):
            raise RuntimeError(f"Preview rejected {permalink}, missing={missing}, warning={preview.get('warning')}")
        removed = (preview.get("sanitization_report") or {}).get("total_removed")
        print(f"PREVIEW OK {permalink} ({name!r}); HTML={len(sanitized)}, sanitizer removals={removed}")
        if old == sanitized:
            print(f"UNCHANGED {permalink}")
            continue
        if not args.publish:
            print(f"PREVIEW ONLY {permalink}; no publish")
            continue
        put = request(token, "products/" + key, "PUT", {"custom_html": new_page})
        if not put.get("success"):
            raise RuntimeError("Gumroad did not confirm product update")
        live = request(token, "products/" + key + "/custom_html")
        live_html = live.get("custom_html") or ""
        if MARKER not in live_html or 'data-gumroad-action="buy"' not in live_html:
            raise RuntimeError("Product custom page could not be verified after update")
        print(f"PUBLISHED {permalink} | {live.get('landing_url','')}")

if __name__ == "__main__":
    main()
