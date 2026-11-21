"""Branded Gumroad product detail pages must mirror the official product.html."""
import unittest
from scripts.render_gumroad_products import product_pages, detail_page
from scripts.render_gumroad_catalog import group_products, detail_url, load_catalog, ROOT

def p(slug,title,kind,price):
    return {"id":slug,"title":title,"type":kind,"price":price,
            "published":True,"description":"Sample PDF and WAV download",
            "includes":["Guitar tab (PDF)"],"releaseDate":"2026-11-21",
            "gumroadUrl":"https://simonlibonstore.gumroad.com/l/"+slug,
            "image":"https://public-files.gumroad.com/cover"}

class GumroadProductDetailTests(unittest.TestCase):
    def setUp(self):
        self.items=[
            p("mmxjjd","TEST TRACK — Guitar Tab","tabs",0),
            p("ntapzm","TEST TRACK — Guitar Tab + Backing Track","pack",0),
            p("jghmyd","DEMO EP — Complete EP Bundle","bundle",0)
        ]
        self.pages=list(product_pages(self.items))

    def test_one_unique_detail_per_published_format(self):
        self.assertEqual({slug for slug,_,_ in self.pages},
                         {"product-mmxjjd","product-ntapzm","product-jghmyd"})

    def test_canonical_product_layout_title_and_checkout(self):
        for slug,group,option in self.pages:
            rendered=detail_page(group,option)
            self.assertIn('data-sl-mirror="official-page-'+slug+'"',rendered)
            for field in ('class="sl-product-layout"','class="sl-product-cover"',
                          'id="product-title"','id="product-price"',
                          'id="product-buy"','id="product-description"',
                          'class="sl-product-details"','data-sl-mirror-css="style.css"',
                          'data-sl-mirror-css="shop.css"'):
                self.assertIn(field,rendered)
            self.assertIn(group["title"],rendered)
            self.assertIn('/l/'+slug.removeprefix("product-")+'?price=0&amp;wanted=true',rendered)
            self.assertIn('href="https://simonlibonstore.gumroad.com/tabs"',rendered)
            self.assertNotIn('src="product.js',rendered)
            self.assertNotIn('id="product-error"',rendered)
            self.assertNotIn('id="newsletter-dialog"',rendered)

    def test_switch_between_tab_and_pack_without_javascript(self):
        tabs=next(detail_page(g,o) for slug,g,o in self.pages if slug=="product-mmxjjd")
        pack=next(detail_page(g,o) for slug,g,o in self.pages if slug=="product-ntapzm")
        for doc in (tabs,pack):
            self.assertIn('CHOOSE YOUR DOWNLOAD',doc)
            self.assertIn('href="https://simonlibonstore.gumroad.com/product-',doc)
            self.assertIn('class="shop-option selected"',doc)
            self.assertIn('class="shop-option"',doc)
        self.assertIn('product-ntapzm',tabs)
        self.assertIn('product-mmxjjd',pack)
        self.assertIn("TEST TRACK",tabs)
        self.assertIn("TEST TRACK",pack)

    def test_real_catalog_has_matching_live_details(self):
        entries=load_catalog()
        actual=list(product_pages(entries))
        bundles,tracks=group_products(entries)
        self.assertEqual(len(actual),sum(len(g["options"]) for g in bundles+tracks))
        urls={"https://simonlibonstore.gumroad.com/"+slug for slug,_,_ in actual}
        for g in bundles+tracks:
            self.assertIn(detail_url(g),urls)

if __name__=="__main__":
    unittest.main()
