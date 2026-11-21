"""Gumroad's catalogue must remain visible when remote JavaScript is blocked."""
import unittest
from pathlib import Path
from scripts.render_gumroad_catalog import (
    load_catalog, group_products, render_shop, product_card, safe_product, detail_url, ROOT
)
from scripts.mirror_gumroad import mirror_standalone


def product(name, slug, kind, price=5, published=True):
    return {
        "id": slug, "title": name, "type": kind,
        "price": price, "published": published, "releaseDate": "2026-11-21",
        "gumroadUrl": "https://simonlibonstore.gumroad.com/l/" + slug,
        "image": "https://public-files.gumroad.com/demo-cover",
        "description": "Valid download",
    }


class GumroadCatalogHTMLTests(unittest.TestCase):
    def setUp(self):
        self.products = [
            product("TEST TRACK — Guitar Tab", "mmxjjd", "tabs", 0),
            product("TEST TRACK — Guitar Tab + Backing Track", "ntapzm", "pack", 0),
            product("DEMO EP — Complete EP Bundle", "jghmyd", "bundle", 0),
            product("[SONG TITLE] — Guitar Tab", "notready", "tabs"),
            product("Hidden — Guitar Tab", "hidden", "tabs", published=False),
            product("Only — Backing Track", "audioalone", "backing"),
        ]

    def test_group_same_song_and_bundle(self):
        bundles, tracks = group_products(self.products)
        self.assertEqual(len(bundles), 1)
        self.assertEqual(len(tracks), 1)
        self.assertEqual(len(tracks[0]["options"]), 2)
        self.assertEqual(tracks[0]["title"], "TEST TRACK")
        self.assertEqual(bundles[0]["title"], "DEMO EP — Complete EP Bundle")

    def test_shop_cards_open_branded_product_details_without_js(self):
        original = (ROOT / "tabs.html").read_text(encoding="utf-8")
        result = render_shop(original, self.products)
        self.assertEqual(result.count('class="shop-item"'), 2)
        bundles,tracks=group_products(self.products)
        self.assertIn(detail_url(bundles[0]), result)
        self.assertIn(detail_url(tracks[0]), result)
        self.assertNotIn("?price=0&amp;wanted=true", result, "product cover must not send visitors to checkout")
        self.assertIn("VIEW OPTIONS", result)
        self.assertIn("VIEW BUNDLE", result)
        self.assertIn('data-sl-static-catalog="1"', result)
        self.assertIn('id="shop-count" class="shop-count">2 RELEASES', result)
        self.assertNotIn("notready", result)
        self.assertNotIn("audioalone", result)
        self.assertNotIn("Hidden — Guitar Tab", result)
        self.assertIn('id="shop-ep-section" class="shop-group-section"', result)
        self.assertIn('id="shop-track-heading" class="shop-list-heading"', result)

    def test_empty_shop_has_explicit_message(self):
        source = (ROOT / "tabs.html").read_text(encoding="utf-8")
        result = render_shop(source, [])
        self.assertEqual(result.count('class="shop-item"'), 0)
        self.assertIn('id="shop-empty" class="shop-empty"', result)
        self.assertIn('>0 RELEASES', result)
        self.assertIn('COMING SOON', result)

    def test_reject_unpublished_template_untrusted_url(self):
        bad = product("Track — Guitar Tab", "slug", "tabs")
        bad["gumroadUrl"] = "https://attacker.example/l/slug"
        self.assertIsNone(safe_product(bad))
        bad["gumroadUrl"] = "https://simonlibonstore.gumroad.com/l/slug"
        self.assertIsNotNone(safe_product(bad))
        bad["published"] = False
        self.assertIsNone(safe_product(bad))

    def test_current_gumroad_build_matches_official_catalogue(self):
        catalog = load_catalog()
        published = sum(len(g["options"]) for group in group_products(catalog) for g in group)
        mirrored = mirror_standalone("tabs")
        self.assertEqual(mirrored.count('class="shop-item"'), sum(len(group) for group in group_products(catalog)))
        self.assertGreaterEqual(published, 0)
        for collection in group_products(catalog):
            for group in collection:
                self.assertIn(detail_url(group), mirrored)
        self.assertNotIn("SHOP TEMPORARILY UNAVAILABLE", mirrored)


if __name__ == "__main__":
    unittest.main()
