# Simon Libon — Official website

Official artist website hosted on GitHub Pages.

## Digital shop: Gumroad

The **Tabs & Backing Tracks** section at `tabs.html` uses the original custom Gumroad storefront:
- `shop.css`, `shop.js` and `catalog.js` provide the site-native catalog, filters and purchase links.
- `scripts/sync_gumroad.py` reads **published** products from Gumroad and updates `catalog.js`.
- `.github/workflows/sync-gumroad.yml` schedules this sync and supports manual runs.
- The Gumroad token is kept in the GitHub Actions secret `GUMROAD_ACCESS_TOKEN`, never on the public site.

**Gumroad is the source of truth for saleable products.** Publish a real product with its final cover, delivered files and correct price on Gumroad first; the workflow then mirrors only published products to `catalog.js`. Do not replace that generated file with the export from the legacy `EDITEUR-BOUTIQUE.html` preview editor.

Draft, archived and unpublished products are not shown. The workflow may run later than its nominal five-minute schedule. Product checkout and delivery are handled by Gumroad. Placeholder and demo products must remain unpublished.

Custom Gumroad promotional pages may be rejected while the seller has no published product or sale. The Gumroad page workflows now skip that publication stage when the synced catalogue contains no genuine non-test product. Recheck and test the complete purchase-to-download flow after the first real product is published.

## Public pages

Home, Music, Concerts, Tabs & Backing Tracks, Merch, Press / EPK and Privacy Policy.

The Press / EPK page is accessible from the shared footer; the top navigation remains limited to Music, Concerts, Tabs & Backing Tracks and Merch.
