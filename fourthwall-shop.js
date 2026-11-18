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
  footer.append(note, total, checkout, continueButton);
  panel.append(header, cartItems, footer);
  overlay.append(shade, panel);
  document.body.append(overlay);

  function showCart() {
    renderCart();
    overlay.hidden = false;
    document.body.classList.add("fw-cart-visible");
    closeButton.focus();
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
    const qty = cart.reduce((n, item) => n + item.quantity, 0);
    openButton.querySelector("[data-cart-count]").textContent = String(qty);
    cartItems.replaceChildren();
    total.replaceChildren();
    checkout.disabled = true;
    const staleCount = cart.length - entries.length;
    if (!cart.length) {
      cartItems.append(node("p", "fw-cart-empty", "Your cart is empty. Add a release to get started."));
    } else if (!products.length) {
      cartItems.append(node("p", "fw-cart-empty", "Loading your saved items…"));
    } else {
      if (staleCount) cartItems.append(node("p", "fw-cart-warning", "Some previously saved items are no longer available."));
      for (const { item, product: p } of entries) {
        const line = node("div", "fw-cart-line");
        if (p.image) {
          const img = node("img", "fw-cart-thumb"); img.src = p.image; img.alt = ""; img.loading = "lazy"; line.append(img);
        }
        const details = node("div", "fw-cart-line-copy");
        details.append(node("strong", "", p.name), node("small", "", money(Number(p.price || 0), p.currency)));
        const controls = node("div", "fw-cart-qty");
        const minus = node("button", "", "−"), plus = node("button", "", "+"), number = node("span", "", String(item.quantity));
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
      if (currencies.size === 1 && entries.length && !staleCount && entries.every(x => canAdd(x.product))) {
        const currency = entries[0].product.currency || "USD";
        const amount = entries.reduce((sum, x) => sum + Number(x.product.price || 0) * x.item.quantity, 0);
        total.append(node("strong", "", "ESTIMATED TOTAL"), node("strong", "", money(amount, currency)));
        checkout.disabled = false;
      } else {
        total.append(node("span", "", "Review cart items before checkout."));
      }
    }
    checkout.textContent = "SECURE CHECKOUT";
    note.textContent = "Your items are transferred to Fourthwall’s secure checkout, where taxes and the final total are confirmed.";
  }
  function changeQuantity(id, quantity) {
    const current = cart.find(i => i.id === id);
    if (!current) return;
    if (quantity <= 0) cart = cart.filter(i => i.id !== id);
    else current.quantity = quantity;
    saveCart();
  }
  function addToCart(p) {
    if (!canAdd(p)) return;
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
  // Fourthwall documents direct checkout by variant UUID and quantities.
  // No Storefront token or API-created cart is required for this entrypoint.
  const checkoutStatus = node("p", "fw-cart-warning");
  checkoutStatus.setAttribute("role", "status");
  checkoutStatus.hidden = true;
  footer.insertBefore(checkoutStatus, checkout);
  checkout.addEventListener("click", async () => {
    if (checkout.disabled) return;
    const entries = availableCart();
    if (!entries.length || entries.length !== cart.length ||
        !entries.every(x => canAdd(x.product) && x.item.quantity >= 1 && x.item.quantity <= 99)) return;
    const currencies = new Set(entries.map(x => x.product.currency || "USD"));
    if (currencies.size !== 1) return;
    const currency = entries[0].product.currency || "USD";
    checkout.disabled = true;
    checkout.textContent = "CONNECTING SECURE CHECKOUT…";
    checkoutStatus.hidden = true;
    try {
      // Create a real Fourthwall cart before opening their supported checkout URL.
      const cfgResponse = await fetch("fourthwall-public-config.json?v=" + Date.now(), { cache: "no-store" });
      if (!cfgResponse.ok) throw new Error("The store connection is still being prepared.");
      const cfg = await cfgResponse.json();
      if (!cfg || typeof cfg.storefrontToken !== "string" || !/^ptkn_[-a-zA-Z0-9]+$/.test(cfg.storefrontToken))
        throw new Error("The Fourthwall Storefront connection is unavailable.");
      const url = new URL("https://storefront-api.fourthwall.com/v1/carts");
      url.searchParams.set("storefront_token", cfg.storefrontToken);
      url.searchParams.set("currency", currency);
      const response = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          items: entries.map(x => ({ variantId: x.product.variantId, quantity: x.item.quantity }))
        }),
        cache: "no-store"
      });
      if (!response.ok) throw new Error("Fourthwall could not prepare this checkout.");
      const data = await response.json();
      if (!data || typeof data.id !== "string" || !data.id || data.id.length > 256)
        throw new Error("Fourthwall did not return a valid checkout cart.");
      const checkoutUrl = new URL(shop + "/checkout/");
      checkoutUrl.searchParams.set("cartId", data.id);
      checkoutUrl.searchParams.set("cartCurrency", currency);
      window.location.assign(checkoutUrl.href);
    } catch (error) {
      checkoutStatus.hidden = false;
      checkoutStatus.textContent = "The direct checkout could not be opened. " +
        (error instanceof Error ? error.message : "Please try again.") +
        " You can retry, or use the official Fourthwall payment page.";
      const fallback = document.createElement("a");
      fallback.href = entries.length === 1 ? entries[0].product.url : shop;
      fallback.textContent = " OPEN FOURTHWALL";
      fallback.style.marginLeft = "8px";
      fallback.style.textDecoration = "underline";
      checkoutStatus.append(fallback);
      checkout.disabled = false;
      checkout.textContent = "SECURE CHECKOUT";
    }
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

  fetch("fourthwall-products.json?v=" + Math.floor(Date.now() / 300000), { cache: "no-store" })
    .then(r => { if (!r.ok) throw Error("Catalog unavailable"); return r.json(); })
    .then(data => {
      products = Array.isArray(data.products) ? data.products.filter(p =>
        typeof p.id === "string" && typeof p.name === "string" &&
        typeof p.url === "string" && p.url.startsWith(shop + "/products/")
      ) : [];
      search.disabled = false; sort.disabled = false;
      filters.forEach(button => {
        button.disabled = false;
        button.addEventListener("click", () => { active = button.dataset.shopFilter; render(); });
      });
      search.addEventListener("input", render);
      sort.addEventListener("change", render);
      render();
    })
    .catch(() => {
      empty.hidden = false;
      empty.querySelector("p").textContent = "The Fourthwall catalog is temporarily unavailable. Gumroad is unaffected.";
      renderCart();
    });
  renderCart();
})();