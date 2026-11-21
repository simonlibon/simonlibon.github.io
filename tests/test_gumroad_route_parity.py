import unittest
from scripts.mirror_gumroad import mirror_profile, mirror_standalone, stamp_mirror_revision
from scripts.render_gumroad_catalog import load_catalog
from scripts.render_gumroad_products import product_pages, detail_page
from scripts.verify_gumroad_route import check, revision

class MirrorRevisionTest(unittest.TestCase):
    def test_static_routes(self):
        for slug in ("music","concerts","tabs","merch","press","privacy"):
            with self.subTest(slug=slug):
                check(slug,mirror_standalone(slug))
    def test_product_routes(self):
        count=0
        for slug,group,selected in product_pages(load_catalog()):
            check(slug,detail_page(group,selected))
            count+=1
        self.assertGreater(count,0)
    def test_homepage_stamp(self):
        self.assertEqual(len(revision(mirror_profile())),20)
    def test_revision_changes_with_html_or_css(self):
        a=stamp_mirror_revision("<main><p>old</p></main>")
        b=stamp_mirror_revision("<main><p>new</p></main>")
        self.assertNotEqual(revision(a),revision(b))
    def test_outdated_content_is_rejected(self):
        source=mirror_standalone("tabs")
        with self.assertRaises(ValueError):
            check("tabs",source.replace('data-sl-mirror-sha=',"data-sl-old="))
        with self.assertRaises(ValueError):
            check("concerts",source)
