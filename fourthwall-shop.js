(function () {
  "use strict";
  const shop = "https://simon-libon-music-shop.fourthwall.com";
  const key = "simonlibon_fourthwall_cart_v1";
  const grid = document.getElementById("shop-grid");
  const count = document.getElementById("shop-count");
  const empty = document.getElementById("shop-empty");
  const search = document.getElementById("shop-search-input");
  const sort = document.getElementById("shop-sort-select");
  const filters = Array.from(document.querySelectorAll("[data-shop-filter]"));
  const openButton = document.getElementById("fourthwall-cart-open");
  if (!grid || !count || !empty || !search || !sort || !openButton) return;

  const categories = { tabs: "Guitar tabs", backing: "Backing tracks", bundle: "Bundles" };
  let products = [];
  let active = "all";
  let cart = [];
  let catalogVerified = false;
  let catalogError = false;
  let catalogRefresh = null;
  let controlsReady = false;
  let cartNotice = "";
  const uuid = /^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$/i;
  const category = p => /bundle|pack|ep complete|ep full/i.test(p.name) || p.productType === "BUNDLE"
    ? "bundle" : /backing|track|instrumental/i.test(p.name) ? "backing" : "tabs";
  const node = (tag, cls, value) => {
    const el = document.createElement(tag);
    if (cls) el.className = cls;
    if (value !== undefined) el.textContent = value;
    return el;
  };
  function money(amount, currency) {
    try { return new Intl.NumberFormat("en-IE", { style: "currency", currency: currency || "USD" }).format(amount); }
    catch { return String(amount) + " " + (currency || "USD"); }
  }
  function canAdd(p) {
    return p.productType !== "BUNDLE" && p.available !== false && p.variantCount === 1
      && typeof p.variantId === "string" && uuid.test(p.variantId);
  }
  function readCart() {
    try {
      const stored = JSON.parse(localStorage.getItem(key) || "[]");
      cart = Array.isArray(stored) ? stored.filter(i => i && typeof i.id === "string" && Number.isInteger(i.quantity) && i.quantity > 0).slice(0, 100) : [];
    } catch { cart = []; }
  }
  function saveCart() {
    try { localStorage.setItem(key, JSON.stringify(cart)); } catch {}
    renderCart();
  }
  readCart();

  const overlay = node("div", "fw-cart-overlay");
  overlay.hidden = true;
  const shade = node("button", "fw-cart-shade");
  shade.type = "button";
  shade.setAttribute("aria-label", "Close shopping cart");
  const panel = node("section", "fw-cart-panel");
  panel.setAttribute("role", "dialog");
  panel.setAttribute("aria-modal", "true");
  panel.setAttribute("aria-label", "Shopping cart");
  const header = node("div", "fw-cart-head");
  const heading = node("h2", "", "YOUR CART");
  const closeButton = node("button", "fw-cart-close", "×");
  closeButton.type = "button";
  closeButton.setAttribute("aria-label", "Close shopping cart");
  header.append(heading, closeButton);
  const cartItems = node("div", "fw-cart-items");
  const footer = node("div", "fw-cart-footer");
  const note = node("p", "fw-cart-note", "Total is estimated. Final pricing is confirmed at Fourthwall checkout.");
  const total = node("div", "fw-cart-total");
  const checkout = node("button", "fw-cart-checkout", "CHECKOUT");
  checkout.type = "button";
  const continueButton = node("button", "fw-cart-continue", "CONTINUE SHOPPING");
  continueButton.type = "button";
  const fallbackArea = node("div", "fw-cart-fallback");
  fallbackArea.hidden = true;
  const fallbackText = node("p", "fw-cart-fallback-note");
  const fallbackLink = node("a", "fw-cart-fallback-link", "OPEN FOURTHWALL");
  fallbackLink.rel = "noopener noreferrer";
  fallbackArea.append(fallbackText, fallbackLink);
  footer.append(note, total, fallbackArea, checkout, continueButton);
  panel.append(header, cartItems, footer);
  overlay.append(shade, panel);
  document.body.append(overlay);

  function showCart() {
    renderCart();
    overlay.hidden = false;
    document.body.classList.add("fw-cart-visible");
    closeButton.focus();
    // Every time the cart opens, check current products and remove discontinued ones.
    refreshCatalog();
  }
  function hideCart() {
    overlay.hidden = true;
    document.body.classList.remove("fw-cart-visible");
    openButton.focus();
  }
  openButton.addEventListener("click", showCart);
  shade.addEventListener("click", hideCart);
  closeButton.addEventListener("click", hideCart);
  continueButton.addEventListener("click", hideCart);
  document.addEventListener("keydown", e => {
    if (e.key === "Escape" && !overlay.hidden) hideCart();
  });
  function availableCart() {
    const known = new Map(products.map(p => [p.id, p]));
    return cart.map(item => ({ item, product: known.get(item.id) })).filter(x => x.product);
  }
  function renderCart() {
    const entries = availableCart();
    const qty = catalogVerified ? cart.reduce((n, item) => n + item.quantity, 0) : 0;
    openButton.querySelector("[data-cart-count]").textContent = String(qty);
    cartItems.replaceChildren();
    total.replaceChildren();
    checkout.disabled = true;
    checkout.hidden = false;
    fallbackArea.hidden = true;
    checkoutStatus.hidden = true;

    if (!catalogVerified) {
      cartItems.append(node("p", "fw-cart-empty", catalogError
        ? "Could not verify the current Fourthwall products. Please try again."
        : "Checking current products and your saved cart…"));
    } else {
      if (cartNotice) cartItems.append(node("p", "fw-cart-warning", cartNotice));
      if (!cart.length) {
        cartItems.append(node("p", "fw-cart-empty", "Your cart is empty. Add a release to get started."));
      } else {
        for (const { item, product: p } of entries) {
          const line = node("div", "fw-cart-line");
          if (p.image) {
            const img = node("img", "fw-cart-thumb");
            img.src = p.image; img.alt = ""; img.loading = "lazy"; line.append(img);
          }
          const details = node("div", "fw-cart-line-copy");
          details.append(node("strong", "", p.name), node("small", "", money(Number(p.price || 0), p.currency)));
          const controls = node("div", "fw-cart-qty");
          const minus = node("button", "", "−");
          const plus = node("button", "", "+");
          const number = node("span", "", String(item.quantity));
          minus.type = plus.type = "button";
          minus.setAttribute("aria-label", "Decrease quantity for " + p.name);
          plus.setAttribute("aria-label", "Increase quantity for " + p.name);
          minus.addEventListener("click", () => changeQuantity(p.id, item.quantity - 1));
          plus.addEventListener("click", () => changeQuantity(p.id, Math.min(99, item.quantity + 1)));
          controls.append(minus, number, plus);
          details.append(controls);
          line.append(details);
          cartItems.append(line);
        }
        const currencies = new Set(entries.map(x => x.product.currency || "USD"));
        if (currencies.size === 1 && entries.length === cart.length && entries.every(x => canAdd(x.product))) {
          const currency = entries[0].product.currency || "USD";
          const amount = entries.reduce((sum, x) => sum + Number(x.product.price || 0) * x.item.quantity, 0);
          total.append(node("strong", "", "ESTIMATED TOTAL"), node("strong", "", money(amount, currency)));
          checkout.disabled = false;
        } else {
          total.append(node("span", "", "Review cart items before checkout."));
        }
      }
    }
    checkout.textContent = "SECURE CHECKOUT";
    note.textContent = "Your items are transferred to Fourthwall's secure checkout, where taxes and the final total are confirmed.";
  }
  function reconcileCart() {
    // Never erase saved purchases on a transient network failure.
    // Only remove items after a successful read of the current live catalog.
    const purchasableIds = new Set(products.filter(canAdd).map(p => p.id));
    const removedCount = cart.filter(item => !purchasableIds.has(item.id)).length;
    if (removedCount) {
      cart = cart.filter(item => purchasableIds.has(item.id));
      try { localStorage.setItem(key, JSON.stringify(cart)); } catch (_) {}
      cartNotice = removedCount === 1
        ? "An unpublished or deleted product was automatically removed from your cart."
        : "Unpublished or deleted products were automatically removed from your cart.";
    }
  }
  function changeQuantity(id, quantity) {
    const current = cart.find(i => i.id === id);
    if (!current) return;
    if (quantity <= 0) cart = cart.filter(i => i.id !== id);
    else current.quantity = quantity;
    saveCart();
  }
  function addToCart(p) {
    if (!catalogVerified || !canAdd(p)) return;
    cartNotice = "";
    const currency = p.currency || "USD";
    const currencyConflict = availableCart().some(x => (x.product.currency || "USD") !== currency);
    if (currencyConflict) {
      showCart();
      const message = node("p", "fw-cart-warning", "Please check out products in one currency at a time.");
      cartItems.prepend(message);
      return;
    }
    const match = cart.find(i => i.id === p.id);
    if (match) match.quantity = Math.min(99, match.quantity + 1);
    else cart.push({ id: p.id, quantity: 1 });
    saveCart();
    showCart();
  }
  // Official Fourthwall direct-products checkout works without any Storefront API token.
  // Keep the user's cart and quantities here, and use a single browser redirect to Fourthwall.
  const checkoutStatus = node("p", "fw-cart-warning");
  checkoutStatus.setAttribute("role", "status");
  checkoutStatus.hidden = true;
  footer.insertBefore(checkoutStatus, checkout);
  checkout.addEventListener("click", async () => {
    if (checkout.disabled) return;
    checkout.disabled = true;
    // Recheck immediately before redirect: never pass an unpublished or changed product to checkout.
    await refreshCatalog();
    if (!catalogVerified) return;
    const entries = availableCart();
    if (!entries.length || entries.length !== cart.length ||
        !entries.every(x => canAdd(x.product) && x.item.quantity >= 1 && x.item.quantity <= 99)) {
      renderCart();
      return;
    }
    const currencies = new Set(entries.map(x => x.product.currency || "USD"));
    if (currencies.size !== 1) {
      renderCart();
      return;
    }
    const url = new URL(shop + "/cart/checkout");
    url.searchParams.set("products", entries.map(x => x.product.variantId + ":" + x.item.quantity).join(","));
    url.searchParams.set("currency", entries[0].product.currency || "USD");
    window.location.assign(url.href);
  });


  // Product details remain on Simon Libon, rather than opening Fourthwall.
  const detail = node("div", "fw-product-overlay");
  detail.hidden = true;
  const detailShade = node("button", "fw-product-shade");
  detailShade.type = "button";
  detailShade.setAttribute("aria-label", "Close product details");
  const detailPanel = node("section", "fw-product-panel");
  detailPanel.setAttribute("role", "dialog");
  detailPanel.setAttribute("aria-modal", "true");
  detailPanel.setAttribute("aria-label", "Product details");
  const detailTop = node("div", "fw-product-top");
  const detailBack = node("button", "fw-product-back", "← BACK TO SHOP");
  detailBack.type = "button";
  detailTop.append(detailBack);
  const detailBody = node("div", "fw-product-body");
  detailPanel.append(detailTop, detailBody);
  detail.append(detailShade, detailPanel);
  document.body.append(detail);
  let detailReturn = null;
  function closeDetails() {
    detail.hidden = true;
    document.body.classList.remove("fw-product-visible");
    if (detailReturn && detailReturn.isConnected) detailReturn.focus();
  }
  function openDetails(p, origin) {
    detailReturn = origin;
    detailBody.replaceChildren();
    const cover = node("div", "fw-product-cover");
    if (p.image) {
      const img = node("img"); img.src = p.image; img.alt = "Cover artwork for " + p.name; cover.append(img);
    } else {
      cover.append(node("span", "fw-product-placeholder", "SIMON LIBON"));
    }
    const info = node("div", "fw-product-info");
    info.append(node("p", "fw-product-kicker", categories[category(p)] || "Digital release"),
      node("h2", "fw-product-name", p.name),
      node("p", "fw-product-price", typeof p.price === "number" ? money(p.price, p.currency) : "VIEW PRODUCT"));
    const description = (p.description || "").trim();
    if (description) info.append(node("p", "fw-product-description", description));
    if (canAdd(p)) {
      const add = node("button", "fw-product-add", "ADD TO CART");
      add.type = "button";
      add.addEventListener("click", () => { closeDetails(); addToCart(p); });
      info.append(add);
    } else {
      // Items with options require selecting the variant at Fourthwall.
      const go = node("a", "fw-product-add", "CHOOSE OPTIONS ON FOURTHWALL");
      go.href = p.url; go.rel = "noopener noreferrer";
      info.append(go);
    }
    const small = node("p", "fw-product-footnote", "Secure payment and digital delivery are handled by Fourthwall.");
    info.append(small);
    detailBody.append(cover, info);
    detail.hidden = false;
    document.body.classList.add("fw-product-visible");
    detailBack.focus();
  }
  detailShade.addEventListener("click", closeDetails);
  detailBack.addEventListener("click", closeDetails);
  document.addEventListener("keydown", e => {
    if (e.key === "Escape" && !detail.hidden) closeDetails();
  });

  function card(p) {
    const item = node("article", "shop-item");
    const imageLink = node("button", "shop-card-link fw-product-preview");
    imageLink.type = "button";
    imageLink.setAttribute("aria-label", "View " + p.name + " details on Simon Libon");
    imageLink.addEventListener("click", () => openDetails(p, imageLink));
    const photo = node("div", "shop-item-image");
    if (p.image) {
      const img = node("img"); img.src = p.image; img.alt = "Cover artwork for " + p.name; img.loading = "lazy"; photo.append(img);
    } else {
      photo.classList.add("is-placeholder");
      const placeholder = node("span", "placeholder-text", category(p) === "tabs" ? "GUITAR\nTABS" : category(p) === "backing" ? "BACKING\nTRACK" : "EP / ALBUM\nBUNDLE");
      placeholder.style.whiteSpace = "pre-line";
      photo.append(placeholder);
    }
    imageLink.append(photo); item.append(imageLink);
    const meta = node("div", "shop-item-meta"), detail = node("div");
    const titleButton = node("button", "fw-product-title", p.name);
    titleButton.type = "button";
    titleButton.addEventListener("click", () => openDetails(p, titleButton));
    const h = node("h3", "shop-item-title"); h.append(titleButton);
    detail.append(h, node("div", "shop-item-type", categories[category(p)]));
    meta.append(detail, node("span", "shop-item-price", typeof p.price === "number" ? money(p.price, p.currency) : "VIEW PRODUCT"));
    item.append(meta);
    const actions = node("div", "shop-item-actions");
    if (canAdd(p)) {
      const buy = node("button", "fw-add-to-cart", "ADD TO CART");
      buy.type = "button"; buy.addEventListener("click", () => addToCart(p)); actions.append(buy);
    } else {
      const view = node("button", "fw-add-to-cart", p.productType === "BUNDLE" ? "VIEW BUNDLE" : "VIEW DETAILS");
      view.type = "button";
      view.addEventListener("click", () => openDetails(p, view));
      actions.append(view);
    }
    item.append(actions);
    return item;
  }

  function render() {
    const q = search.value.trim().toLocaleLowerCase();
    const shown = products.filter(p => (active === "all" || category(p) === active) && p.name.toLocaleLowerCase().includes(q));
    shown.sort((a, b) => sort.value === "az" ? a.name.localeCompare(b.name) : sort.value === "za" ? b.name.localeCompare(a.name)
      : (String(b.createdAt).localeCompare(String(a.createdAt))) * (sort.value === "old" ? -1 : 1));
    grid.replaceChildren(...shown.map(card));
    empty.hidden = shown.length > 0;
    empty.querySelector("h3").textContent = products.length ? "NO MATCHES." : "COMING SOON.";
    empty.querySelector("p").textContent = products.length ? "Try a different search or category." : "Your published Fourthwall releases will appear here.";
    count.textContent = products.length + (products.length === 1 ? " RELEASE" : " RELEASES");
    filters.forEach(b => b.setAttribute("aria-pressed", String(b.dataset.shopFilter === active)));
    renderCart();
  }

  // Read Fourthwall directly when the public Storefront configuration is available.
  // The synchronized JSON file is a fallback for network/API failures.
  // This keeps newly published and unpublished products up to date on page load.
  async function getLiveCatalog() {
    const configResponse = await fetch("fourthwall-public-config.json", { cache: "no-store" });
    if (!configResponse.ok) throw new Error("Live catalog configuration unavailable");
    const config = await configResponse.json();
    const token = config && config.storefrontToken;
    if (typeof token !== "string" || !/^ptkn_[a-z0-9-]+$/i.test(token)) {
      throw new Error("Live catalog configuration invalid");
    }
    const raw = [];
    for (let page = 0; page < 100; page++) {
      const endpoint = new URL("https://storefront-api.fourthwall.com/v1/collections/all/products");
      endpoint.searchParams.set("storefront_token", token);
      endpoint.searchParams.set("page", String(page));
      endpoint.searchParams.set("size", "50");
      const response = await fetch(endpoint.href, { cache: "no-store" });
      if (!response.ok) throw new Error("Live catalog request unavailable");
      const data = await response.json();
      if (!data || !Array.isArray(data.results)) throw new Error("Unexpected live catalog response");
      raw.push(...data.results);
      if (!data.paging || !data.paging.hasNextPage) {
        return raw.filter(p => p && typeof p.slug === "string" && p.slug &&
          p.state && p.state.type === "AVAILABLE")
          .map(p => {
            const variants = Array.isArray(p.variants) ? p.variants : [];
            const isBundle = p.type === "BUNDLE";
            const price = (isBundle ? p.price : variants[0] && variants[0].unitPrice) || {};
            const cover = Array.isArray(p.images) ? p.images[0] : null;
            return {
              id: String(p.id || p.slug),
              name: String(p.name || p.slug),
              description: String(p.description || "").replace(/<[^>]*>/g, " ").replace(/\s+/g, " ").trim().slice(0, 1800),
              url: shop + "/products/" + encodeURIComponent(p.slug),
              image: cover && (cover.url || cover.src) || "",
              price: typeof price.value === "number" ? price.value : null,
              currency: price.currency || "EUR",
              createdAt: p.createdAt || "",
              productType: p.type || "PRODUCT",
              variantId: !isBundle && variants.length === 1 ? variants[0].id : null,
              variantCount: variants.length,
              available: p.state && p.state.type === "AVAILABLE"
            };
          });
      }
    }
    throw new Error("Live catalog pagination limit reached");
  }
  // Fourthwall is the source of truth: never show an old GitHub cache as if it were live.
  // This prevents deleted or unpublished products from reappearing after an API error.
  async function refreshCatalog() {
    if (catalogRefresh) return catalogRefresh;
    catalogVerified = false;
    catalogError = false;
    renderCart();
    catalogRefresh = (async () => {
      try {
        const fetched = await getLiveCatalog();
        products = fetched.filter(p =>
          typeof p.id === "string" && typeof p.name === "string" &&
          typeof p.url === "string" && p.url.startsWith(shop + "/products/") &&
          p.available === true
        );
        catalogVerified = true;
        catalogError = false;
        reconcileCart();
        if (!controlsReady) {
          search.disabled = false;
          sort.disabled = false;
          filters.forEach(button => {
            button.disabled = false;
            button.addEventListener("click", () => { active = button.dataset.shopFilter; render(); });
          });
          search.addEventListener("input", render);
          sort.addEventListener("change", render);
          controlsReady = true;
        }
        render();
      } catch (_) {
        catalogVerified = false;
        catalogError = true;
        products = [];
        grid.replaceChildren();
        empty.hidden = false;
        empty.querySelector("h3").textContent = "CATALOG UNAVAILABLE.";
        empty.querySelector("p").textContent =
          "Could not load current Fourthwall products. Please refresh and try again.";
        count.textContent = "RELEASES";
        renderCart();
      }
    })();
    try {
      await catalogRefresh;
    } finally {
      catalogRefresh = null;
    }
  }
  refreshCatalog();
  window.addEventListener("focus", () => refreshCatalog());
  document.addEventListener("visibilitychange", () => {
    if (!document.hidden) refreshCatalog();
  });
  window.addEventListener("storage", event => {
    if (event.key === key) {
      readCart();
      if (catalogVerified) reconcileCart();
      renderCart();
    }
  });
  // Also refresh if the user leaves the page open while editing products on Fourthwall.
  setInterval(() => { if (!document.hidden) refreshCatalog(); }, 120000);
  renderCart();
})();
