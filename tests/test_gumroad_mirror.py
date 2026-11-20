"""The Gumroad mirror uses canonical, same-source HTML/CSS, not another theme."""
import unittest
from scripts.mirror_gumroad import mirror_profile, mirror_product, ROOT

class GumroadMirrorTests(unittest.TestCase):
    def test_home_has_canonical_structure_and_styles(self):
        original = (ROOT / "index.html").read_text(encoding="utf-8")
        mirrored = mirror_profile()
        for token in ('data-page="home"', 'class="header"', 'class="footer"',
                      'data-newsletter-open', 'data-sl-mirror-css="style.css"'):
            self.assertIn(token, mirrored)
        self.assertIn('<main></main>', mirrored)
        self.assertIn('SIMON LIBON', mirrored)
        self.assertEqual(mirrored.count('data-sl-mirror="official-home-v2"'), 1)
        self.assertIn('https://simonlibon.github.io/music.html', mirrored)
        self.assertIn('class="newsletter-dialog"', original)

    def test_product_has_canonical_markup_and_real_gumroad_buy(self):
        result = mirror_product(
            {"name": "Kinetic — Guitar Tab + Backing Track"},
            '<img src="https://example.com/cover.jpg" alt="Cover">',
            "INDIVIDUAL TRACK", "€9.00",
            ["Guitar tab (PDF)", "Backing track (WAV)"]
        )
        for token in ('data-sl-product-template="v2"', 'class="sl-product-layout"',
                      'class="sl-product-cover"', 'data-sl-mirror-css="style.css"',
                      'data-sl-mirror-css="shop.css"', 'data-gumroad-field="name"',
                      'data-gumroad-field="price"', 'data-gumroad-field="description"',
                      'data-gumroad-action="buy"', 'ALL TABS &amp; BACKING TRACKS',
                      'Kinetic — Guitar Tab + Backing Track'):
            self.assertIn(token, result)
        self.assertNotIn('src="product.js', result)
        self.assertNotIn('id="product-layout" class="sl-product-layout" hidden', result)
        self.assertNotIn('id="product-error"', result)
        self.assertTrue(len(result) < 150000)

if __name__ == "__main__":
    unittest.main()
