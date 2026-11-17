"""Synchronize published Gumroad products into the public website catalogue."""
import json
import os
import re
import urllib.parse
import urllib.request
from html import unescape
from pathlib import Path

TOKEN = os.environ["GUMROAD_ACCESS_TOKEN"]
BASE = "https://api.gumroad.com/v2/products"
CATALOG = Path("catalog.js")

def fetch_products():
    query = urllib.parse.urlencode({"access_token": TOKEN})
    request = urllib.request.Request(BASE + "?" + query, headers={"Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=30) as response:
        data = json.load(response)
    if not data.get("success") or not isinstance(data.get("products"), list):
        raise RuntimeError("Gumroad did not return a valid product list")
    return data["products"]

def product_type(name):
    name = name.lower()
    if "bundle" in name or ("tab" in name and ("track" in name or "backing" in name)):
        return "bundle"
    if "backing" in name or "track" in name:
        return "backing"
    return "tabs"

def main():
    products = []
    for p in fetch_products():
        if p.get("published") is not True or p.get("deleted") is True:
            continue
        url = p.get("short_url") or ""
        if not re.fullmatch(r"https://simonlibonstore\.gumroad\.com/l/[a-zA-Z0-9_-]+/?", url):
            continue
        name = str(p.get("name") or "Untitled")
        raw_description = re.sub(r"<[^>]+>", " ", str(p.get("description") or ""))
        description = re.sub(r"\s+", " ", unescape(raw_description)).strip()
        products.append({
            "id": str(p.get("id") or url),
            "title": name,
            "type": product_type(name),
            "description": description,
            "includes": [],
            "price": (p.get("price") or 0) / 100,
            "gumroadUrl": url,
            "image": p.get("thumbnail_url") or p.get("preview_url") or "",
            "published": True,
            "releaseDate": str(p.get("created_at") or "")[:10],
        })
    catalogue = {"shopName": "Simon Libon — Tabs & Backing Tracks", "products": products}
    content = "/* Auto-generated from published Gumroad products. Do not edit manually. */\n"
    content += "window.SIMON_SHOP_CATALOG = " + json.dumps(catalogue, ensure_ascii=False, indent=2) + ";\n"
    CATALOG.write_text(content, encoding="utf-8")
    print(f"Synced {len(products)} published products")

if __name__ == "__main__":
    main()
