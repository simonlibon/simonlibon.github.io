/* Shared site interactions: navigation, social links, contact and copyright. */
const SITE={
  homePhoto:'',
  links:{
    youtube:'https://www.youtube.com/@simonlibon',
    instagram:'https://www.instagram.com/simon.libon/',
    tiktok:'https://www.tiktok.com/@simonlibon.music',
    facebook:'https://www.facebook.com/profile.php?id=100070692266151',
    email:'simonlibon.music@gmail.com'
  }
};
const goodUrl=v=>{try{return new URL(v).protocol==='https:'}catch{return false}};

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
  n.querySelectorAll('a').forEach(a=>a.addEventListener('click',()=>{if(!a.classList.contains('music-dropdown-trigger'))setOpen(false)}));
  document.addEventListener('keydown',e=>{if(e.key==='Escape')setOpen(false)});
}


/* Compact artist-profile dropdown for the MUSIC navigation item.
   Only direct profile URLs are clickable; track links are not artist profiles. */
function initStreamingMenu(){
  const nav=document.getElementById('site-nav');
  if(!nav||nav.querySelector('.music-nav-wrap'))return;
  const trigger=Array.from(nav.children).find(node=>
    node.tagName==='A' && /^music\.html(?:[?#]|$)/.test(node.getAttribute('href')||'')
  );
  if(!trigger)return;
  const wrap=document.createElement('div');
  wrap.className='music-nav-wrap';
  trigger.before(wrap);
  wrap.append(trigger);
  trigger.classList.add('music-dropdown-trigger');
  trigger.setAttribute('aria-haspopup','true');
  trigger.setAttribute('aria-expanded','false');
  trigger.setAttribute('aria-controls','music-nav-options');

  const menu=document.createElement('div');
  menu.id='music-nav-options';
  menu.className='music-nav-options';
  menu.setAttribute('role','group');
  menu.setAttribute('aria-label','Streaming and video platforms');
  menu.hidden=true;
  wrap.append(menu);

  if(!document.getElementById('music-dropdown-style')){
    const style=document.createElement('style');
    style.id='music-dropdown-style';
    style.textContent=[
      '.music-nav-wrap{position:relative;justify-self:start;align-self:center;z-index:5}',
      '.music-nav-wrap:after{content:"";position:absolute;pointer-events:none;right:-12px;top:calc(50% - 3px);height:5px;width:5px;border-right:1px solid #77757a;border-bottom:1px solid #77757a;transform:rotate(45deg)}',
      '.music-nav-options{position:absolute;z-index:100;left:-16px;top:calc(100% + 11px);width:240px;max-width:calc(100vw - 20px);padding:7px;background:#faf9f7;border:1px solid #dedbd8;box-shadow:0 10px 32px #00000013}',
      '.music-nav-options[hidden]{display:none!important}',
      '.nav .music-nav-options a.music-nav-link{position:static!important;display:flex!important;justify-content:space-between!important;align-items:center!important;min-height:42px!important;width:100%!important;padding:10px 12px!important;color:#18181a!important;text-decoration:none!important;text-transform:none!important;font-size:11px!important;font-weight:600!important;letter-spacing:.01em!important;white-space:normal!important}',
      '.nav .music-nav-options a.music-nav-link:hover,.nav .music-nav-options a.music-nav-link:focus-visible{background:#efede9!important;outline-color:#888}',
      '.music-nav-options .music-nav-note{margin:6px 10px 8px;font:500 10px/1.6 "DM Sans",Arial,sans-serif;color:#77757a;letter-spacing:0;white-space:normal;text-transform:none}',
      '@media(max-width:650px){.nav .music-nav-wrap{justify-self:stretch;align-self:stretch;display:flex;min-width:0;width:100%;min-height:44px;align-items:center}.nav .music-nav-wrap>.music-dropdown-trigger{width:100%!important;min-height:44px!important;display:flex!important;align-items:center!important;justify-content:center!important}.music-nav-wrap:after{right:4px}.music-nav-options{left:0;top:calc(100% + 4px);width:min(245px,90vw)}}'
    ].join('');
    document.head.append(style);
  }

  const entries=[
    ['Spotify','open.spotify.com',/^\/artist\/[^/]+/],
    ['Apple Music','music.apple.com',/\/artist\/[^/]+\/\d+/],
    ['YouTube Music','music.youtube.com',/^\/(?:channel|browse)\/[^/]+/],
    ['Deezer','www.deezer.com',/^\/(?:[a-z]{2}\/)?artist\/\d+/],
    ['Amazon Music','music.amazon.com',/^\/artists\/[^/]+/],
    ['YouTube','www.youtube.com',/^\/@[^/]+\/?$/]
  ];
  const validProfile=(name,host,path,url)=>{
    if(typeof url!=='string'||!url)return false;
    try{
      const parsed=new URL(url);
      return parsed.protocol==='https:' && !parsed.username && !parsed.password &&
        (parsed.hostname===host || (name==='Deezer'&&parsed.hostname==='deezer.com') ||
         (name==='YouTube'&&parsed.hostname==='youtube.com')) &&
        path.test(parsed.pathname);
    }catch{return false;}
  };
  const setOpen=open=>{menu.hidden=!open;trigger.setAttribute('aria-expanded',String(open));};
  trigger.addEventListener('click',event=>{
    event.preventDefault();
    setOpen(menu.hidden);
  });
  trigger.addEventListener('keydown',event=>{
    if(event.key===' '){event.preventDefault();setOpen(menu.hidden);}
    if(event.key==='ArrowDown'){
      event.preventDefault();setOpen(true);
      const first=menu.querySelector('a');if(first)first.focus();
    }
  });
  document.addEventListener('click',event=>{if(!wrap.contains(event.target))setOpen(false);});
  document.addEventListener('keydown',event=>{
    if(event.key==='Escape'&&!menu.hidden){setOpen(false);trigger.focus();}
  });
  function render(profiles){
    menu.replaceChildren();
    const missing=[];
    entries.forEach(([name,host,path])=>{
      const url=profiles&&profiles[name];
      if(validProfile(name,host,path,url)){
        const link=document.createElement('a');
        link.className='music-nav-link';
        link.href=url;
        link.textContent=name+' ↗';
        link.rel='noopener noreferrer';
        menu.append(link);
      }else if(name!=='YouTube'){
        missing.push(name);
      }
    });
    if(missing.length){
      const note=document.createElement('p');
      note.className='music-nav-note';
      note.textContent=missing.length===5
        ? 'Spotify, Apple Music and other streaming profiles coming soon.'
        : 'More streaming profiles coming soon.';
      menu.append(note);
    }
    if(!menu.children.length){
      const note=document.createElement('p');
      note.className='music-nav-note';
      note.textContent='Artist profiles coming soon.';
      menu.append(note);
    }
  }
  // The verified YouTube video channel is available before the first music release.
  render({'YouTube':SITE.links.youtube});
  fetch('streaming-profiles.json',{cache:'no-store'}).then(response=>{
    if(!response.ok)throw Error('Profile configuration unavailable');
    return response.json();
  }).then(data=>render(data&&data.profiles)).catch(()=>{});
}

function initHomePhoto(){const n=document.querySelector('.home-stage-photo');if(n && goodUrl(SITE.homePhoto)){n.style.backgroundImage=`url("${SITE.homePhoto.replace(/[\"\\()]/g,'')}")`}}

function init(){
  initHomePhoto();
  initLinks();
  initMenu();
  initStreamingMenu();
  initContact();
  document.querySelectorAll('[data-year]').forEach(n=>n.textContent=new Date().getFullYear());
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();

/* One shared newsletter handler across every official site page.
   Avoid multiple showModal calls from duplicated page-specific listeners. */
(function initNewsletterDialog(){
  const dialog = document.getElementById('newsletter-dialog');
  if (!dialog) return;
  function open(){
    if (dialog.open || typeof dialog.showModal !== 'function') return;
    dialog.showModal();
  }
  document.addEventListener('click', function(event){
    const trigger = event.target.closest('[data-newsletter-open]');
    if (trigger) {
      event.preventDefault();
      open();
    } else if (event.target === dialog && dialog.open) {
      dialog.close();
    }
  });
  function openFromLink(){
    if (location.hostname !== 'simonlibon.github.io') return;
    if (new URLSearchParams(location.search).get('newsletter') === '1' ||
        location.hash === '#newsletter') open();
  }
  window.addEventListener('hashchange', openFromLink);
  openFromLink();
})();

(function initConcertCountryPicker() {
  const dialog = document.getElementById('newsletter-dialog');
  if (!dialog) return;
  function mountPicker() {
    const field = dialog.querySelector('[eo-label="Concert country"] [data-column-index][data-choices]');
    if (!field || !field.querySelector('[role="combobox"]')) return false;
    const select = document.createElement('select');
    select.id = 'newsletter-concert-country';
    select.add(new Option('Select your country', ''));
    const choices = JSON.parse(field.dataset.choices);
    choices.sort((a, b) => a.label.localeCompare(b.label, 'en'));
    for (const choice of choices) {
      select.add(new Option(choice.label, String(choice.value)));
    }
    const label = document.createElement('label');
    label.htmlFor = select.id;
    label.textContent = 'Concert country (optional)';
    // The embed reads named inputs into its request body.
    const value = document.createElement('input');
    value.type = 'hidden';
    function sync() {
      value.value = select.value;
      if (select.value) value.name = 'field_' + field.dataset.columnIndex;
      else value.removeAttribute('name');
    }
    select.addEventListener('change', sync);
    field.closest('form').addEventListener('reset', () => setTimeout(sync, 0));
    const wrapper = document.createElement('div');
    wrapper.className = 'newsletter-country-picker';
    wrapper.append(label, select, value);
    field.style.display = 'none';
    field.after(wrapper);
    const email = dialog.querySelector('.main-form input[type=email]');
    if (email && email.id && !email.labels.length) {
      const emailLabel = document.createElement('label');
      emailLabel.className = 'newsletter-email-label';
      emailLabel.htmlFor = email.id;
      emailLabel.textContent = 'Email address';
      email.placeholder = 'you@example.com';
      email.before(emailLabel);
    }
    return true;
  }
  if (mountPicker()) return;
  const observer = new MutationObserver(() => {
    if (mountPicker()) observer.disconnect();
  });
  observer.observe(dialog, { childList: true, subtree: true });
})();
