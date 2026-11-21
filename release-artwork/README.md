# Release artwork

For each release, place the approved source artwork here:

`release-artwork/<slug>/source.png`

Use a lowercase slug such as `lueur`. In GitHub Actions, run **Prepare release cover and thumbnail** and enter that slug. The workflow creates:

- `cover-square.jpg` — 3000 × 3000, intended as the Gumroad product cover.
- `thumbnail-square.jpg` — 600 × 600, used for release cards on the official and Gumroad-mirrored shop.

When a matching published Gumroad product is synchronized, the site uses the generated thumbnail. If no generated thumbnail exists, it continues using the Gumroad cover.

The source artwork still needs to be created and approved for each release. After generation, the square cover must be attached to the Gumroad product; Gumroad product publishing and cover upload remain separate steps. Never publish a draft until its title, price, cover, and delivered files are final.
