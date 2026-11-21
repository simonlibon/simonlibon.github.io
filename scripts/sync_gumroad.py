"""Synchronise les produits publiés Gumroad vers la boutique GitHub Pages.

Ne modifie jamais les produits Gumroad. Le jeton reste dans un secret GitHub
et n'est jamais écrit dans un fichier public.
"""
import datetime as dt
import json
import os
import re
import time
from html import unescape
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
CATALOG = ROOT / "catalog.js"
API = "https://api.gumroad.com/v2"
STORE = "simonlibonstore.gumroad.com"
EXCLUDED_PRODUCT_IDS = {"OVXljMxC50PnMR5NFLXYkg=="}  # Ancien produit Test explicitement exclu.


def api_get(endpoint, token, params=None):
    url = API + endpoint
    if params:
        url += "?" + urlencode(params)
    request = Request(url, headers={
        "Authorization": "Bearer " + token,
        "Accept": "application/json",
        "User-Agent": "SimonLibonCatalogueSync/2.0",
    })
    for attempt in range(4):
        try:
            with urlopen(request, timeout=25) as response:
                payload = json.load(response)
            if not isinstance(payload, dict) or payload.get("success") is not True:
                raise RuntimeError("Gumroad returned an unsuccessful or invalid API response")
            return payload
        except HTTPError as error:
            if error.code != 429 or attempt == 3:
                raise RuntimeError(f"Gumroad API HTTP {error.code}") from error
            time.sleep(2 ** attempt)
    raise RuntimeError("Gumroad API retry limit reached")


def fetch_products(token):
    products, seen_pages = [], set()
    page_key = None
    for _ in range(100):
        params = {"page_key": page_key} if page_key else None
        response = api_get("/products", token, params)
        batch = response.get("products")
        if not isinstance(batch, list):
            raise RuntimeError("Gumroad products list incomplete: missing products array")
        products.extend(batch)
        next_key = response.get("next_page_key")
        if not next_key:
            if response.get("has_more") is True or response.get("next_page_url"):
                raise RuntimeError("Gumroad pagination format unexpected; refusing partial sync")
            return products
        if not isinstance(next_key, str) or next_key in seen_pages:
            raise RuntimeError("Gumroad pagination loop or invalid key")
        seen_pages.add(next_key)
        page_key = next_key
    raise RuntimeError("Too many Gumroad pages; refusing incomplete sync")


def slug_of(item):
    for key in ("custom_permalink", "permalink"):
        value = item.get(key)
        if isinstance(value, str) and re.fullmatch(r"[A-Za-z0-9_-]+", value.strip()):
            return value.strip()
    for key in ("url", "short_url", "product_permalink"):
        value = item.get(key)
        if not isinstance(value, str):
            continue
        parsed = urlparse(value)
        if parsed.scheme != "https" or parsed.hostname not in (
            "gumroad.com", "www.gumroad.com", STORE
        ):
            continue
        match = re.fullmatch(r"/l/([A-Za-z0-9_-]+)/?", parsed.path)
        if match:
            return match.group(1)
    return None


def kind_of(item, old=None):
    name = str(item.get("name", "")).lower()
    has_tabs = bool(re.search(r"\b(tabs?|tablatures?)\b", name))
    has_backing = bool(re.search(r"\bbacking\b", name))
    # An EP/album is one bundle. A single song sold with both files is a pack.
    if re.search(r"\b(ep|album)\b", name):
        return "bundle"
    if has_tabs and has_backing:
        return "pack"
    if "bundle" in name:
        return "bundle"
    if has_backing:
        return "backing"
    if has_tabs:
        return "tabs"
    return (old or {}).get("type") or "digital"


def description_of(item, kind, old):
    raw = str(item.get("description") or "")
    plain = unescape(re.sub(r"<br\s*/?>|</p>|</li>", "\n", raw, flags=re.I))
    plain = re.sub(r"<[^>]*>", " ", plain)
    plain = re.sub(r"[ \t]+", " ", plain)
    plain = re.sub(r"\n\s*\n+", "\n", plain).strip()
    if "[SONG TITLE]" in plain.upper() or not plain:
        existing = str((old or {}).get("description") or "")
        if existing and "[SONG TITLE]" not in existing.upper():
            return existing
        name = str(item.get("name", "")).strip()
        if kind == "backing":
            return f"Official backing track without lead guitar for {name}. Digital audio download."
        if kind == "tabs":
            return f"Official guitar tablature for {name}. PDF digital download."
        return f"Official digital release: {name}."
    return plain[:1000]


def image_of(item, old):
    covers = item.get("covers") or item.get("cover_images")
    choices = []
    if isinstance(covers, list):
        choices += [c.get("url") if isinstance(c, dict) else c for c in covers]
    choices += [item.get(key) for key in (
        "cover_image_url", "thumbnail_url", "preview_url", "image_url"
    )]
    choices += [(old or {}).get("image")]
    for candidate in choices:
        if isinstance(candidate, str) and urlparse(candidate).scheme == "https":
            return candidate
    return ""


def read_catalogue():
    source = CATALOG.read_text(encoding="utf-8")
    match = re.fullmatch(
        r"\s*(?://[^\n]*\n\s*)*window\.SIMON_SHOP_CATALOG\s*=\s*(\{[\s\S]*\})\s*;\s*", source
    )
    if not match:
        raise RuntimeError("Unknown catalog.js format; refusing to overwrite")
    catalog = json.loads(match.group(1))
    if not isinstance(catalog, dict) or not isinstance(catalog.get("products"), list):
        raise RuntimeError("Malformed catalog.js; refusing to overwrite")
    return catalog, source


def main():
    token = os.environ.get("GUMROAD_ACCESS_TOKEN", "").strip()
    if not token:
        raise RuntimeError("Missing repository secret GUMROAD_ACCESS_TOKEN")
    catalog, original = read_catalogue()
    listing = fetch_products(token)
    if not listing:
        raise RuntimeError("Empty Gumroad inventory; refusing to clear catalogue")

    old = catalog["products"]
    by_id = {p.get("id"): p for p in old if isinstance(p, dict)}
    drafts = [p for p in old if isinstance(p, dict) and p.get("demo") is True]
    published = []
    seen_ids = set()
    today = dt.datetime.now(ZoneInfo("Europe/Brussels")).date().isoformat()

    for summary in listing:
        if not isinstance(summary, dict) or not isinstance(summary.get("id"), str):
            raise RuntimeError("Gumroad inventory returned malformed product")
        product_id = summary["id"]
        if product_id in seen_ids:
            raise RuntimeError("Gumroad inventory contains duplicate product IDs")
        seen_ids.add(product_id)
        if product_id in EXCLUDED_PRODUCT_IDS or summary.get("deleted") is True:
            continue
        if not isinstance(summary.get("published"), bool):
            raise RuntimeError("Gumroad product has unknown published state")
        if not summary["published"] or summary.get("archived") is True:
            continue

        detail = api_get("/products/" + product_id, token).get("product")
        if not isinstance(detail, dict):
            raise RuntimeError("Gumroad product detail missing")
        product = dict(summary)
        product.update({k: v for k, v in detail.items() if v is not None})
        if product.get("published") is not True:
            raise RuntimeError("Gumroad product status changed during sync; retry later")

        slug = slug_of(product)
        if not slug:
            raise RuntimeError("Published Gumroad product has no valid URL slug")
        old_product = by_id.get(slug) or next(
            (p for p in old if isinstance(p, dict) and
             p.get("gumroadUrl") == f"https://{STORE}/l/{slug}"), None
        )
        name = str(product.get("name") or "").strip()
        currency = str(product.get("currency") or "").lower()
        raw_price = product.get("price_cents", product.get("price"))
        if not name or currency != "eur" or isinstance(raw_price, bool):
            raise RuntimeError("Published Gumroad product has missing name or EUR price")
        try:
            cents = int(raw_price)
        except (ValueError, TypeError) as error:
            raise RuntimeError("Published Gumroad product has invalid price") from error
        if cents < 0 or str(raw_price).strip() not in (str(cents),):
            raise RuntimeError("Published Gumroad product price has unexpected format")
        kind = kind_of(product, old_product)
        includes = {
            "tabs": ["Guitar tab (PDF)"],
            "backing": ["Backing track (audio)"],
            "pack": ["Guitar tab (PDF)", "Backing track (audio)"],
            "bundle": ["Tabs and backing tracks"],
        }.get(kind, ["Digital download"])
        # Known synthetic checkout tests use WAV, not an unspecified audio file.
        # Keep this exact description through every hourly Gumroad sync.
        if slug == "mmxjjd" and kind == "pack":
            includes = ["Guitar tab (PDF)", "Backing track (WAV)"]
        published.append({
            "id": slug,
            "title": name,
            "type": kind,
            "description": description_of(product, kind, old_product),
            "includes": includes,
            "price": cents / 100,
            "gumroadUrl": f"https://{STORE}/l/{slug}",
            "image": image_of(product, old_product),
            "published": True,
            "releaseDate": (old_product or {}).get("releaseDate") or today,
        })

    if len({p["id"] for p in published}) != len(published):
        raise RuntimeError("Duplicate Gumroad permalinks; refusing to overwrite")
    old_ids = {p.get("id") for p in old if isinstance(p, dict) and not p.get("demo")}
    new_ids = {p["id"] for p in published}
    catalog["products"] = published + drafts
    updated = "window.SIMON_SHOP_CATALOG = " + json.dumps(
        catalog, ensure_ascii=False, indent=2
    ) + ";\n"
    if updated == original:
        print("Gumroad catalogue unchanged")
        return
    CATALOG.write_text(updated, encoding="utf-8")
    print(
        f"Gumroad catalogue synchronised: {len(new_ids - old_ids)} added, "
        f"{len(old_ids - new_ids)} removed; {len(published)} published total."
    )


if __name__ == "__main__":
    main()
