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
