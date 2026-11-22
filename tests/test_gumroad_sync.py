"""Offline regression tests for the Gumroad-to-GitHub catalog sync."""
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import sync_gumroad as sync


def row(product_id, name, permalink, price=500, published=True):
    return {
        "id": product_id, "name": name, "permalink": permalink,
        "price_cents": price, "currency": "eur", "published": published,
    }


class GumroadSyncTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.catalog = Path(self.tmp.name) / "catalog.js"
        self.catalog.write_text(
            'window.SIMON_SHOP_CATALOG = {"shopName":"Simon Libon","products":[]};\n',
            encoding="utf-8",
        )
        patch_catalog = patch.object(sync, "CATALOG", self.catalog)
        patch_catalog.start()
        self.addCleanup(patch_catalog.stop)

    def read(self):
        return sync.read_catalogue()[0]["products"]

    def test_no_published_products_never_create_checkout(self):
        inventory = [
            row("tab-id", "[SONG TITLE] — Guitar Tab", "tab", published=False),
            row("pack-id", "[SONG TITLE] — Guitar Tab + Backing Track", "pack", published=False),
        ]
        with patch.dict(os.environ, {"GUMROAD_ACCESS_TOKEN": "offline-test"}), \
             patch.object(sync, "fetch_products", return_value=inventory), \
             patch.object(sync, "api_get", side_effect=AssertionError("Draft details must not be fetched")):
            sync.main()
        self.assertEqual(self.read(), [])

    def test_published_song_products_and_bundle(self):
        inventory = [
            row("tab-id", "Kinetic — Guitar Tab", "kinetic-tab", 500),
            row("pack-id", "Kinetic — Guitar Tab + Backing Track", "kinetic-pack", 900),
            row("ep-id", "My EP — Complete EP Bundle", "kinetic-ep", 2500),
        ]

        def fake_detail(endpoint, token, params=None):
            product_id = endpoint.rsplit("/", 1)[-1]
            return {"product": next(x for x in inventory if x["id"] == product_id)}

        with patch.dict(os.environ, {"GUMROAD_ACCESS_TOKEN": "offline-test"}), \
             patch.object(sync, "fetch_products", return_value=inventory), \
             patch.object(sync, "api_get", side_effect=fake_detail):
            sync.main()
        products = self.read()
        self.assertEqual(len(products), 3)
        self.assertEqual([p["type"] for p in products], ["tabs", "pack", "bundle"])
        self.assertEqual([p["price"] for p in products], [5, 9, 25])
        self.assertTrue(all(p["published"] for p in products))
        self.assertTrue(all(p["gumroadUrl"].startswith("https://simonlibonstore.gumroad.com/l/") for p in products))

    def test_tab_and_track_modern_naming_and_zip_metadata(self):
        inventory = [
            row("modern-tab", "Reverie — Guitar Tab", "reverie-tab", 500),
            row("modern-pack", "Reverie — Tab & Track", "reverie-pack", 900),
            row("modern-bundle", "Reverie EP — Complete Bundle", "reverie-ep", 2500),
        ]
        def detail(endpoint, token, params=None):
            return {"product": next(x for x in inventory if x["id"] == endpoint.rsplit("/", 1)[-1])}
        with (patch.dict(os.environ, {"GUMROAD_ACCESS_TOKEN": "offline-test"}),
              patch.object(sync, "fetch_products", return_value=inventory),
              patch.object(sync, "api_get", side_effect=detail)):
            sync.main()
        items = self.read()
        self.assertEqual([p["type"] for p in items], ["tabs", "pack", "bundle"])
        self.assertTrue(all("ZIP" in p["includes"][0] for p in items))
        self.assertIn("WAV + MP3", items[1]["includes"][0])

    def test_demo_downloads_remain_clear_after_automatic_sync(self):
        inventory = [
            row("tab-test","FREE TEST — Demo Guitar Tab (PDF)","ksiweq",0),
            row("pack-test","FREE TEST — Demo Guitar Tab + Backing Track","mmxjjd",0),
        ]
        for item in inventory:
            item["description"] = "<p>Free technical demo with synthetic sample files to test checkout and digital delivery. Not an official music release.</p>"
        def detail(endpoint, token, params=None):
            product_id=endpoint.rsplit("/",1)[-1]
            return {"product":next(x for x in inventory if x["id"] == product_id)}
        with (patch.dict(os.environ, {"GUMROAD_ACCESS_TOKEN": "offline-test"}),
              patch.object(sync, "fetch_products", return_value=inventory),
              patch.object(sync, "api_get", side_effect=detail)):
            sync.main()
        items=self.read()
        self.assertEqual([p["type"] for p in items],["tabs","pack"])
        self.assertEqual(items[0]["includes"],["Guitar tab (PDF)"])
        self.assertEqual(items[1]["includes"],["Guitar tab (PDF)","Backing track (WAV)"])
        for product in items:
            self.assertIn("Not an official music release.",product["description"])
            self.assertNotIn("RETURN TO THE OFFICIAL",product["description"])
            self.assertNotIn("Digital download",str(product["includes"]))

    def test_current_free_txt_item_does_not_claim_pdf(self):
        inventory = [row("free-txt", "TEST ONLY — Mini Guitar Tab (gratuit)", "pnmqyo", 0)]
        inventory[0]["description"] = (
            "Contains two TXT files: test instructions and a demo guitar tab. No PDF."
        )
        def detail(endpoint, token, params=None):
            return {"product": inventory[0]}
        with (patch.dict(os.environ, {"GUMROAD_ACCESS_TOKEN": "offline-test"}),
              patch.object(sync, "fetch_products", return_value=inventory),
              patch.object(sync, "api_get", side_effect=detail)):
            sync.main()
        item = self.read()[0]
        self.assertEqual(item["includes"], ["Test instructions (TXT)", "Demo guitar tab (TXT)"])
        self.assertEqual(item["price"], 0)
        self.assertEqual(item["gumroadUrl"], "https://simonlibonstore.gumroad.com/l/pnmqyo")

    def test_invalid_catalog_is_not_overwritten(self):
        unsafe = "/* unexpected script */\nalert('x');\n"
        self.catalog.write_text(unsafe, encoding="utf-8")
        with self.assertRaises(RuntimeError):
            sync.read_catalogue()
        self.assertEqual(self.catalog.read_text(encoding="utf-8"), unsafe)

    def test_invalid_published_state_fails_closed(self):
        inventory = [row("tab-id", "Kinetic — Guitar Tab", "kinetic-tab")]
        inventory[0]["published"] = "yes"
        with patch.dict(os.environ, {"GUMROAD_ACCESS_TOKEN": "offline-test"}), \
             patch.object(sync, "fetch_products", return_value=inventory):
            with self.assertRaises(RuntimeError):
                sync.main()
        self.assertEqual(self.read(), [])


if __name__ == "__main__":
    unittest.main()
