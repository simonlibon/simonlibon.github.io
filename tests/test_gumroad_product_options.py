"""Check tab/track choice links on native Gumroad pages. No network access."""
import unittest
from scripts.publish_gumroad_product_pages import options_html, build

def row(name, slug, kindprice, published=True):
    return {"name":name,"permalink":slug,"url":"https://simonlibonstore.gumroad.com/l/"+slug,
            "price_cents":kindprice,"published":published}

class ProductOptionTests(unittest.TestCase):
    def test_two_download_options_select_in_place_before_checkout(self):
        tab=row("TEST TRACK — Guitar Tab","mmxjjd",500)
        pack=row("TEST TRACK — Guitar Tab + Backing Track","ntapzm",900)
        markup=options_html(tab,[tab,pack])
        self.assertIn('CHOOSE YOUR DOWNLOAD',markup)
        self.assertIn('data-sl-native-formats="v4"',markup)
        self.assertEqual(markup.count('name="sl-native-download-format"'), 2)
        self.assertEqual(markup.count(' checked="checked"'), 1)
        self.assertIn('for="sl-native-tabs"',markup)
        self.assertIn('for="sl-native-pack"',markup)
        self.assertNotIn('<a class="shop-option"',markup, "Option rows must not link directly to checkout")
        self.assertIn('€5.00',markup)
        self.assertIn('€9.00',markup)
        self.assertIn('href="https://simonlibonstore.gumroad.com/l/ntapzm?wanted=true"',markup)
        output=build(tab,[tab,pack])
        self.assertIn('data-sl-native-format-css="v4"',output)
        self.assertIn('class="sl-shop sl-product-page sl-has-formats"',output)
        self.assertIn('data-gumroad-action="buy"',output)
        self.assertIn('id="product-buy"',output)
        self.assertIn('#sl-native-tabs:checked ~ .sl-native-buttons',output)
        self.assertIn('#sl-native-pack:checked ~ .sl-native-buttons',output)
        self.assertEqual(output.count('class="sl-buy-button sl-native-buy"'),2)

    def test_actual_published_demo_names_group_on_native_product_links(self):
        tab=row("FREE TEST — Demo Guitar Tab (PDF)","ksiweq",0)
        pack=row("FREE TEST — Demo Guitar Tab + Backing Track","mmxjjd",0)
        for current in (tab,pack):
            selector=options_html(current,[tab,pack])
            self.assertIn("CHOOSE YOUR DOWNLOAD",selector)
            self.assertEqual(selector.count('name="sl-native-download-format"'),2)
            self.assertIn('/l/ksiweq?price=0&amp;wanted=true',selector)
            self.assertIn('/l/mmxjjd?price=0&amp;wanted=true',selector)
            page=build(current,[tab,pack])
            self.assertIn('class="sl-shop sl-product-page sl-has-formats"',page)
            self.assertIn('data-sl-native-formats="v4"',page)
            self.assertIn('for="sl-native-tabs"',page)
            self.assertIn('for="sl-native-pack"',page)
            self.assertNotIn("ADD TO CART",page)
        self.assertIn('id="sl-native-tabs" name="sl-native-download-format" value="tabs" checked="checked"',options_html(tab,[tab,pack]))
        self.assertIn('id="sl-native-pack" name="sl-native-download-format" value="pack" checked="checked"',options_html(pack,[tab,pack]))

    def test_free_demo_format_switch_bypasses_product_landing_page(self):
        tab=row("TEST TRACK — Guitar Tab","mmxjjd",0)
        pack=row("TEST TRACK — Guitar Tab + Backing Track","ntapzm",0)
        free_switch=options_html(tab,[tab,pack])
        self.assertIn('href="https://simonlibonstore.gumroad.com/l/ntapzm?price=0&amp;wanted=true"',free_switch)
        native_page=build({**tab,"price":0},[tab,pack])
        self.assertIn('data-gumroad-action="buy"',native_page)
        self.assertIn('data-gumroad-price="0"',native_page)
        self.assertIn('href="https://simonlibonstore.gumroad.com/l/mmxjjd?price=0&amp;wanted=true"',native_page)
        # The visible "Buy Now" action is a regular HTTPS checkout link,
        # not Gumroad's native product-page action that could reopen the listing.
        self.assertIn('class="sl-gumroad-native-fallback" data-gumroad-action="buy"',native_page)
        paid_page=build({**tab,"price":500},[tab,pack])
        self.assertNotIn('data-gumroad-price="0"',paid_page)
        self.assertIn('href="https://simonlibonstore.gumroad.com/l/mmxjjd?wanted=true"',paid_page)

    def test_only_published_sku_buys_directly_and_keeps_native_fallback(self):
        tab=row("FREE TEST — Demo Guitar Tab (PDF)","mmxjjd",0)
        page=build(tab,[tab])
        self.assertIn('<a id="product-buy" class="sl-buy-button" href="https://simonlibonstore.gumroad.com/l/mmxjjd?price=0&amp;wanted=true"',page)
        self.assertIn('class="sl-gumroad-native-fallback" data-gumroad-action="buy"',page)
        self.assertNotIn('id="product-buy" class="sl-buy-button" data-gumroad-action',page)
        self.assertNotIn('href="https://simonlibonstore.gumroad.com/l/mmxjjd"',page)
        self.assertNotIn("ADD TO CART",page)

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
