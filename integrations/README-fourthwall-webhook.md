# Optional Fourthwall → GitHub near-immediate product sync

**Current status: Prepared, NOT connected or deployed.** The existing scheduled
`.github/workflows/sync-fourthwall.yml` continues working as a fallback. No
product data is edited manually by this integration.

## How it works

Fourthwall product created or updated → signed webhook POST → Cloudflare Worker
(`fourthwall-webhook-worker.js`) → authenticated GitHub `repository_dispatch`
with event type `fourthwall_products_changed` → the existing GitHub Action
runs `scripts/sync_fourthwall.py` → GitHub Pages publishes the current **public**
catalog. The action always refreshes from Fourthwall, without trusting webhook
payload fields as product data.

## Configuration required before the event-triggered sync is active

1. Deploy `integrations/fourthwall-webhook-worker.js` as a Cloudflare Worker.
   Obtain the HTTPS Worker URL. This requires a Cloudflare account and does not
   happen automatically by committing a file to GitHub.
2. In Cloudflare, configure **encrypted Worker secrets** (never commit them):
   - `FOURTHWALL_WEBHOOK_SECRET`: the shop webhook secret from Fourthwall.
   - `GITHUB_DISPATCH_TOKEN`: a fine-grained GitHub access token scoped to
     `simonlibon/simonlibon.github.io` and granted **Contents: Read and write**,
     as required to create `repository_dispatch` events. Use an expiring token
     and renew it when needed.
3. In the original Fourthwall **Tabs & Backing Tracks** shop, go to the webhook
   settings (Settings → For developers → Webhooks), register the Worker HTTPS
   URL, and subscribe to `PRODUCT_CREATED` and `PRODUCT_UPDATED` events.
   Do not subscribe a second, unrelated merch shop to this worker.
4. Publish/update a real public product to test. The Worker acknowledges
   Fourthwall test-mode notifications without triggering a real catalog
   update. Confirm an Action run with event `repository_dispatch`, then
   confirm the published website matches Fourthwall.
5. Keep the existing scheduled sync enabled. Fourthwall webhook delivery
   is not guaranteed, so periodic reconciliation is important.

The webhook receiver checks `X-Fourthwall-Hmac-SHA256` using HMAC-SHA256 of
the exact raw request body, verified with Cloudflare Web Crypto. It ignores
non-product and test-mode notifications. **Neither secret belongs in the GitHub
repository or in a chat.**

## Limitations

- The event-driven path is not live until a Worker is deployed and the
  Fourthwall webhook and secrets are configured.
- GitHub Actions and Pages still take some time after each trigger.
- `PRODUCT_UPDATED` should be tested with visibility changes. If Fourthwall
  does not emit this event on a particular visibility action, the scheduled
  reconciliation will still detect it.
- GitHub scheduled jobs may be delayed, particularly at times of high load.

Reference: https://docs.makemanifest.dev/webhooks/signature-verification/
GitHub: https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#repository_dispatch
