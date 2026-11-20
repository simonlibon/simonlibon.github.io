#!/usr/bin/env python3
"""Render the *same published catalogue* in Gumroad's standalone shop HTML.

Gumroad custom pages may block remote scripts; cards must not depend on JS.
The master list is catalog.js, refreshed from the creator's actual Gumroad
products. This builder never creates, prices, or publishes Gumroad products.
"""
import html
import json
import re
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
DOMAIN = "simonlibonstore.gumroad.com"
CATALOG = ROOT / "catalog.js"


def load_catalog(path=CATALOG):
    source = Path(path).read_text(encoding="utf-8")
    match = re.fullmatch(
        r"\s*window\.SIMON_SHOP_CATALOG\s*=\s*(\{[\s\S]*\})\s*;\s*", source
    )
    if not match:
        raise ValueError("Unrecognized official catalog.js: refusing to render")
    data = json.loads(match.group(1))
    if not isinstance(data, dict) or not isinstance(data.get("products"), list):
        raise ValueError("Invalid official product catalogue")
    return data["products"]


def safe_product(item):
    if not isinstance(item, dict) or item.get("published") is not True or item.get("demo") is True:
        return None
    title = str(item.get("title") or "").strip()
    if not title or re.search(r"\[(?:song|ep|release)\s+title\]", title, re.I):
        return None
    url = str(item.get("gumroadUrl") or "")
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname != DOMAIN or parsed.port is not None:
        return None
    if not re.fullmatch(r"/l/[a-zA-Z0-9_-]+/?", parsed.path) or parsed.query or parsed.fragment:
        return None
    price = item.get("price")
    if isinstance(price, bool) or not isinstance(price, (int, float)) or not (0 <= price < 1000000):
        return None
    kind = str(item.get("type") or "")
    if kind == "backing":
        return None
    if re.search(r"\b(ep|album|bundle)\b", title, re.I) or kind == "bundle":
        kind = "bundle"
    elif re.search(r"\btabs?\b.*\bbacking\b", title, re.I) or kind == "pack":
        kind = "pack"
    elif re.search(r"\btabs?\b", title, re.I) or kind == "tabs":
        kind = "tabs"
    else:
        return None
    target = f"https://{DOMAIN}{parsed.path.rstrip('/')}"
    # Exactly the same direct checkout semantics as shop-model.js.
    checkout = target + ("?price=0&wanted=true" if price == 0 else "?wanted=true")
    return dict(title=title, kind=kind, price=price, image=item.get("image"),
                date=str(item.get("releaseDate") or ""), checkout=checkout,
                description=str(item.get("description") or ""))


def group_products(products):
    groups = {}
    seen = set()
    for entry in products:
        p = safe_product(entry)
        if not p or p["checkout"] in seen:
            continue
        seen.add(p["checkout"])
        if p["kind"] == "bundle":
            key = "bundle:" + p["title"].casefold()
            display = p["title"]
        else:
            # Same strip rule as the official shop: variants of a song share a card.
            display = re.sub(
                r"(?:\s*[-–—|:]\s*|\s+)(?:(?:official\s+)?(?:guitar\s+)?"
                r"tabs?(?:\s*\(pdf\))?|(?:guitar\s+)?tablatures?|"
                r"backing\s+tracks?|(?:guitar\s+)?tabs?\s*(?:\+|&|and)\s*"
                r"backing\s+tracks?)\s*$", "", p["title"], flags=re.I
            ).strip() or p["title"]
            key = "track:" + re.sub(r"[^a-z0-9]+", "-", display.casefold()).strip("-")
        if key not in groups:
            groups[key] = {"kind": "bundle" if p["kind"] == "bundle" else "track",
                           "title": display, "image": "", "date": "", "options": [], "search": ""}
        group = groups[key]
        group["options"].append(p)
        group["search"] += " " + p["description"]
        if not group["image"] and isinstance(p["image"], str) and p["image"].startswith("https://"):
            group["image"] = p["image"]
        group["date"] = max(group["date"], p["date"])
    all_groups = sorted(groups.values(), key=lambda g: (g["date"], g["title"].casefold()), reverse=True)
    for g in all_groups:
        priority = {"tabs": 0, "pack": 1, "bundle": 2}
        g["options"].sort(key=lambda p: priority.get(p["kind"], 3))
    return [g for g in all_groups if g["kind"] == "bundle"], [g for g in all_groups if g["kind"] == "track"]


def product_card(g):
    esc = lambda s: html.escape(str(s), quote=True)
    options = g["options"]
    choice = next((p for p in options if p["kind"] == "pack"), options[0])
    cover = ('<img src="' + esc(g["image"]) + '" alt="Cover artwork for ' +
             esc(g["title"]) + '" loading="lazy">') if g["image"] else (
             '<span class="placeholder-text">SIMON LIBON</span>')
    price = min(p["price"] for p in options)
    links = []
    labels = {"tabs": "GUITAR TAB", "pack": "TAB + TRACK", "bundle": "BUY BUNDLE"}
    for option in options:
        links.append('<a class="buy-quick" href="' + esc(option["checkout"]) +
                     '">' + labels.get(option["kind"], "BUY NOW") + '</a>')
    type_text = "Complete collection" if g["kind"] == "bundle" else "Guitar tabs & tracks"
    return ('<article class="shop-item" data-shop-release="' + esc(g["title"].casefold()) +
            '" data-shop-search="' + esc((g["title"] + " " + g["search"]).casefold()) +
            '" data-shop-date="' + esc(g["date"]) + '">'
            '<a class="shop-card-link" href="' + esc(choice["checkout"]) +
            '" aria-label="Checkout: ' + esc(g["title"]) +
            '"><div class="shop-item-image">' + cover + '</div></a>'
            '<div class="shop-item-meta"><div><h3 class="shop-item-title"><a href="' +
            esc(choice["checkout"]) + '">' + esc(g["title"]) + '</a></h3>'
            '<div class="shop-item-type">' + type_text + '</div></div>'
            '<span class="shop-item-price">' +
            ("FROM " if g["kind"] == "track" and len(options) > 1 else "") +
            "€{:.2f}".format(price) + '</span></div>'
            '<div class="shop-item-actions">' + ''.join(links) + '</div></article>')


# Progressive enhancement only. The markup works without JavaScript.
FILTER_SCRIPT = r"""
<script data-sl-static-filter="v1">
(function(){
  function init(){
    var root=document.body;
    if(!root||!root.hasAttribute('data-sl-static-catalog'))return;
    var search=document.getElementById('shop-search-input');
    var select=document.getElementById('shop-sort-select');
    var bundle=document.getElementById('shop-bundle-grid');
    var tracks=document.getElementById('shop-grid');
    var bundleSection=document.getElementById('shop-ep-section');
    var trackHeading=document.getElementById('shop-track-heading');
    var empty=document.getElementById('shop-empty');
    if(!search||!select||!bundle||!tracks||!empty)return;
    var coll=new Intl.Collator('en',{sensitivity:'base',numeric:true});
    var total=bundle.children.length+tracks.children.length;
    function sortGrid(grid){
      var cards=Array.from(grid.children);
      var sort=select.value;
      cards.sort(function(a,b){
        var name=coll.compare(a.getAttribute('data-shop-release')||'',b.getAttribute('data-shop-release')||'');
        var date=(a.getAttribute('data-shop-date')||'').localeCompare(b.getAttribute('data-shop-date')||'');
        if(sort==='az')return name;
        if(sort==='za')return -name;
        return sort==='old'?(date||name):(-date||name);
      });
      cards.forEach(function(el){grid.appendChild(el)});
    }
    function render(){
      var query=search.value.trim().toLocaleLowerCase();
      var visible=0;
      [bundle,tracks].forEach(function(grid){
        sortGrid(grid);
        Array.from(grid.children).forEach(function(card){
          var matches=!query||(card.getAttribute('data-shop-search')||'').indexOf(query)!==-1;
          card.hidden=!matches;
          if(matches)visible++;
        });
      });
      bundleSection.hidden=!Array.from(bundle.children).some(function(c){return !c.hidden});
      trackHeading.hidden=!Array.from(tracks.children).some(function(c){return !c.hidden});
      empty.hidden=visible>0;
      empty.querySelector('h3').textContent=total?'NO MATCHES.':'COMING SOON.';
    }
    search.addEventListener('input',render);
    select.addEventListener('change',render);
    render();
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);
  else init();
})();
</script>
"""


def render_shop(document, products):
    """Inject a resilient product grid into the official tabs page DOM."""
    if 'id="shop-bundle-grid" class="shop-product-grid"' not in document:
        raise ValueError("Official shop markup changed: bundle grid missing")
    if 'id="shop-grid" class="shop-product-grid"' not in document:
        raise ValueError("Official shop markup changed: track grid missing")
    bundles, tracks = group_products(products)
    def replace_one(old, new):
        nonlocal document
        if document.count(old) != 1:
            raise ValueError("Expected one official shop DOM anchor: " + old[:90])
        document = document.replace(old, new, 1)
    replace_one('<div id="shop-bundle-grid" class="shop-product-grid" aria-live="polite"></div>',
                '<div id="shop-bundle-grid" class="shop-product-grid" aria-live="polite">' +
                ''.join(product_card(g) for g in bundles) + '</div>')
    replace_one('<div id="shop-grid" class="shop-product-grid" aria-live="polite"></div>',
                '<div id="shop-grid" class="shop-product-grid" aria-live="polite">' +
                ''.join(product_card(g) for g in tracks) + '</div>')
    count = len(bundles) + len(tracks)
    replace_one('id="shop-count" class="shop-count">RELEASES',
                'id="shop-count" class="shop-count">' +
                str(count) + (" RELEASE" if count == 1 else " RELEASES"))
    if bundles:
        document = document.replace('id="shop-ep-section" class="shop-group-section" hidden',
                                    'id="shop-ep-section" class="shop-group-section"', 1)
    if tracks:
        document = document.replace('id="shop-track-heading" class="shop-list-heading" hidden',
                                    'id="shop-track-heading" class="shop-list-heading"', 1)
    if not count:
        document = document.replace('id="shop-empty" class="shop-empty" hidden',
                                    'id="shop-empty" class="shop-empty"', 1)
    if 'data-sl-mirror="official-page-tabs"' in document:
        document = document.replace(
            '<body data-sl-mirror="official-page-tabs"',
            '<body data-sl-static-catalog="1" data-sl-mirror="official-page-tabs"', 1
        )
    else:
        document = document.replace(
            '<body data-page="tabs"',
            '<body data-sl-static-catalog="1" data-page="tabs"', 1
        )
    if 'data-sl-static-catalog="1"' not in document:
        raise ValueError("Cannot mark Gumroad catalogue as pre-rendered")
    # Search/sort improve the mirror when Gumroad permits inline scripts.
    # The cards themselves remain visible even when scripts are stripped.
    if document.count("</body>") != 1:
        raise ValueError("Official shop body tag missing")
    document = document.replace("</body>", FILTER_SCRIPT + "</body>", 1)
    return document
