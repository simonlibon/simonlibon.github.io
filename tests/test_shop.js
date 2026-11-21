/* Safe, offline storefront tests. No API tokens, no orders, no product publishing. */
"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const modelFile = fs.readFileSync("shop-model.js", "utf8");
const sandbox = { window: {}, URL, URLSearchParams };
vm.runInNewContext(modelFile, sandbox, { filename: "shop-model.js" });
const model = sandbox.window.SIMON_SHOP_MODEL;
assert(model && typeof model.build === "function");

function product(id, title, type, price, published = true, url = "https://simonlibonstore.gumroad.com/l/" + id) {
  return { id, title, type, price, published, gumroadUrl: url, image: "" };
}
const catalog = [
  product("kinetic-tab", "Kinetic — Guitar Tab", "tabs", 5),
  product("kinetic-pack", "Kinetic — Guitar Tab + Backing Track", "pack", 9),
  product("dababy-tab", "Dababy — Guitar Tab", "tabs", 5),
  product("ep-bundle", "My EP — Complete EP Bundle", "bundle", 25),
  product("draft", "Sidechain — Guitar Tab", "tabs", 5, false),
  product("backing", "Dababy — Backing Track", "backing", 7),
  product("template", "[SONG TITLE] — Guitar Tab", "tabs", 5),
  product("evil", "Unsafe — Guitar Tab", "tabs", 5, true, "https://not-gumroad.example/l/evil")
];
const grouped = model.build(catalog);
assert.equal(grouped.bundles.length, 1, "exactly one EP bundle");
assert.equal(grouped.tracks.length, 2, "two songs, no unpublished/template/audio-only products");
const kinetic = grouped.tracks.find(x => x.title === "Kinetic");
assert(kinetic, "Kinetic grouped into one card");
assert.equal(kinetic.options.length, 2);
assert.equal(kinetic.options[0].kind, "tabs");
assert.equal(kinetic.options[1].kind, "pack");
assert.equal(kinetic.options[0].product.price, 5);
assert.equal(kinetic.options[1].product.price, 9);
assert.equal(grouped.tracks.find(x => x.title === "Dababy").options.length, 1);
assert(!model.isLive(catalog[4]), "draft cannot be purchased");
assert(!model.isLive(catalog[6]), "template cannot be purchased");
assert(!model.isLive(catalog[7]), "untrusted checkout host cannot be purchased");
assert.equal(model.checkout(catalog[4]), "", "draft has no checkout");
const checkout = new URL(model.checkout(catalog[1]));
assert.equal(checkout.hostname, "simonlibonstore.gumroad.com");
assert.equal(checkout.pathname, "/l/kinetic-pack");
assert.equal(checkout.searchParams.get("wanted"), "true");
assert.equal(checkout.searchParams.has("price"), false, "never preselect a price for paid products");
for (const slug of ["mmxjjd", "ntapzm", "jghmyd"]) {
  const free = product(slug, "TEST TRACK — Guitar Tab", "tabs", 0);
  const url = new URL(model.checkout(free));
  assert.equal(url.searchParams.get("price"), "0", "zero+ product must preselect free price");
  assert.equal(url.searchParams.get("wanted"), "true", "zero+ product should request direct checkout");
}
assert.equal(model.build([]).tracks.length, 0, "empty shop is safe");

const storePage = fs.readFileSync("tabs.html", "utf8");
const detailPage = fs.readFileSync("product.html", "utf8");
assert(storePage.includes('id="shop-bundle-grid"'));
assert(storePage.includes('id="shop-grid"'));
assert(storePage.includes('shop-model.js'));
assert(storePage.includes('shop.js'));
assert(detailPage.includes('product.js'));
assert(!detailPage.includes('id="product-add-to-cart"'), "No Add to cart on product page");
assert(!storePage.includes('class="shop-cart-link"'), "No cart shortcut in storefront");
assert(!detailPage.includes("ADD TO CART"), "Secondary cart action must be absent");
new vm.Script(fs.readFileSync("shop.js", "utf8"), { filename: "shop.js" });
new vm.Script(fs.readFileSync("product.js", "utf8"), { filename: "product.js" });
const shopScript = fs.readFileSync("shop.js", "utf8");
const productScript = fs.readFileSync("product.js", "utf8");
const gumroadProfile = fs.readFileSync("gumroad-site/profile.html", "utf8");
assert(shopScript.includes('get("demo") === "1"'), "Shop demo mode must be opt-in");
assert(shopScript.includes('const grouped = model.build(preview ? demoProducts : products)'), "Demo must not enter normal catalog");
assert(shopScript.includes('const gumroadMirror = window.location.hostname === "simonlibonstore.gumroad.com"'), "Shop must detect Gumroad mirror");
assert(shopScript.includes('group.options.forEach(function (option) {'), "Gumroad shop must expose each real format");
assert(shopScript.includes('if (!option || !model.isLive(option.product) || (preview && !demoCheckoutOpen)) return ""'), "Expired Gumroad previews must not sell");
assert(storePage.includes("shop.js?v=direct-gumroad-checkout-3"), "Browser cache must not serve the old Gumroad shop implementation");
assert(productScript.includes('DEMO ONLY — NOT FOR SALE'), "Demo detail must disable checkout");
assert(productScript.includes('buy.removeAttribute("href")'), "Demo detail must not retain checkout URLs");
assert(!productScript.includes('https://gumroad.com/js/gumroad.js'), "Gumroad overlay must not load");
assert(gumroadProfile.includes('var isDemo=new URLSearchParams(location.search).get("demo")==="1"'), "Gumroad demo mode must be opt-in");
assert(gumroadProfile.includes('if(!isDemo||demoCheckoutOpen){a.href='), "Gumroad demo checkout is open only during an explicit temporary window");
assert(gumroadProfile.includes('2026-11-21T01:49:00+01:00'), "Gumroad demo must expire");
assert(productScript.includes('const testPermalinks = new Set(["mmxjjd", "ntapzm", "jghmyd"])'), "Only three approved products can checkout");
assert(productScript.includes('if (preview && !approvedDemo)'), "Expired or unapproved demo must disable checkout");
assert(productScript.includes('2026-11-21T01:49:00+01:00'), "Product demo must expire");
console.log("Storefront tests passed: grouping, drafts, checkout links, limited free demo checkout, expiry, page references.");
