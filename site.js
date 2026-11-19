/* CUSTOMIZE YOUR SITE HERE. Leave links empty until they are real. */
const SITE={
  // Optional: add your own HTTPS photo URL; shown faintly behind your name.
  homePhoto:'',
  release:{title:'',coverImage:'',listenUrl:''},
  featuredVideo:{youtubeId:'',title:''},
  links:{youtube:'https://www.youtube.com/@simonlibon',instagram:'https://www.instagram.com/simon.libon/',tiktok:'https://www.tiktok.com/@simonlibon.music',facebook:'https://www.facebook.com/profile.php?id=100070692266151',spotify:'',appleMusic:'',youtubeMusic:'',bandcamp:'',email:'simonlibon.music@gmail.com'},
  shows:[],
  products:[]
};
const goodUrl = v => {try{let u=new URL(v);return u.protocol==='https:'}catch{return false}};
const safe = v => String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const toast = msg => {let n=document.querySelector('.toast');if(!n){n=document.createElement('div');n.className='toast';n.setAttribute('role','status');document.body.appendChild(n)}n.textContent=msg;n.classList.add('show');clearTimeout(window.__toastTimer);window.__toastTimer=setTimeout(()=>n.classList.remove('show'),2600)};
function target(kind){let v=SITE.links[kind];if(kind==='email' && /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v||'')){location.href='mailto:'+v;return}if(goodUrl(v)){window.location.assign(v);return}toast('Link coming soon')}
function initLinks(){
  document.querySelectorAll('[data-link]').forEach(node=>{
    const key=node.dataset.link;
    const value=SITE.links[key];
    const isEmail=key==='email' && /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value||'');
    if(isEmail){node.href='mailto:'+value;return}
    if(goodUrl(value)){
      node.href=value;
      node.removeAttribute('target');
      node.rel='noopener noreferrer';
      node.classList.remove('inactive');
      return;
    }
    node.classList.add('inactive');
    node.removeAttribute('href');
    node.setAttribute('aria-disabled','true');
  });
}
function initRelease(){const r=SITE.release;document.querySelectorAll('[data-release-title]').forEach(n=>{if(r.title)n.textContent=r.title});if(goodUrl(r.coverImage)){document.querySelectorAll('[data-release-cover]').forEach(n=>{n.innerHTML='';const img=document.createElement('img');img.src=r.coverImage;img.alt=r.title?`${r.title} artwork`:'Release artwork';img.loading='lazy';n.append(img)})}if(goodUrl(r.listenUrl)){document.querySelectorAll('[data-listen]').forEach(n=>{n.href=r.listenUrl;n.removeAttribute('target');n.rel='noopener noreferrer';n.textContent='LISTEN ↗'})}}
function initVideo(){const v=SITE.featuredVideo;if(v.title)document.querySelectorAll('[data-video-title]').forEach(n=>n.textContent=v.title);if(!/^[A-Za-z0-9_-]{11}$/.test(v.youtubeId||''))return;document.querySelectorAll('[data-video-player]').forEach(n=>{n.innerHTML='';let f=document.createElement('iframe');f.src='https://www.youtube-nocookie.com/embed/'+v.youtubeId;f.title='Simon Libon guitar video';f.allow='accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture; web-share';f.referrerPolicy='strict-origin-when-cross-origin';f.allowFullscreen=true;n.append(f)})}
let filter='all';function renderProducts(){let node=document.querySelector('[data-products]');if(!node)return;let mode=document.body.dataset.page;const visible=SITE.products.filter(p=>(mode==='merch'?p.type==='merch':p.type!=='merch')&&(filter==='all'||p.type===filter));node.innerHTML=visible.map(p=>{const live=goodUrl(p.url);const type=p.type==='tabs'?'TAB':p.type==='backing'?'WAV':'S/L';return `<article class="product"><div class="product-art ${safe(p.type)}"><span class="stub ${safe(p.type==='tabs'?'tab':p.type)}">${type}</span></div><div class="product-meta"><div><h3>${safe(p.title)}</h3><span>${live?(p.price?safe(p.price):'AVAILABLE'):'COMING SOON'}</span></div><button type="button" data-buy="${safe(p.id)}" ${live?'':'disabled'}>${live?'BUY ↗':'SOON'}</button></div></article>`}).join('');node.querySelectorAll('[data-buy]').forEach(b=>b.addEventListener('click',()=>{const p=SITE.products.find(p=>p.id===b.dataset.buy);if(p&&goodUrl(p.url))window.open(p.url,'_blank','noopener,noreferrer')}));document.querySelectorAll('[data-filter]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.filter===filter)))}
function initShows(){let node=document.querySelector('[data-shows]');if(!node)return;let today=new Date();today.setHours(0,0,0,0);const shows=SITE.shows.filter(e=>e.date&&new Date(e.date+'T00:00:00')>=today).sort((a,b)=>a.date.localeCompare(b.date));if(!shows.length){node.innerHTML='<div class="empty"><strong>NO SHOWS ANNOUNCED.</strong></div>';return}node.innerHTML=shows.map(e=>{const d=new Date(e.date+'T12:00:00');const ds=isNaN(d.getTime())?e.date:d.toLocaleDateString('en-GB',{day:'2-digit',month:'short',year:'numeric'});return `<div class="event-row"><span class="date">${safe(ds)}</span><span>${safe(e.city)}</span><span class="venue">${safe(e.venue)}</span>${goodUrl(e.tickets)?`<a href="${safe(e.tickets)}" rel="noopener noreferrer">TICKETS ↗</a>`:'<span>SOON</span>'}</div>`}).join('')}
function initContact(){
  const trigger=document.querySelector('[data-contact-trigger]');
  const panel=document.getElementById('contact-panel');
  if(!trigger||!panel)return;
  trigger.addEventListener('click',event=>{
    event.preventDefault();
    const opening=panel.hidden;
    panel.hidden=!opening;
    trigger.setAttribute('aria-expanded',String(opening));
    if(opening)panel.scrollIntoView({behavior:'smooth',block:'nearest'});
  });
  const copy=panel.querySelector('[data-copy-email]');
  const feedback=panel.querySelector('[data-contact-feedback]');
  if(!copy)return;
  copy.addEventListener('click',async()=>{
    const address=copy.dataset.copyEmail;
    try{
      if(navigator.clipboard && window.isSecureContext){
        await navigator.clipboard.writeText(address);
      }else{
        const helper=document.createElement('textarea');
        helper.value=address;
        helper.setAttribute('readonly','');
        helper.style.position='fixed';helper.style.opacity='0';
        document.body.appendChild(helper);helper.select();
        const ok=document.execCommand('copy');helper.remove();
        if(!ok)throw new Error('Copy unavailable');
      }
      if(feedback)feedback.textContent='EMAIL COPIED';
      copy.textContent='COPIED ✓';
      setTimeout(()=>{copy.textContent='COPY EMAIL';if(feedback)feedback.textContent='';},2500);
    }catch{
      if(feedback)feedback.textContent='SELECT AND COPY THE EMAIL ADDRESS ABOVE';
    }
  });
}

function initMenu(){
  const b=document.querySelector('.menu-toggle'),n=document.querySelector('.nav');
  if(!b||!n)return;
  const setOpen=open=>{n.classList.toggle('open',open);b.setAttribute('aria-expanded',String(open));b.textContent=open?'CLOSE':'MENU'};
  b.addEventListener('click',()=>setOpen(!n.classList.contains('open')));
  n.querySelectorAll('a').forEach(a=>a.addEventListener('click',()=>setOpen(false)));
  document.addEventListener('keydown',e=>{if(e.key==='Escape')setOpen(false)});
}
function initHomePhoto(){const n=document.querySelector('.home-stage-photo');if(n && goodUrl(SITE.homePhoto)){n.style.backgroundImage=`url("${SITE.homePhoto.replace(/[\"\\()]/g,'')}")`}}

/* Keep the original shop tab when Gumroad opens a separate return tab.
   This never handles payments or download links. */
function initShopTabReturn(){
  const originKey='sl_original_checkout_tab_v1';
  const pendingKey='sl_checkout_return_v1';
  const channelName='sl_checkout_tabs_v1';
  const maxAge=20*60*1000;
  const safeSessionGet=key=>{try{return sessionStorage.getItem(key)}catch{return null}};
  const getPending=()=>{
    try{
      const value=JSON.parse(localStorage.getItem(pendingKey)||'null');
      return value&&typeof value.token==='string'&&Date.now()-value.time<maxAge&&Date.now()>=value.time?value:null;
    }catch{return null}
  };
  let channel;
  try{if('BroadcastChannel' in window)channel=new BroadcastChannel(channelName)}catch{}
  if(channel){
    channel.addEventListener('message',event=>{
      const msg=event.data;
      if(!msg||typeof msg!=='object')return;
      const pending=getPending();
      if(!pending||msg.token!==pending.token)return;
      if(msg.action==='find-shop'&&safeSessionGet(originKey)===pending.token){
        // Confirm the original shop is still open before the return tab tries to close.
        channel.postMessage({action:'shop-found',token:pending.token});
        try{window.focus()}catch{}
        if(location.pathname.endsWith('/product.html')){
          setTimeout(()=>{location.assign('tabs.html')},300);
        }
      }
    });
  }
  document.addEventListener('click',event=>{
    const link=event.target.closest?.('a[href]');
    if(!link)return;
    let url;
    try{url=new URL(link.href)}catch{return}
    if(url.hostname!=='gumroad.com'||url.pathname!=='/checkout')return;
    const token=String(Date.now())+'-'+Math.random().toString(36).slice(2);
    const pending={token,time:Date.now()};
    try{
      sessionStorage.setItem(originKey,token);
      localStorage.setItem(pendingKey,JSON.stringify(pending));
    }catch{}
  },true);
  // Only the shop return destination is eligible. Do not close ordinary navigation.
  if(!channel||!location.pathname.endsWith('/tabs.html'))return;
  const pending=getPending();
  if(!pending)return;
  const fromGumroad=/^https:\/\/([^/]+\.)?gumroad\.com(?:\/|$)/i.test(document.referrer);
  if(safeSessionGet(originKey)===pending.token&&!fromGumroad)return;
  let replied=false;
  const onReply=event=>{
    const data=event.data;
    if(replied||data?.action!=='shop-found'||data.token!==pending.token)return;
    replied=true;
    channel.removeEventListener('message',onReply);
    try{localStorage.removeItem(pendingKey)}catch{}
    // Chrome can generally close a tab created by a normal target=_blank link.
    // If the browser blocks this, the buyer stays on the normal shop page.
    window.close();
    setTimeout(()=>{
      if(document.visibilityState==='visible'){
        toast('Your original shop tab is open. You can close this extra tab.');
      }
    },600);
  };
  channel.addEventListener('message',onReply);
  setTimeout(()=>channel.postMessage({action:'find-shop',token:pending.token}),120);
  setTimeout(()=>{if(!replied)channel.removeEventListener('message',onReply)},2200);
}

function init(){initShopTabReturn();initHomePhoto();initLinks();initRelease();initVideo();initShows();renderProducts();initMenu();initContact();document.querySelectorAll('[data-filter]').forEach(b=>b.addEventListener('click',()=>{filter=b.dataset.filter;renderProducts()}));document.querySelectorAll('[data-year]').forEach(n=>n.textContent=new Date().getFullYear())}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
