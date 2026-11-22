/* Shop view model: only real, published Gumroad products can be offered. */
(function () {
  "use strict";
  const safeUrl = function (value) {
    try {
      const u = new URL(value);
      return u.protocol === "https:" &&
        u.hostname === "simonlibonstore.gumroad.com" &&
        /^\/l\/[a-z0-9_-]+\/?$/i.test(u.pathname);
    } catch (_) { return false; }
  };
  const isLive = function (p) {
    // A published template is not a finished product; never promote placeholders.
    const title = String(p?.title || "");
    const template = /\[(?:song|ep|release)\s+title\]/i.test(title);
    return !!p && p.published === true && p.demo !== true &&
      !template && safeUrl(p.gumroadUrl);
  };
  const classify = function (p) {
    const title = String(p.title || "").toLowerCase();
    const ep = /\b(ep|album)\b/.test(title);
    const tab = /\b(tabs?|tablatures?)\b/.test(title);
    const backing = /\bbacking[\s-]*tracks?\b/.test(title);
    if (ep || (p.type === "bundle" && !(tab && backing && !ep))) return "bundle";
    if (tab && (backing || /\btabs?\s*(?:\+|&|and)\s*tracks?\b/.test(title))) return "pack";
    if (p.type === "pack" || p.type === "tabs" || p.type === "backing") return p.type;
    if (backing) return "backing";
    if (tab) return "tabs";
    return "digital";
  };
  const trackTitle = function (p) {
    if (typeof p.songTitle === "string" && p.songTitle.trim()) return p.songTitle.trim();
    const name = String(p.title || "").trim();
    const suffix = "(?:(?:official\\s+)?(?:guitar\\s+)?tabs?(?:\\s*\\(pdf\\))?|(?:guitar\\s+)?tablatures?|backing\\s*tracks?|(?:guitar\\s+)?tabs?\\s*(?:\\+|&|and)\\s*backing\\s*tracks?|tabs?\\s*(?:\\+|&|and)\\s*tracks?)";
    const modern = name.replace(/(?:\s*[-–—|:]\s*|\s+)tabs?\s*(?:\+|&|and)\s*tracks?\s*$/i, "").trim();
    if (modern !== name) return modern;
    const without = name.replace(new RegExp("(?:\\s*[-–—|:]\\s*|\\s+)" + suffix + "\\s*$", "i"), "").trim();
    return without || name;
  };
  const trackKey = function (title) {
    return title.normalize("NFKD").replace(/[\u0300-\u036f]/g, "")
      .toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
  };
  const order = { tabs: 0, pack: 1, backing: 2, digital: 3, bundle: 4 };
  const build = function (allProducts) {
    const bundles = [];
    const tracksMap = new Map();
    (Array.isArray(allProducts) ? allProducts : []).filter(isLive).forEach(function (p) {
      const kind = classify(p);
      // The storefront sells a tab or a tab+audio pack, never audio by itself.
      if (kind === "backing") return;
      if (kind === "bundle") {
        bundles.push({ kind: "bundle", id: p.id, title: p.title, options: [{ kind: "bundle", product: p }], image: p.image || "", thumbnail: p.thumbnail || p.image || "", date: p.releaseDate || "" });
        return;
      }
      const title = trackTitle(p);
      const key = trackKey(title) || ("product-" + String(p.id));
      if (!tracksMap.has(key)) {
        tracksMap.set(key, { kind: "track", key: key, title: title, options: [], image: "", thumbnail: "", date: "" });
      }
      const group = tracksMap.get(key);
      group.options.push({ kind: kind, product: p });
      if (!group.image && p.image) group.image = p.image;
      if (!group.thumbnail && p.thumbnail) group.thumbnail = p.thumbnail;
      if (String(p.releaseDate || "") > String(group.date || "")) group.date = p.releaseDate;
    });
    const tracks = [...tracksMap.values()];
    tracks.forEach(function (g) {
      g.options.sort(function (a, b) { return (order[a.kind] || 0) - (order[b.kind] || 0); });
    });
    return { bundles: bundles, tracks: tracks };
  };
  const checkout = function (product) {
    if (!isLive(product)) return "";
    // Gumroad officially supports a product URL plus ?wanted=true for direct checkout.
    // Use the creator's validated product URL instead of an undocumented checkout URL.
    const checkoutUrl = new URL(product.gumroadUrl);
    // Gumroad's zero-price products show €0+ (pay what you want). For those,
    // its checkout requires an explicit price before wanted=true can bypass
    // the intermediary landing page. Never override paid-product prices.
    if (Number(product.price) === 0) checkoutUrl.searchParams.set("price", "0");
    checkoutUrl.searchParams.set("wanted", "true");
    return checkoutUrl.href;
  };
  const productPage = function (product) {
    if (!isLive(product)) return "";
    // The documented Gumroad product URL opens the native Add to cart step;
    // it must NOT contain ?wanted=true, which skips straight to checkout.
    return new URL(product.gumroadUrl).href;
  };
  window.SIMON_SHOP_MODEL = { build: build, checkout: checkout, productPage: productPage, isLive: isLive };
})();
