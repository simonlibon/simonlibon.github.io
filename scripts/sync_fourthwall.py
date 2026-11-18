"""Read-only Fourthwall catalog sync. Token never appears in generated files."""
import json, os, urllib.request, urllib.parse
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
TOKEN=os.environ.get("FOURTHWALL_STOREFRONT_TOKEN","")
if not TOKEN: raise SystemExit("Missing FOURTHWALL_STOREFRONT_TOKEN")
base="https://storefront-api.fourthwall.com/v1/collections/all/products"
products=[]
for page in range(100):
    qs=urllib.parse.urlencode({"storefront_token":TOKEN,"currency":"EUR","page":page,"size":100})
    req=urllib.request.Request(base+"?"+qs,headers={"Accept":"application/json"})
    with urllib.request.urlopen(req,timeout=30) as res: data=json.load(res)
    if isinstance(data,list): batch=data; more=len(batch)==100
    elif isinstance(data,dict):
        batch=data.get("results",data.get("products",[]))
        paging=data.get("paging",{})
        more=paging.get("hasNextPage",False)
    else: raise RuntimeError("Unexpected Fourthwall API response")
    if not isinstance(batch,list): raise RuntimeError("Invalid product list")
    products.extend(batch)
    if not more: break
else: raise RuntimeError("Pagination limit exceeded")
out=[]
for p in products:
    if not isinstance(p,dict): continue
    if p.get("access",{}).get("type","PUBLIC")!="PUBLIC": continue
    slug=p.get("slug")
    if not slug: continue
    variants=p.get("variants") or []
    price=(variants[0].get("unitPrice") if variants else None) or {}
    images=p.get("images") or []
    out.append({"id":str(p.get("id",slug)),"name":p.get("name") or slug,"slug":slug,"url":"https://simon-libon-music-shop.fourthwall.com/products/"+urllib.parse.quote(slug),"image":images[0].get("url","") if images else "","price":price.get("value"),"currency":price.get("currency","EUR"),"createdAt":p.get("createdAt","")})
path=ROOT/"fourthwall-products.json"
content=json.dumps({"products":out},ensure_ascii=False,indent=2)+"\n"
if not path.exists() or path.read_text()!=content: path.write_text(content)
print("Synced",len(out),"Fourthwall products")
