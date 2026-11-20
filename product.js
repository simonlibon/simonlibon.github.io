/* Track detail and checkout: every option is a separate, published Gumroad product. */
(function () {
  "use strict";
  const el = function (tag, cls, value) {
    const result = document.createElement(tag);
    if (cls) result.className = cls;
    if (value !== undefined) result.textContent = value;
    return result;
  };
  const euro = function (n) {
    return Number(n || 0).toLocaleString("en-IE", { style: "currency", currency: "EUR" });
  };
  const labels = {
    tabs: "Guitar Tab (PDF)",
    pack: "Tab + Backing Track",
    backing: "Backing Track",
    digital: "Digital Download",
    bundle: "Complete EP Bundle"
  };
  function showError() {
    document.getElementById("product-error").hidden = false;
    document.getElementById("product-layout").hidden = true;
  }
  function load(src, callback) {
    const script = document.createElement("script");
    script.src = src;
    script.onload = callback;
    script.onerror = showError;
    document.body.append(script);
  }
  function render() {
    const model = window.SIMON_SHOP_MODEL;
    if (!model) return showError();
    const products = Array.isArray(window.SIMON_SHOP_CATALOG?.products) ? window.SIMON_SHOP_CATALOG.products : [];
    const grouped = model.build(products);
    const params = new URLSearchParams(location.search);
    const id = params.get("id");
    const track = params.get("track");
    let group;
    if (track) group = grouped.tracks.find(function (g) { return g.key === track; });
    else if (id) {
      group = grouped.bundles.find(function (g) { return String(g.id) === id; }) ||
        grouped.tracks.find(function (g) {
          return g.options.some(function (o) { return String(o.product.id) === id; });
        });
    }
    if (!group || !group.options.length) return showError();

    document.title = group.title + " | Simon Libon";
    document.getElementById("product-title").textContent = group.title;
    document.getElementById("product-type").textContent =
      group.kind === "bundle" ? "EP COLLECTION" : "INDIVIDUAL TRACK";
    const cover = document.getElementById("product-cover");
    if (typeof group.image === "string" && /^https:\/\//i.test(group.image)) {
      const img = el("img");
      img.src = group.image;
      img.alt = "Cover art for " + group.title;
      cover.append(img);
    } else {
      cover.textContent = group.title;
    }

    const options = group.options;
    const buy = document.getElementById("product-buy");
    const price = document.getElementById("product-price");
    const description = document.getElementById("product-description");
    const includedSection = document.getElementById("product-included-section");
    const includedList = document.getElementById("product-included");
    let optionsField;
    function select(option) {
      const product = option.product;
      const checkoutUrl = model.checkout(product);
      if (!checkoutUrl) return showError();
      buy.href = checkoutUrl;
      price.textContent = euro(product.price);
      description.textContent = product.description ||
        "Official digital download by Simon Libon.";
      includedList.replaceChildren();
      const included = Array.isArray(product.includes) ? product.includes : [];
      included.forEach(function (value) {
        includedList.append(el("li", null, String(value)));
      });
      includedSection.hidden = included.length === 0;
      if (optionsField) {
        optionsField.querySelectorAll(".shop-option").forEach(function (label) {
          label.classList.toggle("selected", label.querySelector("input").checked);
        });
      }
    }

    if (options.length > 1) {
      optionsField = el("fieldset", "shop-purchase-options");
      optionsField.append(el("legend", null, "CHOOSE YOUR DOWNLOAD"));
      options.forEach(function (option, index) {
        const label = el("label", "shop-option");
        const input = el("input");
        input.type = "radio";
        input.name = "shop-purchase-option";
        input.value = String(index);
        input.checked = false;
        const name = el("span", "shop-option-name", labels[option.kind] || "Digital Download");
        const amount = el("strong", "shop-option-price", euro(option.product.price));
        label.append(input, name, amount);
        optionsField.append(label);
        input.addEventListener("change", function () {
          if (input.checked) select(option);
        });
      });
      price.after(optionsField);
    }
    // Prefer the complete pack when it is genuinely on sale. Never synthesize one.
    const preferred = options.find(function (o) { return o.kind === "pack"; }) ||
      options.find(function (o) { return o.kind === "tabs"; }) || options[0];
    if (optionsField) {
      const index = options.indexOf(preferred);
      optionsField.querySelectorAll("input")[index].checked = true;
    }
    select(preferred);
    document.getElementById("product-layout").hidden = false;
  }
  load("catalog.js?refresh=" + Date.now(), function () {
    load("shop-model.js?v=1", render);
  });
})();
