(function(){
"use strict";
const list=Array.isArray(window.SIMON_SHOP_CATALOG?.products)?window.SIMON_SHOP_CATALOG.products:[];
const names={tabs:"Guitar tabs",backing:"Backing tracks",bundle:"Bundles"};
const titles={tabs:"GUITAR\nTABS",backing:"BACKING\nTRACK",bundle:"EP / ALBUM\nBUNDLE"};
const arrow='<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12h14m-6-6 6 6-6 6"/></svg>';
const el=(tag,cls,text)=>{const e=document.createElement(tag);if(cls)e.className=cls;if(text!==undefined)e.textContent=text;return e};
const euro=n=>Number(n||0).toLocaleString("en-IE",{style:"currency",currency:"EUR"});
const good=u=>{try{const x=new URL(u);return x.protocol==="https:"&&x.hostname==="simonlibonstore.gumroad.com"&&/^\/l\/[a-z0-9_-]+\/?$/i.test(x.pathname)}catch{return false}};
const canPurchase=p=>!p?.demo&&good(p?.gumroadUrl);
const live=p=>p?.published===true&&(p.demo===true||canPurchase(p));
const pay=p=>{const u=new URL(p.gumroadUrl);u.searchParams.set("wanted","true");return u.href};
function art(p,cls){const box=el("div",cls),uri=String(p.image||"");if(uri&&(/^(https?:\/\/|data:image\/(png|jpeg|webp);base64,)/i.test(uri)||/^images\//i.test(uri))){const img=el("img");img.src=uri;img.alt="Cover artwork for "+p.title;img.loading="lazy";box.append(img)}else{box.classList.add("is-placeholder");const text=el("span","placeholder-text",titles[p.type]||"SIMON\nLIBON");text.style.whiteSpace="pre-line";box.append(text)}return box}
function card(p){
 const item=el("article","shop-item"), purchasable=canPurchase(p),url=purchasable?pay(p):"";
 const cover=el(purchasable?"a":"div",purchasable?"shop-card-link":"shop-card-preview");
 if(purchasable){
   cover.href=url;
   cover.rel="noopener noreferrer";
   cover.target="_blank";
   cover.setAttribute("aria-label","Buy "+p.title+" securely through Gumroad");
 }
 cover.append(art(p,"shop-item-image"));
 item.append(cover);
 const meta=el("div","shop-item-meta"),info=el("div");
 info.append(el("h3","shop-item-title",p.title),el("div","shop-item-type",names[p.type]||"Digital release"));
 meta.append(info,el("span","shop-item-price",p.demo?"DEMO":euro(p.price)));
 item.append(meta);
 const actions=el("div","shop-item-actions");
 if(purchasable){
   const buy=el("a","buy-quick","BUY ON GUMROAD");
   buy.href=url;
   buy.rel="noopener noreferrer";
   buy.target="_blank";
   buy.insertAdjacentHTML("beforeend",arrow);
   actions.append(buy);
 } else {
   actions.append(el("span","shop-item-type","DEMO · NOT FOR SALE"));
 }
 item.append(actions);
 return item;
}
function catalogue(){const grid=document.getElementById("shop-grid");if(!grid)return;const search=document.getElementById("shop-search-input"),sort=document.getElementById("shop-sort-select"),empty=document.getElementById("shop-empty"),count=document.getElementById("shop-count"),filterButtons=[...document.querySelectorAll("[data-shop-filter]")],coll=new Intl.Collator("en",{sensitivity:"base",numeric:true}),all=list.filter(live);let active="all";
function render(){const q=search.value.trim().toLocaleLowerCase();const filtered=all.filter(p=>(active==="all"||p.type===active)&&(!q||(p.title+" "+p.description+" "+(names[p.type]||"")).toLocaleLowerCase().includes(q)));const order=sort.value;filtered.sort((a,b)=>order==="az"?coll.compare(a.title,b.title):order==="za"?coll.compare(b.title,a.title):((new Date(b.releaseDate).getTime()||0)-(new Date(a.releaseDate).getTime()||0))*(order==="new"?1:-1));grid.replaceChildren(...filtered.map(card));empty.hidden=filtered.length>0;empty.querySelector("h3").textContent=all.length?"NO MATCHES.":"COMING SOON.";empty.querySelector("p").textContent=all.length?"Try a different search or category.":"Official tabs, backing tracks and bundles will appear here when released.";count.textContent=all.length+" "+(all.length===1?"RELEASE":"RELEASES");filterButtons.forEach(b=>b.setAttribute("aria-pressed",String(b.dataset.shopFilter===active)))}
filterButtons.forEach(b=>b.addEventListener("click",()=>{active=b.dataset.shopFilter;render()}));document.querySelectorAll("[data-shop-category]").forEach(b=>b.addEventListener("click",()=>{active=b.dataset.shopCategory;render();document.getElementById("shop-catalog").scrollIntoView({behavior:"smooth"})}));search.addEventListener("input",render);sort.addEventListener("change",render);render()}
if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",()=>{catalogue()});else{catalogue()}
})();