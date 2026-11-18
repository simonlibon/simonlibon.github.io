(function(){
"use strict";
const grid=document.getElementById("shop-grid"),count=document.getElementById("shop-count"),
empty=document.getElementById("shop-empty"),search=document.getElementById("shop-search-input"),
sort=document.getElementById("shop-sort-select"),filters=[...document.querySelectorAll("[data-shop-filter]")];
if(!grid||!count||!empty||!search||!sort)return;
let products=[],active="all";
const names={tabs:"Guitar tabs",backing:"Backing tracks",bundle:"Bundles"};
const category=p=>/bundle|pack|ep complete|ep full/i.test(p.name)?"bundle":/backing|track|instrumental/i.test(p.name)?"backing":"tabs";
const el=(tag,className,content)=>{const e=document.createElement(tag);if(className)e.className=className;if(content!==undefined)e.textContent=content;return e;};
const price=p=>typeof p.price==="number"?new Intl.NumberFormat("en-IE",{style:"currency",currency:p.currency||"USD"}).format(p.price):"VIEW PRODUCT";
function card(p){
  const item=el("article","shop-item"),photoLink=el("a","shop-card-link");
  photoLink.href=p.url;photoLink.target="_blank";photoLink.rel="noopener noreferrer";
  photoLink.setAttribute("aria-label","View "+p.name+" on Fourthwall");
  const photo=el("div","shop-item-image");
  if(p.image){
    const img=el("img");img.src=p.image;img.alt="Cover artwork for "+p.name;img.loading="lazy";photo.append(img);
  }else{
    photo.classList.add("is-placeholder");
    photo.append(el("span","placeholder-text",category(p)==="tabs"?"GUITAR\nTABS":category(p)==="backing"?"BACKING\nTRACK":"EP / ALBUM\nBUNDLE"));
    photo.style.whiteSpace="pre-line";
  }
  photoLink.append(photo);item.append(photoLink);
  const meta=el("div","shop-item-meta"),info=el("div");
  info.append(el("h3","shop-item-title",p.name),el("div","shop-item-type",names[category(p)]));
  meta.append(info,el("span","shop-item-price",price(p)));item.append(meta);
  const actions=el("div","shop-item-actions"),buy=el("a","buy-quick","VIEW ON FOURTHWALL");
  buy.href=p.url;buy.target="_blank";buy.rel="noopener noreferrer";
  actions.append(buy);item.append(actions);
  return item;
}
function render(){
 const q=search.value.trim().toLocaleLowerCase();
 const shown=products.filter(p=>(active==="all"||category(p)===active)&&p.name.toLocaleLowerCase().includes(q));
 shown.sort((a,b)=>sort.value==="az"?a.name.localeCompare(b.name):sort.value==="za"?b.name.localeCompare(a.name):sort.value==="old"?String(a.createdAt).localeCompare(String(b.createdAt)):String(b.createdAt).localeCompare(String(a.createdAt)));
 grid.replaceChildren(...shown.map(card));empty.hidden=shown.length>0;
 empty.querySelector("h3").textContent=products.length?"NO MATCHES.":"COMING SOON.";
 empty.querySelector("p").textContent=products.length?"Try a different search or category.":"Fourthwall products will appear here when published.";
 count.textContent=products.length+" "+(products.length===1?"RELEASE":"RELEASES");
 filters.forEach(btn=>btn.setAttribute("aria-pressed",String(btn.dataset.shopFilter===active)));
}
fetch("fourthwall-products.json?v="+Math.floor(Date.now()/300000),{cache:"no-store"})
.then(r=>{if(!r.ok)throw new Error("Catalog not available");return r.json()})
.then(data=>{
 products=Array.isArray(data.products)?data.products.filter(p=>typeof p.name==="string"&&/^https:\/\/simon-libon-music-shop\.fourthwall\.com\/products\//.test(p.url)): [];
 search.disabled=false;sort.disabled=false;
 filters.forEach(btn=>{btn.disabled=false;btn.addEventListener("click",()=>{active=btn.dataset.shopFilter;render()})});
 search.addEventListener("input",render);sort.addEventListener("change",render);render();
}).catch(()=>{empty.hidden=false;empty.querySelector("p").textContent="The Fourthwall catalog is temporarily unavailable. Your Gumroad shop is unaffected.";});
})();
