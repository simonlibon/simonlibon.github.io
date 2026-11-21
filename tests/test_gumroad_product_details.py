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
            self.assertRegex(rendered, r'<main data-sl-mirror-sha="[0-9a-f]{20}"')
            self.assertIn('Canonical product sheet: balanced framing and readable type v3.',rendered)
            self.assertIn('Unified final product details across official, native and custom Gumroad routes v4.',rendered)
            self.assertIn('font-weight:700!important',rendered)
            self.assertIn('list-style-type:disc!important',rendered)
            self.assertIn('display:list-item!important',rendered)
            self.assertIn('font-size:16px!important',rendered)
            self.assertIn('@media(max-width:860px)',rendered)
            for field in ('class="sl-product-layout"','class="sl-product-cover"',
                          'id="product-title"','id="product-price"',
                          'id="product-buy"','id="product-description"',
                          'class="sl-product-details"','data-sl-mirror-css="style.css"',
                          'data-sl-mirror-css="shop.css"'):
                self.assertIn(field,rendered)
            self.assertIn(group["title"],rendered)
            self.assertIn('/l/'+slug.removeprefix("product-")+'?price=0&amp;wanted=true',rendered)
            self.assertIn('href="https://simonlibonstore.gumroad.com/tabs"',rendered)
            self.assertNotIn('class="shop-cart-link sl-product-cart-link"',rendered)
            self.assertNotIn('href="https://gumroad.com/checkout',rendered)
            self.assertNotIn('id="product-add-to-cart"',rendered)
            self.assertNotIn('ADD TO CART',rendered)
            self.assertNotIn('src="product.js',rendered)
            self.assertNotIn('id="product-error"',rendered)
            self.assertNotIn('id="newsletter-dialog"',rendered)

    def test_switch_between_tab_and_pack_in_place_without_javascript(self):
        tabs=next(detail_page(g,o) for slug,g,o in self.pages if slug=="product-mmxjjd")
        pack=next(detail_page(g,o) for slug,g,o in self.pages if slug=="product-ntapzm")
        for doc in (tabs,pack):
            self.assertIn('CHOOSE YOUR DOWNLOAD',doc)
            self.assertIn('data-sl-inline-formats="v3"',doc)
            self.assertIn('type="radio" id="sl-format-tabs"',doc)
            self.assertIn('type="radio" id="sl-format-pack"',doc)
            self.assertIn('for="sl-format-tabs"',doc)
            self.assertIn('for="sl-format-pack"',doc)
            self.assertIn('#sl-format-tabs:checked ~ ',doc)
            self.assertIn('#sl-format-pack:checked ~ ',doc)
            self.assertNotIn('href="https://simonlibonstore.gumroad.com/product-',doc)
            self.assertIn('href="https://simonlibonstore.gumroad.com/l/mmxjjd?price=0&amp;wanted=true"',doc)
            self.assertIn('href="https://simonlibonstore.gumroad.com/l/ntapzm?price=0&amp;wanted=true"',doc)
            self.assertEqual(doc.count('name="sl-download-format"'),2)
            self.assertEqual(doc.count(' checked="checked"'),1)
            self.assertEqual(doc.count('class="sl-buy-button sl-variant-buy"'),2)
            self.assertEqual(doc.count('id="product-buy"'),1)
        self.assertIn('id="sl-format-tabs" name="sl-download-format" value="tabs" checked="checked"',tabs)
        self.assertIn('id="sl-format-pack" name="sl-download-format" value="pack" checked="checked"',pack)

    def test_included_files_and_description_have_clean_spacing(self):
        demo=[
            {**p("ksiweq","FREE TEST — Demo Guitar Tab (PDF)","tabs",0),
             "description":"Free technical demo. Not an official music release.",
             "includes":["Guitar tab (PDF)"]},
            {**p("mmxjjd","FREE TEST — Demo Guitar Tab + Backing Track","pack",0),
             "description":"Free technical demo. Not an official music release.",
             "includes":["Guitar tab (PDF)","Backing track (WAV)"]},
        ]
        pages=list(product_pages(demo))
        self.assertEqual(len(pages),2)
        for slug,g,o in pages:
            page=detail_page(g,o)
            self.assertIn('class="sl-payment-copy"',page)
            self.assertIn('data-sl-inline-formats="v3"',page)
            self.assertIn('Free technical demo. Not an official music release.',page)
            self.assertNotIn('RETURN TO THE OFFICIAL SIMON LIBON SHOP',page)
            self.assertNotIn('Digital download</li>',page)
            self.assertNotIn('class="shop-cart-link sl-product-cart-link"',page)
            self.assertLess(page.index('BUY NOW · SECURE CHECKOUT'),page.index('class="sl-payment-copy"'))
            self.assertIn('Backing track (WAV)',page)

    def test_route_matrix_same_title_variants_and_files_for_all_skus(self):
        from scripts.publish_gumroad_product_pages import build
        from urllib.parse import urlparse
        catalog=load_catalog()
        native_rows=[{"name":p["title"],"permalink":p["id"],"price_cents":round(p["price"]*100),
                      "published":True} for p in catalog if p.get("published")]
        bundles,tracks=group_products(catalog)
        self.assertTrue(tracks)
        for group in bundles+tracks:
            for opt in group["options"]:
                sku=urlparse(opt["checkout"]).path.rsplit("/",1)[-1]
                standalone=detail_page(group,opt)
                native=build(next(p for p in native_rows if p["permalink"]==sku),native_rows)
                common='<h1 id="product-title">'+group["title"]+'</h1>'
                self.assertIn(common,standalone)
                self.assertIn(common,native)
                for doc in (standalone,native):
                    self.assertIn('data-sl-canonical-product="v1"',doc)
                    self.assertRegex(doc, r'<main data-sl-mirror-sha="[0-9a-f]{20}"')
                    self.assertIn('class="sl-product-layout"',doc)
                    self.assertIn('class="shop-purchase-options"',doc)
                    self.assertIn('CHOOSE YOUR DOWNLOAD',doc)
                    self.assertIn('WHAT\'S INCLUDED',doc)
                    self.assertIn('class="sl-payment-copy"',doc)
                    self.assertIn('data-sl-inline-formats="v3"',doc)
                    self.assertNotIn('shop-cart-link sl-product-cart-link',doc)
                    self.assertNotIn('ADD TO CART',doc)
                    self.assertNotIn('RETURN TO THE OFFICIAL SIMON LIBON SHOP',doc)
                    self.assertEqual(doc.count('name="sl-download-format"'),len(group["options"]))
                    self.assertEqual(doc.count(' checked="checked"'),1)
                    for option in group["options"]:
                        self.assertIn(option["checkout"].replace("&","&amp;"),doc)
                        for file in option.get("includes",[]):
                            self.assertIn(file,doc)
                self.assertIn('data-gumroad-action="buy"',native)
                self.assertIn('data-gumroad-field="name"',native)
                self.assertNotIn('data-gumroad-action="buy"',standalone)

    def test_mobile_navigation_matches_all_site_sections(self):
        source=(ROOT/"product.html").read_text(encoding="utf-8")
        self.assertIn('body[data-page="product"] .header-inner{height:58px!important',source)
        self.assertIn('body[data-page="product"] .nav,body[data-page="product"] .nav.open{display:grid!important;grid-template-columns:repeat(4,minmax(0,1fr))!important;width:100%!important;height:47px!important',source)
        self.assertIn('html{overflow-y:scroll;scrollbar-gutter:stable}', (ROOT/"style.css").read_text(encoding="utf-8"))

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
