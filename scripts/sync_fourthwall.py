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

# Diagnostic: compare the documented public collection feed with the API.
# Print only public product titles/slugs, never credentials or response bodies.
def inspect_public_feed():
    url = SHOP + "/collections/all.json?sync_check=" + str(int(datetime.now(timezone.utc).timestamp()))
    req = urllib.request.Request(url, headers={
        "Accept": "application/json", "User-Agent": "SimonLibonCatalogSync/2.0"
    })
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            payload = json.load(response)
        print("Public feed root:", type(payload).__name__)
        if isinstance(payload, dict):
            print("Public feed keys:", sorted(payload.keys())[:15])
            for k in ("products", "results", "items", "collection"):
                v = payload.get(k)
                if isinstance(v, dict):
                    print("Public feed", k, "keys:", sorted(v.keys())[:15])
                    v = v.get("products") or v.get("results")
                if isinstance(v, list):
                    print("Public feed", k, "entries:", len(v))
                    print("Public feed items:", [(p.get("slug"), p.get("name")) for p in v[:15] if isinstance(p, dict)])
        elif isinstance(payload, list):
            print("Public feed entries:", len(payload))
            print("Public feed items:", [(p.get("slug"), p.get("name")) for p in payload[:15] if isinstance(p, dict)])
    except (urllib.error.HTTPError, urllib.error.URLError, ValueError) as exc:
        print("Public feed unavailable:", type(exc).__name__, getattr(exc, "code", ""))

inspect_public_feed()

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

# Some public bundles are missing from the 'all' collection response.
# Check the known public bundle slug directly on each scheduled sync.
# The lookup has no local placeholder: removed or private bundles disappear.
PUBLIC_BUNDLE_SLUGS = ("bundle",)
for slug in PUBLIC_BUNDLE_SLUGS:
    if any(isinstance(p, dict) and p.get("slug") == slug for p in raw):
        continue
    url = "https://storefront-api.fourthwall.com/v1/products/" + urllib.parse.quote(slug, safe="")
    url += "?" + urllib.parse.urlencode({"storefront_token": TOKEN})
    request = urllib.request.Request(url, headers={
        "Accept": "application/json",
        "User-Agent": "SimonLibonCatalogSync/2.0"
    })
    try:
        with urllib.request.urlopen(request, timeout=25) as response:
            product = json.load(response)
    except urllib.error.HTTPError as error:
        # A missing or inaccessible bundle should never hide the other products.
        print("Bundle slug lookup returned HTTP", error.code, "for", slug)
        continue
    except (urllib.error.URLError, ValueError) as error:
        print("Bundle slug lookup temporarily unavailable for", slug, type(error).__name__)
        continue
    if isinstance(product, dict) and product.get("slug") == slug:
        raw.append(product)
        print("Found bundle by public product slug:", slug)
    else:
        print("Unexpected bundle lookup response for", slug)

products = []
print("Fourthwall API returned", len(raw), "entries before filtering.")
for p in raw:
    if not isinstance(p, dict) or not p.get("slug"):
        print("Skipped entry: missing product slug")
        continue
    # The 'all' collection contains published products. Fourthwall may omit
    # state/access metadata for some listing types, including bundles.
    # Respect explicit hidden/unavailable states, but do not reject missing
    # metadata that would otherwise make a published listing disappear.
    state = p.get("state")
    access = p.get("access")
    state_type = state.get("type") if isinstance(state, dict) else (state if isinstance(state, str) else None)
    access_type = access.get("type") if isinstance(access, dict) else (access if isinstance(access, str) else None)
    if state_type and state_type != "AVAILABLE":
        print("Skipped product", p.get("name", p.get("slug")), "state:", state_type, "type:", p.get("type"))
        continue
    if access_type and access_type != "PUBLIC":
        print("Skipped product", p.get("name", p.get("slug")), "access:", access_type, "type:", p.get("type"))
        continue
    if not state_type or not access_type:
        print("Included published listing with omitted status metadata:", p.get("name", p.get("slug")), "type:", p.get("type"))
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
