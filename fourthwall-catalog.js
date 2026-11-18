(() => {
  'use strict';
  const shop = 'https://simon-libon-music-shop.fourthwall.com';
  const grid = document.getElementById('fw-products');
  const message = document.getElementById('fw-message');
  const number = document.getElementById('fw-count');
  const search = document.getElementById('fw-search');
  const sorter = document.getElementById('fw-sort');
  const filters = Array.from(document.querySelectorAll('[data-fw-filter]'));
  if (!grid || !message || !number || !search || !sorter) return;

  let products = [], filter = 'all';
  const validUUID = /^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$/i;

  const el = (tag, className, content) => {
    const n = document.createElement(tag);
    if (className) n.className = className;
    if (content !== undefined) n.textContent = content;
    return n;
  };

  const category = p => {
    const name = (p.name || '').toLowerCase();
    if (p.productType === 'BUNDLE' || /bundle|pack|complete ep|full ep/.test(name)) return 'bundle';
    if (/backing|instrumental|track/.test(name)) return 'backing';
    return 'tabs';
  };

  function price(p) {
    if (typeof p.price !== 'number' || !Number.isFinite(p.price)) return '';
    try {
      return new Intl.NumberFormat('en-IE', {
        style: 'currency', currency: p.currency || 'EUR'
      }).format(p.price);
    } catch (_) { return String(p.price) + ' ' + (p.currency || ''); }
  }

  function trustedProductUrl(p) {
    try {
      const url = new URL(p.url);
      return url.protocol === 'https:' && url.origin === shop && url.pathname.startsWith('/products/')
        ? url.href : '';
    } catch (_) { return ''; }
  }

  // A product is purchased one at a time. Nothing is stored in a local cart.
  // This is Fourthwall's previously used single-variant direct checkout link.
  function checkoutUrl(p) {
    // Only native Fourthwall bundle types need a product-page checkout.
    // A digital product named "Bundle" with one variant uses the normal direct checkout.
    if (p.productType === 'BUNDLE') return '';
    if (!validUUID.test(p.variantId || '') || p.variantCount !== 1 || p.available !== true) return '';
    const url = new URL('/cart/checkout', shop);
    url.searchParams.set('products', p.variantId + ':1');
    url.searchParams.set('currency', p.currency || 'EUR');
    return url.href;
  }

  function productCard(p) {
    const card = el('article', 'fw-product-card');
    const cover = el('div', 'fw-product-art');
    if (p.image && /^https:\/\//.test(p.image)) {
      const img = el('img');
      img.src = p.image;
      img.alt = 'Cover of ' + p.name;
      img.loading = 'lazy';
      cover.append(img);
    } else {
      cover.append(el('span', 'fw-art-placeholder', 'SIMON LIBON'));
    }
    card.append(cover);
    const copy = el('div', 'fw-product-copy');
    const label = {tabs: 'GUITAR TABS', backing: 'BACKING TRACK', bundle: 'BUNDLE'}[category(p)];
    copy.append(el('span', 'fw-product-type', label));
    copy.append(el('h2', 'fw-product-title', p.name));
    const cost = price(p);
    if (cost) copy.append(el('div', 'fw-product-price', cost));
    if (p.description) copy.append(el('p', 'fw-product-description', p.description));
    const actions = el('div', 'fw-product-actions');
    const buy = checkoutUrl(p);
    const detail = trustedProductUrl(p);
    if (buy) {
      const link = el('a', 'fw-buy-button', 'BUY NOW');
      link.href = buy;
      link.setAttribute('aria-label', 'Buy ' + p.name + ' — Fourthwall checkout');
      actions.append(link);
    } else if (detail) {
      const link = el('a', 'fw-buy-button', 'BUY NOW');
      link.href = detail;
      link.setAttribute('aria-label', 'View and buy ' + p.name + ' on Fourthwall');
      actions.append(link);
    }
    copy.append(actions);
    card.append(copy);
    return card;
  }

  function render() {
    const term = search.value.trim().toLocaleLowerCase();
    const visible = products.filter(p =>
      (filter === 'all' || category(p) === filter) &&
      ((p.name || '').toLocaleLowerCase().includes(term) ||
      (p.description || '').toLocaleLowerCase().includes(term)));
    const nameOrder = (a, b) => (a.name || '').localeCompare(b.name || '', 'en');
    const dateOrder = (a, b) => String(b.createdAt || '').localeCompare(String(a.createdAt || ''));
    const priceOrder = (a, b, direction) => {
      const aPrice = Number.isFinite(a.price) ? a.price : null;
      const bPrice = Number.isFinite(b.price) ? b.price : null;
      if (aPrice === null) return bPrice === null ? nameOrder(a, b) : 1;
      if (bPrice === null) return -1;
      return direction * (aPrice - bPrice) || nameOrder(a, b);
    };
    visible.sort((a, b) => {
      switch (sorter.value) {
        case 'old': return -dateOrder(a, b) || nameOrder(a, b);
        case 'az': return nameOrder(a, b);
        case 'za': return -nameOrder(a, b);
        case 'price-low': return priceOrder(a, b, 1);
        case 'price-high': return priceOrder(a, b, -1);
        default: return dateOrder(a, b) || nameOrder(a, b);
      }
    });
    grid.replaceChildren(...visible.map(productCard));
    number.textContent = products.length + (products.length === 1 ? ' RELEASE' : ' RELEASES');
    filters.forEach(b => b.setAttribute('aria-pressed', String(b.dataset.fwFilter === filter)));
    message.hidden = visible.length > 0;
    if (!visible.length) {
      message.textContent = products.length
        ? 'No releases match this search.'
        : 'No published releases at the moment.';
    }
  }

  async function load() {
    try {
      // Fresh JSON from GitHub Pages; Fourthwall stays the source of product data.
      const response = await fetch('fourthwall-products.json?t=' + Date.now(), {cache: 'no-store'});
      if (!response.ok) throw new Error('Catalog unavailable');
      const data = await response.json();
      // Show the latest successfully synchronized catalog even if the sync is delayed.
      // A delayed sync must not make the entire storefront disappear.
      if (!Array.isArray(data.products)) throw new Error('Invalid catalog');
      products = data.products.filter(p => p &&
        p.available === true && typeof p.id === 'string' &&
        typeof p.name === 'string' && trustedProductUrl(p));
      products.sort((a, b) => String(b.createdAt || '').localeCompare(String(a.createdAt || '')));
      search.disabled = false;
      sorter.disabled = false;
      filters.forEach(b => { b.disabled = false; });
      render();
    } catch (_) {
      products = [];
      grid.replaceChildren();
      number.textContent = 'RELEASES';
      message.hidden = false;
      message.textContent = 'The Fourthwall catalog is temporarily unavailable. Please try again shortly.';
    }
  }
  filters.forEach(b => b.addEventListener('click', () => {
    filter = b.dataset.fwFilter;
    render();
  }));
  search.addEventListener('input', render);
  sorter.addEventListener('change', render);
  load();
  document.addEventListener('visibilitychange', () => { if (!document.hidden) load(); });
  setInterval(() => { if (!document.hidden) load(); }, 120000);
})();