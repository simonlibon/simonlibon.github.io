"""Check tab/track choice links on native Gumroad pages. No network access."""
import unittest
from scripts.publish_gumroad_product_pages import options_html, build

def row(name, slug, kindprice, published=True):
    return {"name":name,"permalink":slug,"url":"https://simonlibonstore.gumroad.com/l/"+slug,
            "price_cents":kindprice,"published":published}

class ProductOptionTests(unittest.TestCase):
    def test_two_download_options_link_without_fabricating_products(self):
        tab=row("TEST TRACK — Guitar Tab","mmxjjd",500)
        pack=row("TEST TRACK — Guitar Tab + Backing Track","ntapzm",900)
        html=options_html(tab,[tab,pack])
        self.assertIn('CHOOSE YOUR DOWNLOAD',html)
        self.assertIn('class="shop-option selected"',html)
        self.assertIn('href="https://simonlibonstore.gumroad.com/l/ntapzm?wanted=true"',html)
        self.assertIn('Guitar Tab (PDF)',html)
        self.assertIn('Tab + Backing Track',html)
        self.assertEqual(html.count('class="shop-option selected"') + html.count('class="shop-option"'), 2)
        output=build(tab,[tab,pack])
        self.assertIn("CHOOSE YOUR DOWNLOAD",output)
        self.assertIn('data-gumroad-action="buy"',output)

    def test_free_demo_format_switch_bypasses_product_landing_page(self):
        tab=row("TEST TRACK — Guitar Tab","mmxjjd",0)
        pack=row("TEST TRACK — Guitar Tab + Backing Track","ntapzm",0)
        free_switch=options_html(tab,[tab,pack])
        self.assertIn('href="https://simonlibonstore.gumroad.com/l/ntapzm?price=0&amp;wanted=true"',free_switch)
        native_page=build({**tab,"price":0},[tab,pack])
        self.assertIn('data-gumroad-action="buy" data-gumroad-price="0"',native_page)
        paid_page=build({**tab,"price":500},[tab,pack])
        self.assertNotIn('data-gumroad-price="0"',paid_page)

    def test_hide_options_if_only_draft_other_format(self):
        tab=row("Kinetic — Guitar Tab","kinetic-tab",500)
        draft=row("Kinetic — Guitar Tab + Backing Track","kinetic-pack",900,False)
        self.assertEqual(options_html(tab,[tab,draft]), "")

    def test_do_not_match_ep_or_unrelated_song(self):
        ep=row("DEMO EP — Complete EP Bundle","jghmyd",2500)
        tab=row("Kinetic — Guitar Tab","kinetic-tab",500)
        self.assertEqual(options_html(ep,[ep,tab]), "")
        self.assertEqual(options_html(tab,[ep,tab]), "")

if __name__=="__main__":
    unittest.main()
