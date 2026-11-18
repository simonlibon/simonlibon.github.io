# Simon Libon — Official website

Official artist website hosted on GitHub Pages.

## Digital shop: Gumroad

The **Tabs & Backing Tracks** section at `tabs.html` uses the original custom Gumroad storefront:
- `shop.css`, `shop.js` and `catalog.js` provide the site-native catalog, filters and purchase links.
- `scripts/sync_gumroad.py` reads **published** products from Gumroad and updates `catalog.js`.
- `.github/workflows/sync-gumroad.yml` schedules this sync and supports manual runs.
- The Gumroad token is kept in the GitHub Actions secret `GUMROAD_ACCESS_TOKEN`, never on the public site.

Draft, archived and unpublished products are not shown. The workflow may run later than its nominal schedule. Product checkout and delivery are handled by Gumroad.

## Public pages

Home, Music, Concerts, Tabs & Backing Tracks, Merch, Press / EPK and Privacy Policy.

The Press / EPK page is accessible from the shared footer; the top navigation remains limited to Music, Concerts, Tabs & Backing Tracks and Merch.
