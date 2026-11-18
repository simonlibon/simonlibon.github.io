"""Synchronize Fourthwall product catalog and public Storefront API browser token."""
import json
import re
from datetime import datetime, timezone
from html import unescape
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOKEN = os.environ.get("FOURTHWALL_STOREFRONT_TOKEN", "").strip()
BASE = "https://storefront-api.fourthwall.com/v1/collections/all/products"
SHOP = "https://simon-libon-music-shop.fourthwall.com"
if not TOKEN:
    raise SystemExit("Fourthwall secret missing: check GitHub Actions repository secret FOURTHWALL_STOREFRONT_TOKEN")

def fetch(page):
    # The token is never printed, even if Fourthwall returns an error.
    params = urllib.parse.urlencode({"storefront_token": TOKEN, "page": page, "size": 50})
    request = urllib.request.Request(BASE + "?" + params, headers={
        "Accept": "application/json",
        "User-Agent": "SimonLibonCatalogSync/1.1",
    })
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        if exc.code in (401, 403):
            raise SystemExit(
                f"Fourthwall denied catalog access (HTTP {exc.code}). "
                "Confirm that the GitHub secret contains an active Storefront API token "
                "for this published Fourthwall shop. No token was printed."
            ) from None
        raise SystemExit(f"Fourthwall API request failed: HTTP {exc.code}. No token was printed.") from None
    except urllib.error.URLError as exc:
        raise SystemExit(f"Could not reach Fourthwall API: {exc.reason}") from None

products = []
for page in range(100):
    data = fetch(page)
    if not isinstance(data, dict) or not isinstance(data.get("results"), list):
        raise SystemExit("Unexpected Fourthwall response format: expected 'results' list.")
    products.extend(data["results"])
    if not data.get("paging", {}).get("hasNextPage", False):
        break
else:
    raise SystemExit("Fourthwall catalog pagination exceeded 100 pages.")

output = []
for product in products:
    if not isinstance(product, dict) or not product.get("slug"):
        continue
    slug = product["slug"]
    variants = product.get("variants") or []
    price = (product.get("price") if product.get("type") == "BUNDLE" else
             (variants[0].get("unitPrice") if variants else None)) or {}
    images = product.get("images") or []
    first_image = images[0] if images and isinstance(images[0], dict) else {}
    description = product.get("description") or ""
    if isinstance(description, str):
        description = unescape(re.sub(r"<[^>]*>", " ", description))
        description = re.sub(r"\s+", " ", description).strip()[:1800]
    else:
        description = ""
    product_type = product.get("type") or "PRODUCT"
    variant_id = variants[0].get("id") if product_type == "PRODUCT" and len(variants) == 1 else None
    is_available = (product.get("state") or {}).get("type") == "AVAILABLE"
    # Do not surface draft, hidden, or unavailable products as public releases.
    if not is_available:
        continue

    image = first_image.get("url") or first_image.get("src") or ""
    output.append({
        "id": str(product.get("id", slug)),
        "name": product.get("name") or slug,
        "description": description,
        "slug": slug,
        "url": SHOP + "/products/" + urllib.parse.quote(slug, safe=""),
        "image": image,
        "price": price.get("value"),
        "currency": price.get("currency") or "EUR",
        "createdAt": product.get("createdAt") or "",
        "productType": product_type,
        "variantId": variant_id,
        "variantCount": len(variants),
        "available": is_available,
    })

# A verified empty API result is meaningful: all products may have been unpublished.
# Never preserve an old product list merely because no products remain.
target = ROOT / "fourthwall-products.json"
content = json.dumps({"syncedAt": datetime.now(timezone.utc).isoformat(), "products": output}, ensure_ascii=False, indent=2) + "\n"
if not target.exists() or target.read_text(encoding="utf-8") != content:
    target.write_text(content, encoding="utf-8")
# The Storefront token is used only by this GitHub Actions job to fetch the catalog.
# Never commit a token into the public Git repository. GitHub push protection
# blocks it, and a failed push would also block catalog updates.
print(f"Fourthwall sync successful: {len(output)} products.")
