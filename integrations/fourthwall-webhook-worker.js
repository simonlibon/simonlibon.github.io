// Optional Cloudflare Worker: connect Fourthwall shop product webhooks to GitHub Actions.
// NOT active until deployed and its secrets are configured in Cloudflare.
const GITHUB_DISPATCH_URL =
  'https://api.github.com/repos/simonlibon/simonlibon.github.io/dispatches';
const PRODUCT_EVENTS = new Set(['PRODUCT_CREATED', 'PRODUCT_UPDATED']);

async function verifiedShopWebhook(request, secret, rawBody) {
  const encoded = (request.headers.get('X-Fourthwall-Hmac-SHA256') || '').trim();
  if (!/^[a-zA-Z0-9+/]{43}=$/.test(encoded)) return false;
  const signature = Uint8Array.from(atob(encoded), (character) => character.charCodeAt(0));
  const key = await crypto.subtle.importKey(
    'raw', new TextEncoder().encode(secret), { name: 'HMAC', hash: 'SHA-256' },
    false, ['verify']
  );
  return crypto.subtle.verify('HMAC', key, signature, rawBody);
}

export default {
  async fetch(request, env) {
    if (request.method !== 'POST') {
      return new Response('Method Not Allowed', { status: 405, headers: { Allow: 'POST' } });
    }
    if (!env.FOURTHWALL_WEBHOOK_SECRET || !env.GITHUB_DISPATCH_TOKEN) {
      return new Response('Webhook integration is not configured', { status: 503 });
    }
    // Protect against unexpectedly large requests; normal product events are small.
    const indicatedSize = Number(request.headers.get('Content-Length') || 0);
    if (indicatedSize > 1024 * 1024) return new Response('Request too large', { status: 413 });

    let raw;
    try {
      raw = await request.arrayBuffer();
    } catch (_) {
      return new Response('Invalid request', { status: 400 });
    }
    if (raw.byteLength > 1024 * 1024) return new Response('Request too large', { status: 413 });

    try {
      if (!await verifiedShopWebhook(request, env.FOURTHWALL_WEBHOOK_SECRET, raw)) {
        return new Response('Invalid signature', { status: 401 });
      }
    } catch (_) {
      return new Response('Invalid signature', { status: 401 });
    }

    let event;
    try {
      event = JSON.parse(new TextDecoder().decode(raw));
    } catch (_) {
      return new Response('Invalid JSON', { status: 400 });
    }
    // Do not let arbitrary payload data enter a workflow command. The workflow
    // always pulls the canonical live public Fourthwall catalog afresh.
    if (event.testMode === true || !PRODUCT_EVENTS.has(event.type)) {
      return new Response('Event acknowledged; no catalog update needed', { status: 200 });
    }

    let response;
    try {
      response = await fetch(GITHUB_DISPATCH_URL, {
        method: 'POST',
        headers: {
          Authorization: 'Bearer ' + env.GITHUB_DISPATCH_TOKEN,
          Accept: 'application/vnd.github+json',
          'Content-Type': 'application/json',
          'User-Agent': 'SimonLibonFourthwallProductSync',
          'X-GitHub-Api-Version': '2022-11-28'
        },
        body: JSON.stringify({ event_type: 'fourthwall_products_changed' })
      });
    } catch (_) {
      // Non-200 makes Fourthwall retry transient network failures.
      return new Response('GitHub unavailable', { status: 502 });
    }
    if (response.status !== 204) return new Response('GitHub dispatch failed', { status: 502 });
    return new Response('Catalog refresh requested', { status: 200 });
  }
};
