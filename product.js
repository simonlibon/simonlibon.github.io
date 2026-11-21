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
    const preview = new URLSearchParams(location.search).get("demo") === "1";
    // Checkout is only unlocked for the three known test products until cleanup time.
    const demoCheckoutOpen = preview && Date.now() < Date.parse("2026-11-21T01:49:00+01:00");
    const testPermalinks = new Set(["mmxjjd", "ntapzm", "jghmyd"]);
    const products = Array.isArray(window.SIMON_SHOP_CATALOG?.products) ? window.SIMON_SHOP_CATALOG.products : [];
    const demoProducts = preview ? [
      {id:"demo-tab",title:"DEMO TRACK — Guitar Tab",type:"tabs",published:true,
        price:0,description:"Temporary free demo: a synthetic guitar tab PDF, not a real release.",releaseDate:"2026-11-21",
        image:"https://public-files.gumroad.com/463u26tobg7hzzc4czodqg7a0osl",
        gumroadUrl:"https://simonlibonstore.gumroad.com/l/mmxjjd",includes:["Guitar tab (PDF)"]},
      {id:"demo-pack",title:"DEMO TRACK — Guitar Tab + Backing Track",type:"pack",published:true,
        price:0,description:"Temporary free demo: synthetic guitar tab PDF and backing WAV.",releaseDate:"2026-11-21",
        image:"https://public-files.gumroad.com/me05sdxis06xvgyy5vlmgye8mqiu",
        gumroadUrl:"https://simonlibonstore.gumroad.com/l/ntapzm",includes:["Guitar tab (PDF)","Backing track (WAV)"]},
      {id:"demo-ep",title:"DEMO EP — Complete EP Bundle",type:"bundle",published:true,
        price:0,description:"Temporary free demo bundle: one synthetic PDF and one WAV, not a full EP.",releaseDate:"2026-11-21",
        image:"https://public-files.gumroad.com/n4sgr37s19z2py5nkrg0rnwlb5ys",
        gumroadUrl:"https://simonlibonstore.gumroad.com/l/jghmyd",includes:["Visual demonstration only"]}
    ] : [];
    const grouped = model.build(preview ? demoProducts : products);
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

    document.title = group.title + (preview ? " — PREVIEW" : "") + " | Simon Libon";
    if (preview) {
      const back = document.querySelector(".back-to-shop");
      if (back) back.href = "tabs.html?demo=1";
      const payment = document.querySelector(".sl-payment-copy");
      if (payment) payment.textContent = demoCheckoutOpen ? "TEMPORARY FREE TEST — Gumroad handles the order and downloads. No official music is included." : "VISUAL DEMONSTRATION — CHECKOUT DISABLED";
    }
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
      const approvedDemo = demoCheckoutOpen && testPermalinks.has(new URL(product.gumroadUrl).pathname.split("/").pop());
      if (preview && !approvedDemo) {
        buy.removeAttribute("href");
        buy.removeAttribute("target");
        buy.textContent = "DEMO ONLY — NOT FOR SALE";
        buy.setAttribute("aria-disabled", "true");
        buy.style.pointerEvents = "none";
        buy.style.opacity = ".55";
      } else {
        buy.href = checkoutUrl;
        if (preview && approvedDemo) {
          buy.textContent = "FREE TEST CHECKOUT · GUMROAD";
          buy.removeAttribute("aria-disabled");
          buy.style.pointerEvents = "";
          buy.style.opacity = "";
        }
      }
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
    // Deep links containing a SKU keep that choice selected, including after
    // browser Back/Forward; the canonical track URL defaults to the pack.
    const preferred = (id && options.find(function (o) {
      return String(o.product.id) === String(id);
    })) || options.find(function (o) { return o.kind === "pack"; }) ||
      options.find(function (o) { return o.kind === "tabs"; }) || options[0];
    if (optionsField) {
      const index = options.indexOf(preferred);
      optionsField.querySelectorAll("input")[index].checked = true;
    }
    select(preferred);
    document.getElementById("product-layout").hidden = false;
  }
  load("catalog.js?refresh=" + Date.now(), function () {
    load("shop-model.js?v=direct-checkout-20261121", render);
  });
})();
