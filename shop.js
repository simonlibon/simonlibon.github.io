(function () {
  "use strict";
  const model = window.SIMON_SHOP_MODEL;
  if (!model) return;
  const products = Array.isArray(window.SIMON_SHOP_CATALOG?.products) ? window.SIMON_SHOP_CATALOG.products : [];
  const grouped = model.build(products);
  const el = function (tag, cls, value) {
    const element = document.createElement(tag);
    if (cls) element.className = cls;
    if (value !== undefined) element.textContent = value;
    return element;
  };
  const euro = function (value) {
    return Number(value || 0).toLocaleString("en-IE", { style: "currency", currency: "EUR" });
  };
  function groupUrl(g) {
    return g.kind === "bundle" ? "product.html?id=" + encodeURIComponent(g.id) :
      "product.html?track=" + encodeURIComponent(g.key);
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
    const link = groupUrl(group);
    const cover = el("a", "shop-card-link");
    cover.href = link;
    cover.setAttribute("aria-label", "View " + group.title);
    cover.append(art(group));
    item.append(cover);

    const meta = el("div", "shop-item-meta");
    const info = el("div");
    const heading = el("h3", "shop-item-title");
    const title = el("a", null, group.title);
    title.href = link;
    heading.append(title);
    info.append(heading);
    info.append(el("div", "shop-item-type", group.kind === "bundle" ?
      "Complete collection" : "Guitar tabs & tracks"));
    meta.append(info);
    meta.append(el("span", "shop-item-price",
      (group.kind === "track" && group.options.length > 1 ? "FROM " : "") + euro(lowestPrice(group))));
    item.append(meta);

    const actions = el("div", "shop-item-actions");
    const action = el("a", "buy-quick", group.kind === "bundle" ? "VIEW BUNDLE" : "VIEW OPTIONS");
    action.href = link;
    actions.append(action);
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
