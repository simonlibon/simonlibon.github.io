(function () {
  "use strict";
  const model = window.SIMON_SHOP_MODEL;
  if (!model) return;
  const preview = new URLSearchParams(window.location.search).get("demo") === "1";
  // The explicit demo checkout is temporary and expires independently of the catalogue.
  const demoCheckoutOpen = preview && Date.now() < Date.parse("2026-11-21T01:49:00+01:00");
  const products = Array.isArray(window.SIMON_SHOP_CATALOG?.products) ? window.SIMON_SHOP_CATALOG.products : [];
  // A visual-only demonstration; the mock products never enter the real catalog.
  const demoProducts = preview ? [
    {id:"demo-tab",title:"DEMO TRACK — Guitar Tab",type:"tabs",published:true,
      price:0,description:"Free checkout test with synthetic PDF. Not an official release.",releaseDate:"2026-11-21",
      image:"https://public-files.gumroad.com/463u26tobg7hzzc4czodqg7a0osl",
      gumroadUrl:"https://simonlibonstore.gumroad.com/l/mmxjjd",includes:["Guitar tab (PDF)"]},
    {id:"demo-pack",title:"DEMO TRACK — Guitar Tab + Backing Track",type:"pack",published:true,
      price:0,description:"Free checkout test with synthetic PDF and WAV. Not an official release.",releaseDate:"2026-11-21",
      image:"https://public-files.gumroad.com/me05sdxis06xvgyy5vlmgye8mqiu",
      gumroadUrl:"https://simonlibonstore.gumroad.com/l/ntapzm",includes:["Guitar tab (PDF)","Backing track (WAV)"]},
    {id:"demo-ep",title:"DEMO EP — Complete EP Bundle",type:"bundle",published:true,
      price:0,description:"Free bundle checkout test; includes one demo PDF and WAV, not an actual EP.",releaseDate:"2026-11-21",
      image:"https://public-files.gumroad.com/n4sgr37s19z2py5nkrg0rnwlb5ys",
      gumroadUrl:"https://simonlibonstore.gumroad.com/l/jghmyd",includes:["Visual demonstration only"]}
  ] : [];
  const grouped = model.build(preview ? demoProducts : products);
  const el = function (tag, cls, value) {
    const element = document.createElement(tag);
    if (cls) element.className = cls;
    if (value !== undefined) element.textContent = value;
    return element;
  };
  const euro = function (value) {
    return Number(value || 0).toLocaleString("en-IE", { style: "currency", currency: "EUR" });
  };
  const gumroadMirror = window.location.hostname === "simonlibonstore.gumroad.com";
  function gumroadCheckout(option) {
    if (!option || !model.isLive(option.product) || (preview && !demoCheckoutOpen)) return "";
    return model.checkout(option.product);
  }
  function groupUrl(g) {
    // On the Gumroad-hosted shop, a card opens checkout directly. The official
    // website retains its own styled product detail / format selector.
    if (gumroadMirror) {
      const option = g.kind === "bundle" ? g.options[0] :
        (g.options.find(function (o) { return o.kind === "pack"; }) || g.options[0]);
      return gumroadCheckout(option);
    }
    const query = preview ? "demo=1&" : "";
    return g.kind === "bundle" ? "product.html?" + query + "id=" + encodeURIComponent(g.id) :
      "product.html?" + query + "track=" + encodeURIComponent(g.key);
  }
  function art(group) {
    const container = el("div", "shop-item-image");
    const uri = String(group.image || "");
    if (/^https:\/\//i.test(uri)) {
      const img = el("img");
      img.src = uri;
      img.alt = "Cover artwork for " + group.title;
      img.loading = "lazy";
      container.append(img);
    } else {
      container.classList.add("is-placeholder");
      container.append(el("span", "placeholder-text", "SIMON\nLIBON"));
      container.querySelector("span").style.whiteSpace = "pre-line";
    }
    return container;
  }
  function lowestPrice(g) {
    return Math.min.apply(null, g.options.map(function (x) { return Number(x.product.price || 0); }));
  }
  function card(group) {
    const item = el("article", "shop-item");
    if (preview) item.classList.add("is-demo");
    const link = groupUrl(group);
    const cover = el("a", "shop-card-link");
    if (link) cover.href = link;
    else cover.setAttribute("aria-disabled", "true");
    cover.setAttribute("aria-label", (gumroadMirror ? "Checkout: " : "View ") + group.title);
    cover.append(art(group));
    item.append(cover);

    const meta = el("div", "shop-item-meta");
    const info = el("div");
    const heading = el("h3", "shop-item-title");
    const title = el("a", null, group.title);
    if (link) title.href = link;
    else title.setAttribute("aria-disabled", "true");
    heading.append(title);
    info.append(heading);
    info.append(el("div", "shop-item-type", group.kind === "bundle" ?
      "Complete collection" : "Guitar tabs & tracks"));
    meta.append(info);
    meta.append(el("span", "shop-item-price",
      (group.kind === "track" && group.options.length > 1 ? "FROM " : "") + euro(lowestPrice(group))));
    item.append(meta);

    const actions = el("div", "shop-item-actions");
    if (gumroadMirror) {
      // Offer every real format as a direct Gumroad checkout, never a second
      // product page. For two formats there are two distinct payment links.
      const labels = { tabs: "GUITAR TAB", pack: "TAB + TRACK", bundle: "BUY BUNDLE" };
      group.options.forEach(function (option) {
        const action = el("a", "buy-quick", labels[option.kind] || "BUY NOW");
        const href = gumroadCheckout(option);
        if (href) action.href = href;
        else action.setAttribute("aria-disabled", "true");
        actions.append(action);
      });
    } else {
      const action = el("a", "buy-quick", group.kind === "bundle" ? "VIEW BUNDLE" : "VIEW OPTIONS");
      action.href = link;
      actions.append(action);
    }
    item.append(actions);
    return item;
  }
  const sortGroups = function (groups, sortValue) {
    const coll = new Intl.Collator("en", { sensitivity: "base", numeric: true });
    groups.sort(function (a, b) {
      if (sortValue === "az") return coll.compare(a.title, b.title);
      if (sortValue === "za") return coll.compare(b.title, a.title);
      const diff = String(b.date || "").localeCompare(String(a.date || ""));
      return (diff || coll.compare(a.title, b.title)) * (sortValue === "old" ? -1 : 1);
    });
    return groups;
  };
  function initShop() {
    const search = document.getElementById("shop-search-input");
    if (preview) {
      const section = document.getElementById("shop-catalog");
      if (section) section.insertBefore(el("p", "shop-demo-note", demoCheckoutOpen ? "TEMPORARY FREE CHECKOUT TEST — NO OFFICIAL MUSIC IS ON SALE" : "VISUAL PREVIEW ONLY — CHECKOUT TEST HAS ENDED"), section.querySelector(".shop-catalog-actions")?.parentElement?.nextSibling || section.firstChild);
    }
    const sort = document.getElementById("shop-sort-select");
    const grid = document.getElementById("shop-grid");
    const bundlesGrid = document.getElementById("shop-bundle-grid");
    const bundleSection = document.getElementById("shop-ep-section");
    const trackHeading = document.getElementById("shop-track-heading");
    const empty = document.getElementById("shop-empty");
    const count = document.getElementById("shop-count");
    if (!search || !sort || !grid || !bundlesGrid || !bundleSection || !trackHeading || !empty || !count) return;

    function matches(g, q) {
      return !q || (g.title + " " + g.options.map(function (option) {
        return String(option.product.description || "");
      }).join(" ")).toLocaleLowerCase().includes(q);
    }
    function render() {
      const query = search.value.trim().toLocaleLowerCase();
      const order = sort.value;
      const bundles = sortGroups(grouped.bundles.filter(function (g) { return matches(g, query); }), order);
      const tracks = sortGroups(grouped.tracks.filter(function (g) { return matches(g, query); }), order);
      bundlesGrid.replaceChildren(...bundles.map(card));
      grid.replaceChildren(...tracks.map(card));
      bundleSection.hidden = bundles.length === 0;
      trackHeading.hidden = tracks.length === 0;
      const overall = grouped.bundles.length + grouped.tracks.length;
      empty.hidden = (bundles.length + tracks.length) > 0;
      empty.querySelector("h3").textContent = overall ? "NO MATCHES." : "COMING SOON.";
      empty.querySelector("p").textContent = overall ?
        "Try a different search." :
        "Official tabs, backing tracks and EP bundles will appear here when released.";
      count.textContent = overall + " " + (overall === 1 ? "RELEASE" : "RELEASES");
    }
    search.addEventListener("input", render);
    sort.addEventListener("change", render);
    render();
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", initShop);
  else initShop();
})();
