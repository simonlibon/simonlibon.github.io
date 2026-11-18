"""Synchronize published Gumroad products without losing existing listings.

Never put GUMROAD_ACCESS_TOKEN in public site JavaScript or the repository.
The API may return incomplete product lists, so unknown existing products are
preserved rather than deleted.
"""
import datetime
import hashlib
import json
import os
import re
from html import unescape
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent.parent
CATALOG = ROOT / "catalog.js"
PAGE = ROOT / "tabs.html"
BASE = "https://api.gumroad.com/v2/products"
STORE = "simonlibonstore.gumroad.com"


def fetch_products():
    token = os.getenv("GUMROAD_ACCESS_TOKEN", "").strip()
    if not token:
        raise RuntimeError("Missing GUMROAD_ACCESS_TOKEN in GitHub repository secrets")
    request = Request(BASE, headers={
        "Authorization": "Bearer " + token,
        "Accept": "application/json",
        "User-Agent": "SimonLibonCatalogueSync/1.0",
    })
    with urlopen(request, timeout=30) as response:
        data = json.load(response)
    if data.get("success") is not True or not isinstance(data.get("products"), list):
        raise RuntimeError("Invalid Gumroad products response; existing catalogue unchanged")
    return data["products"]


def get_slug(product):
    custom = str(product.get("custom_permalink") or "").strip()
    if re.fullmatch(r"[A-Za-z0-9_-]+", custom):
        return custom
    for key in ("short_url", "url", "permalink"):
        url = product.get(key)
        if not isinstance(url, str):
            continue
        parsed = urlparse(url)
        host = (parsed.hostname or "").lower()
        if parsed.scheme != "https" or (host != "gumroad.com" and not host.endswith(".gumroad.com")):
            continue
        match = re.fullmatch(r"/l/([A-Za-z0-9_-]+)/?", parsed.path)
        if match:
            return match.group(1)
    return None


def product_type(name):
    name = name.lower()
    if "bundle" in name or re.search(r"\bep\b", name) or ("tab" in name and "backing" in name):
        return "bundle"
    if "backing" in name:
        return "backing"
    if "tab" in name or "tablature" in name:
        return "tabs"
    return None


def text_description(value, name):
    value = unescape(re.sub(r"<[^>]+>", " ", str(value or "")))
    value = re.sub(r"\s+", " ", value).strip()
    if not value or "[SONG TITLE]" in value:
        return "Official guitar tab or backing track for " + name + " by Simon Libon."
    return value[:400]


def get_image(item):
    options = [item.get("thumbnail_url"), item.get("preview_url"), item.get("cover_image_url")]
    covers = item.get("covers") or item.get("cover_images")
    if isinstance(covers, list):
        options.extend(x.get("url") if isinstance(x, dict) else x for x in covers)
    return next((x for x in options if isinstance(x, str) and x.startswith("https://")), "")


def load_catalogue():
    source = CATALOG.read_text(encoding="utf-8")
    match = re.search(r"window\.SIMON_SHOP_CATALOG\s*=\s*(\{[\s\S]*\});?\s*$", source)
    if not match:
        raise RuntimeError("Unrecognized catalogue format; refusing to overwrite")
    catalogue = json.loads(match.group(1))
    if not isinstance(catalogue.get("products"), list):
        raise RuntimeError("Missing existing catalogue products; refusing to overwrite")
    return catalogue, source


def main():
    catalogue, original = load_catalogue()
    api_products = fetch_products()
    if not api_products:
        raise RuntimeError("Empty Gumroad response; leaving existing catalogue untouched")

    old = catalogue["products"]
    by_slug = {}
    for entry in old:
        if not isinstance(entry, dict):
            continue
        url = urlparse(str(entry.get("gumroadUrl") or ""))
        match = re.fullmatch(r"/l/([A-Za-z0-9_-]+)/?", url.path)
        slug = match.group(1) if match else entry.get("id")
        if slug:
            by_slug[slug] = entry

    added = []
    for item in api_products:
        if not isinstance(item, dict) or item.get("deleted") is True:
            continue
        slug = get_slug(item)
        name = str(item.get("name") or "").strip()
        category = product_type(name)
        if not slug or not category:
            continue
        existing = by_slug.get(slug)
        if item.get("published") is not True:
            if existing:
                existing["published"] = False
            continue

        price_cents = item.get("price")
        if price_cents is None:
            price_cents = item.get("price_cents")
        try:
            price = max(int(price_cents), 0) / 100
        except (TypeError, ValueError):
            continue
        patch = {
            "id": slug,
            "title": name,
            "type": category,
            "price": price,
            "gumroadUrl": f"https://{STORE}/l/{slug}",
            "published": True,
        }
        image = get_image(item)
        if image:
            patch["image"] = image
        if existing:
            existing.update(patch)
        else:
            date = str(item.get("created_at") or "")[:10]
            if not re.fullmatch(r"\d{4}-\d\d-\d\d", date):
                date = datetime.datetime.now(datetime.timezone.utc).date().isoformat()
            new = {
                **patch,
                "description": text_description(item.get("description"), name),
                "includes": [],
                "image": image,
                "releaseDate": date,
            }
            added.append(new)
            by_slug[slug] = new

    catalogue["products"] = added + old
    updated = "window.SIMON_SHOP_CATALOG = " + json.dumps(catalogue, ensure_ascii=False, indent=2) + ";\n"
    if updated == original:
        print("Catalogue unchanged")
        return

    # Validate the page's catalogue script tag before changing either file.
    page = PAGE.read_text(encoding="utf-8")
    version = hashlib.sha256(updated.encode("utf-8")).hexdigest()[:8]
    page_new, count = re.subn(r"catalog\.js\?v=[A-Za-z0-9_-]+", f"catalog.js?v={version}", page)
    if count != 1:
        raise RuntimeError("Cannot update unique catalogue link; catalogue left untouched")
    CATALOG.write_text(updated, encoding="utf-8")
    PAGE.write_text(page_new, encoding="utf-8")
    print(f"Updated catalogue; added {len(added)} new products. Existing listings preserved.")


if __name__ == "__main__":
    main()
