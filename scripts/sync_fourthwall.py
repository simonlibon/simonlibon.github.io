"""Sync Fourthwall's current public product catalog to GitHub Pages (no token in public files)."""
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
import uuid
from datetime import datetime, timezone
from html import unescape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "fourthwall-products.json"
SHOP = "https://simon-libon-music-shop.fourthwall.com"
ENDPOINT = "https://storefront-api.fourthwall.com/v1/collections/all/products"
TOKEN = os.environ.get("FOURTHWALL_STOREFRONT_TOKEN", "").strip()
if not TOKEN:
    raise SystemExit("Missing FOURTHWALL_STOREFRONT_TOKEN GitHub Actions secret")

def fetch(page):
    query = urllib.parse.urlencode({
        "storefront_token": TOKEN, "page": page, "size": 50
    })
    req = urllib.request.Request(ENDPOINT + "?" + query, headers={
        "Accept": "application/json",
        "User-Agent": "SimonLibonCatalogSync/2.0"
    })
    try:
        with urllib.request.urlopen(req, timeout=25) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        raise SystemExit("Fourthwall API error HTTP " + str(error.code)) from None
    except urllib.error.URLError:
        raise SystemExit("Fourthwall API not reachable") from None

raw = []
for page in range(100):
    data = fetch(page)
    if not isinstance(data, dict) or not isinstance(data.get("results"), list):
        raise SystemExit("Unexpected Fourthwall catalog response")
    raw.extend(data["results"])
    paging = data.get("paging") or {}
    if not paging.get("hasNextPage", False):
        break
else:
    raise SystemExit("Fourthwall pagination exceeds 100 pages")

products = []
print("Fourthwall API returned", len(raw), "entries before filtering.")
for p in raw:
    if not isinstance(p, dict) or not p.get("slug"):
        print("Skipped entry: missing product slug")
        continue
    state = p.get("state") or {}
    access = p.get("access") or {}
    if state.get("type") != "AVAILABLE":
        print("Skipped product", p.get("name", p.get("slug")), "state:", state.get("type"))
        continue
    if access and access.get("type") != "PUBLIC":
        print("Skipped product", p.get("name", p.get("slug")), "access:", access.get("type"))
        continue
    slug = str(p["slug"])
    variants = p.get("variants") if isinstance(p.get("variants"), list) else []
    product_type = str(p.get("type") or "PRODUCT")
    price = (p.get("price") if product_type == "BUNDLE" else
             variants[0].get("unitPrice") if variants and isinstance(variants[0], dict) else None) or {}
    variant_id = None
    if len(variants) == 1 and isinstance(variants[0], dict):
        candidate = variants[0].get("id")
        try:
            variant_id = str(uuid.UUID(candidate))
        except (TypeError, ValueError, AttributeError):
            pass
    imgs = p.get("images") or []
    image = imgs[0] if imgs and isinstance(imgs[0], dict) else {}
    text = p.get("description") or ""
    text = unescape(re.sub(r"<[^>]+>", " ", text)) if isinstance(text, str) else ""
    text = re.sub(r"\s+", " ", text).strip()[:1000]
    image_url = image.get("url") or image.get("src") or ""
    if not isinstance(image_url, str) or not image_url.startswith("https://"):
        image_url = ""
    print("Included product:", p.get("name", slug), "type:", product_type)
    products.append({
        "id": str(p.get("id") or slug),
        "name": str(p.get("name") or slug),
        "description": text,
        "image": image_url,
        "url": SHOP + "/products/" + urllib.parse.quote(slug, safe=""),
        "price": price.get("value") if isinstance(price.get("value"), (int, float)) else None,
        "currency": price.get("currency") or "EUR",
        "productType": product_type,
        "variantId": variant_id,
        "variantCount": len(variants),
        "createdAt": p.get("createdAt") or "",
        "available": True
    })

previous = {}
if DEST.exists():
    try:
        previous = json.loads(DEST.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        pass
now = datetime.now(timezone.utc)
old_date = previous.get("syncedAt") if isinstance(previous, dict) else None
try:
    last_check = datetime.fromisoformat(old_date.replace("Z", "+00:00"))
    age = (now - last_check).total_seconds()
except (ValueError, AttributeError, TypeError):
    age = float("inf")

# Save immediately after any product change; otherwise refresh freshness marker hourly.
if previous.get("products") != products or age >= 3600:
    DEST.write_text(json.dumps({
        "syncedAt": now.isoformat(), "products": products
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("Fourthwall public catalog verified:", len(products), "products.")
