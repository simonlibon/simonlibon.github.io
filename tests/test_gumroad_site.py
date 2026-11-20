"""Regression tests for real Gumroad music and concert feeds; no network or sales."""
import datetime as dt
import unittest

from scripts.build_gumroad_site import build, concerts_html, releases_html

TODAY = dt.date(2026, 11, 21)
TEMPLATE = "<main><!-- SIMON_RELEASES_FEED --><!-- SIMON_CONCERTS_FEED --></main>"


class GumroadSiteTests(unittest.TestCase):
    def test_empty_site_has_no_fake_events_or_releases(self):
        self.assertEqual(build(TEMPLATE, [], [], TODAY), "<main></main>")

    def test_published_valid_release_only(self):
        items = [
            {"id": "draft", "title": "Unpublished", "published": False,
             "platforms": [{"url": "https://example.com/track"}]},
            {"id": "published", "title": "Song <One>", "published": True,
             "type": "single", "platforms": [{"url": "https://example.com/track"}]},
            {"id": "no-links", "title": "Invalid", "published": True,
             "platforms": [{"url": "javascript:alert(1)"}]},
        ]
        rendered = releases_html(items)
        self.assertIn("Song &lt;One&gt;", rendered)
        self.assertIn("listen.html?id=published", rendered)
        self.assertNotIn("Unpublished", rendered)
        self.assertNotIn("Invalid", rendered)
        self.assertNotIn("<One>", rendered)

    def test_upcoming_concerts_escape_and_validate_urls(self):
        items = [
            {"date": "2026-11-20", "city": "Past", "country": "Belgium", "ticketUrl": "https://example.com"},
            {"date": "2026-12-03", "city": "Liège <LIVE>", "country": "Belgium",
             "ticketUrl": "javascript:alert(1)"},
            {"date": "2027-01-03", "city": "Brussels", "country": "Belgium",
             "ticketUrl": "https://tickets.example.com/show"},
        ]
        rendered = concerts_html(items, TODAY)
        self.assertIn("Liège &lt;LIVE&gt;", rendered)
        self.assertIn("https://tickets.example.com/show", rendered)
        self.assertNotIn("Past", rendered)
        self.assertNotIn("javascript:", rendered)
        self.assertLess(rendered.index("Liège"), rendered.index("Brussels"))

    def test_template_requires_both_feeds_exactly_once(self):
        with self.assertRaises(ValueError):
            build("<main></main>", [], [], TODAY)
        with self.assertRaises(ValueError):
            build(TEMPLATE + "<!-- SIMON_RELEASES_FEED -->", [], [], TODAY)


if __name__ == "__main__":
    unittest.main()
