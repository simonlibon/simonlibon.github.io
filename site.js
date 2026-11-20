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
  n.querySelectorAll('a').forEach(a=>a.addEventListener('click',()=>setOpen(false)));
  document.addEventListener('keydown',e=>{if(e.key==='Escape')setOpen(false)});
}

function initHomePhoto(){const n=document.querySelector('.home-stage-photo');if(n && goodUrl(SITE.homePhoto)){n.style.backgroundImage=`url("${SITE.homePhoto.replace(/[\"\\()]/g,'')}")`}}

function init(){
  initHomePhoto();
  initLinks();
  initMenu();
  initContact();
  document.querySelectorAll('[data-year]').forEach(n=>n.textContent=new Date().getFullYear());
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();

/* Shared newsletter dialog on every page. */
(function(){const d=document.getElementById('newsletter-dialog');if(!d)return;document.querySelectorAll('[data-newsletter-open]').forEach(a=>a.addEventListener('click',e=>{e.preventDefault();if(!d.open)d.showModal();}));d.addEventListener('click',e=>{if(e.target===d)d.close();});})();

(function initConcertCountryPicker() {
  const dialog = document.getElementById('newsletter-dialog');
  if (!dialog) return;
  function mountPicker() {
    const field = dialog.querySelector('[eo-label="Concert country"] [data-column-index][data-choices]');
    if (!field || !field.querySelector('[role="combobox"]')) return false;
    const select = document.createElement('select');
    select.id = 'newsletter-concert-country';
    select.add(new Option('Select your country', ''));
    for (const choice of JSON.parse(field.dataset.choices)) {
      select.add(new Option(choice.label, String(choice.value)));
    }
    const label = document.createElement('label');
    label.htmlFor = select.id;
    label.textContent = field.dataset.label;
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
    return true;
  }
  if (mountPicker()) return;
  const observer = new MutationObserver(() => {
    if (mountPicker()) observer.disconnect();
  });
  observer.observe(dialog, { childList: true, subtree: true });
})();
