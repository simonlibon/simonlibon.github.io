# Website-to-Gumroad synchronization rule

This is the owner's fixed policy: any update to the official site must also be
published to every corresponding Gumroad-branded path, and confirmed live.
The public visual design stays frozen; these rules change only the publication system.

Canonical site HTML/CSS lives on GitHub Pages. Gumroad owns its live published
product catalogue, prices, checkout, receipts and downloads.

Required mirrored paths: profile/home, music, concerts, tabs, merch, press,
privacy, custom product-permalink pages and native /l/permalink product pages.
Pages without a Gumroad mirror, such as the official Listen and My Library,
must remain accessible from Gumroad through live links to the canonical host.
Gumroad-owned payment and checkout screens cannot be visually duplicated.

Every push to main runs the official deploy and the relevant Gumroad publishers.
Generated custom pages carry an invisible fingerprint of their HTML and CSS.
A page may be skipped only when Gumroad already hosts the same fingerprint.
After publishing, pull and verify every branded custom page, never claim success
when one path was skipped or remains stale. A scheduled reconciliation retries
transient Gumroad preview limits. Native product routes use the same renderer.

Never change the visual styling in order to fix a synchronization bug.
Never send newsletter campaigns, modify product prices or publish drafts as a
side effect of website mirroring.
