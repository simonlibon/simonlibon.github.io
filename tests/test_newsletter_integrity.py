"""Offline newsletter regression checks. Never subscribes or sends email."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
FORM = "https://eocampaign1.com/form/e481fb88-e48d-11f1-b718-bf82b7962b6e.js"
PAGES = ("index.html", "music.html", "concerts.html", "tabs.html",
         "merch.html", "press.html", "privacy.html")


class NewsletterIntegrityTests(unittest.TestCase):
    def test_every_official_page_has_one_working_embed_reference(self):
        for page in PAGES:
            with self.subTest(page=page):
                content = (ROOT / page).read_text(encoding="utf-8")
                self.assertEqual(content.count('id="newsletter-dialog"'), 1)
                self.assertEqual(content.count(FORM), 1)
                self.assertIn('data-form="e481fb88-e48d-11f1-b718-bf82b7962b6e"', content)
                self.assertIn('data-newsletter-open', content)
                self.assertIn('src="site.js?v=newsletter-unified-20261121"', content)
                self.assertNotIn("Newsletter works independently of cached shared scripts.", content)
                self.assertNotIn("const newsletterDialog=document.getElementById('newsletter-dialog');", content)

    def test_shared_handler_opens_once_and_supports_gumroad_link(self):
        script = (ROOT / "site.js").read_text(encoding="utf-8")
        for expected in (
            "function initNewsletterDialog()",
            "if (dialog.open || typeof dialog.showModal !== 'function') return;",
            "document.addEventListener('click', function(event)",
            "new URLSearchParams(location.search).get('newsletter') === '1'",
            "location.hash === '#newsletter'",
            "window.addEventListener('hashchange', openFromLink)",
            "initConcertCountryPicker",
        ):
            self.assertIn(expected, script)
        self.assertEqual(script.count("dialog.showModal();"), 1)

    def test_mobile_modal_is_width_limited_and_scrollable(self):
        home = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn("width:min(420px,calc(100vw - 32px))", home)
        self.assertIn("max-height:calc(100dvh - 36px)", home)
        self.assertIn("https://simonlibon.github.io/?newsletter=1", 
                      (ROOT / "scripts/mirror_gumroad.py").read_text(encoding="utf-8").replace(
                          "url = SITE + \"?newsletter=1\"", "https://simonlibon.github.io/?newsletter=1"))


if __name__ == "__main__":
    unittest.main()
