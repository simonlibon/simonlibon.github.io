(()=>{
"use strict";
const source=window.SIMON_SHOP_CATALOG||{shopName:"Simon Libon — Tabs & Tracks",products:[]};
const data=JSON.parse(JSON.stringify(source));
const $=id=>document.getElementById(id);
let index=0;
const fields=["title","type","price","date","gumroad","description","includes","image","published"];
const current=()=>data.products[index];
function note(msg){$("notice").textContent=msg}
function populate(){const select=$("item");select.replaceChildren(...data.products.map((p,i)=>{const opt=document.createElement("option");opt.value=i;opt.textContent=(p.published?"● ":"○ ")+p.title;return opt}));if(data.products.length){index=Math.min(index,data.products.length-1);select.value=String(index);render()}else{fields.forEach(f=>{const e=$(f);if(e.type==="checkbox")e.checked=false;else e.value=""});$("preview").removeAttribute("src")}}
function render(){const p=current();if(!p)return;$("title").value=p.title||"";$("type").value=p.type||"tabs";$("price").value=p.price??0;$("date").value=p.releaseDate||"";$("gumroad").value=p.gumroadUrl||"";$("description").value=p.description||"";$("includes").value=(p.includes||[]).join("\n");$("image").value=p.image||"";$("published").checked=!!p.published;if(p.image)$("preview").src=p.image;else $("preview").removeAttribute("src");$("photo").value="";note("")}
function save(){const p=current();if(!p)return false;const title=$("title").value.trim(),url=$("gumroad").value.trim(),published=$("published").checked;if(!title){note("Ajoute le nom du produit.");return false}if(published){try{const u=new URL(url);if(u.protocol!=="https:"||u.hostname!=="simonlibonstore.gumroad.com"||!/^\/l\/[a-z0-9_-]+\/?$/i.test(u.pathname))throw Error("invalid")}catch{note("Pour afficher ce produit, ajoute son lien Gumroad valide.");return false}}
Object.assign(p,{title,type:$("type").value,price:Math.max(0,Number($("price").value)||0),releaseDate:$("date").value||new Date().toISOString().slice(0,10),gumroadUrl:url,description:$("description").value.trim(),includes:$("includes").value.split(/\r?\n/).map(x=>x.trim()).filter(Boolean),image:$("image").value.trim(),published});populate();note("Modifications sauvegardées ici. Télécharge catalog.js pour les publier.");return true}
function add(){if(data.products.length&&!save())return;data.products.push({id:"release-"+Date.now(),title:"New release",type:"tabs",description:"",includes:[],price:8,gumroadUrl:"",image:"",published:false,releaseDate:new Date().toISOString().slice(0,10)});index=data.products.length-1;populate()}
function remove(){if(!data.products.length)return;if(!confirm("Retirer ce produit de ton catalogue local ?"))return;data.products.splice(index,1);index=Math.max(0,index-1);populate()}
function exportFile(){if(!save())return;const txt="/* Simon Libon catalogue */\nwindow.SIMON_SHOP_CATALOG = "+JSON.stringify(data,null,2).replaceAll("\u2028","")+";\n";const blob=new Blob([txt],{type:"application/javascript;charset=utf-8"}),url=URL.createObjectURL(blob),a=document.createElement("a");a.href=url;a.download="catalog.js";a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);note("catalog.js téléchargé. Remplace ce fichier sur GitHub pour publier les changements.")}
$("item").addEventListener("change",e=>{const target=Number(e.target.value)||0;if(!save())return;index=target;$("item").value=String(index);render()});
$("add").addEventListener("click",add);
$("remove").addEventListener("click",remove);
$("save").addEventListener("click",save);
$("export").addEventListener("click",exportFile);
$("photo").addEventListener("change",event=>{const file=event.target.files?.[0];if(!file)return;if(file.size>18_000_000){note("Choisis une image de moins de 18 Mo.");return}const img=new Image(),url=URL.createObjectURL(file);img.onload=()=>{const canvas=document.createElement("canvas"),side=800;canvas.width=side;canvas.height=side;const ctx=canvas.getContext("2d");ctx.fillStyle="#eeece8";ctx.fillRect(0,0,side,side);const scale=Math.min(side/img.width,side/img.height);ctx.drawImage(img,(side-img.width*scale)/2,(side-img.height*scale)/2,img.width*scale,img.height*scale);const result=canvas.toDataURL("image/jpeg",.84);$("image").value=result;$("preview").src=result;URL.revokeObjectURL(url);note("Photo ajoutée sans recadrage. Clique sur Enregistrer.");};img.onerror=()=>{URL.revokeObjectURL(url);note("Impossible de lire cette image.")};img.src=url});
populate();
})();