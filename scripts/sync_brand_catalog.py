#!/usr/bin/env python3
import html, json, re, urllib.request
from datetime import datetime, timezone

SOURCES = [
    {
        "brand": "Lattafa",
        "url": "https://www.lattafa-usa.com/collections/eau-de-parfum-edp/products.json?limit=250",
        "base": "https://www.lattafa-usa.com",
        "default_concentration": "Eau de Parfum",
    },
    {
        "brand": "French Avenue",
        "url": "https://usa.shopfrenchavenue.com/collections/french-avenue/products.json?limit=250",
        "base": "https://usa.shopfrenchavenue.com",
        "default_concentration": "Eau de Parfum",
    },
]

EXCLUDE = re.compile(r"\b(bundle|gift set|set of|deodorant|deo spray|air freshener|body mist|hair mist|room spray|bakhoor)\b", re.I)
FAMILY_WORDS = [
    "amber","aromatic","aquatic","citrus","floral","fresh","fruity","gourmand",
    "green","leather","musk","oud","oriental","powdery","smoky","spicy","sweet",
    "tobacco","vanilla","woody"
]

def clean_html(value):
    text = re.sub(r"<[^>]+>", " ", value or "")
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()

def concentration(title, default):
    t = title.lower()
    if "extrait" in t: return "Extrait de Parfum"
    if "eau de toilette" in t or re.search(r"\bedt\b", t): return "Eau de Toilette"
    if "parfum" in t and "eau de parfum" not in t: return "Parfum"
    if "eau de parfum" in t or re.search(r"\bedp\b", t): return "Eau de Parfum"
    return default

def size_ml(title, body):
    text = f"{title} {body}"
    m = re.search(r"(?<!\d)(\d{2,3}(?:\.\d+)?)\s*ml\b", text, re.I)
    if m: return round(float(m.group(1)), 1)
    m = re.search(r"(\d(?:\.\d+)?)\s*(?:fl\.?\s*oz|fluid ounces?)", text, re.I)
    if m: return round(float(m.group(1)) * 29.5735, 1)
    return None

def family_and_notes(product):
    tags = product.get("tags") or []
    if isinstance(tags, str):
        tags = [x.strip() for x in tags.split(",") if x.strip()]
    normalized = {str(x).strip().lower(): str(x).strip() for x in tags}
    hits = [normalized[w] for w in FAMILY_WORDS if w in normalized]
    family = " / ".join(h.title() for h in hits[:2]) if hits else "Modern Middle Eastern"
    notes = ", ".join(hits[:6]) if hits else "See official product profile for the published note pyramid."
    return family, notes

def price(product):
    vals=[]
    for v in product.get("variants") or []:
        try: vals.append(float(v.get("price")))
        except (TypeError, ValueError): pass
    return min(vals) if vals else None

def fetch_json(url):
    req=urllib.request.Request(url, headers={"User-Agent":"FragranceAtlasCatalogSync/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)

def normalize(source, product):
    title=(product.get("title") or "").strip()
    body=clean_html(product.get("body_html") or "")
    fam, notes=family_and_notes(product)
    p=price(product)
    url=f'{source["base"]}/products/{product.get("handle","")}'
    pid=str(product.get("id") or re.sub(r"\W+","-",title.lower()))
    prefix="LTF" if source["brand"]=="Lattafa" else "FAV"
    desc=body[:420].rstrip()
    if len(body)>420: desc += "..."
    if not desc:
        desc=f"{source['brand']} fragrance. Open the official product page for the current published scent description."
    return {
        "id": f"{prefix}-{pid}",
        "brand": source["brand"],
        "name": title,
        "segment": "Basic / value",
        "concentration": concentration(title, source["default_concentration"]),
        "size": size_ml(title, body),
        "price": p,
        "nativePrice": None,
        "currency": "USD",
        "perMl": round(p / size_ml(title, body), 2) if p and size_ml(title, body) else None,
        "deal": None,
        "family": fam,
        "notes": notes,
        "description": desc,
        "development": "Open the official product page for the brand's current note pyramid and development description.",
        "setting": "Performance and seasonal fit have not yet been independently rated by Fragrance Atlas.",
        "context": "Use the official scent profile as the starting point; sample before committing to a full bottle.",
        "caution": "New catalog entry: longevity, projection, seasonal fit, and everyday-ease scores are not independently verified.",
        "hoursLow": None,
        "hoursHigh": None,
        "projection": None,
        "projectionLabel": "Not verified",
        "performanceEvidence": "No Fragrance Atlas performance estimate yet.",
        "performanceSource": None,
        "spring": 0, "summer": 0, "fall": 0, "winter": 0, "night": 0,
        "weirdness": 1,
        "ease": 3,
        "researched": datetime.now(timezone.utc).date().isoformat(),
        "priceBasis": "Current official U.S. storefront catalog price at sync time.",
        "stock": "Check official store",
        "priceCaveat": "Live storefront pricing can change; confirm the exact bottle and checkout total.",
        "priceSource": url,
        "profileSource": url,
        "noteBasis": "Official storefront description/tags where available.",
        "sourceCatalog": source["url"],
        "liveCatalog": True,
    }

def main():
    items=[]
    seen=set()
    stats={}
    for source in SOURCES:
        payload=fetch_json(source["url"])
        count=0
        for product in payload.get("products", []):
            title=(product.get("title") or "").strip()
            if not title or EXCLUDE.search(title):
                continue
            key=(source["brand"].lower(), re.sub(r"\s+"," ",title.lower()).strip())
            if key in seen:
                continue
            seen.add(key)
            items.append(normalize(source, product))
            count += 1
        stats[source["brand"]]=count
    items.sort(key=lambda x:(x["brand"],x["name"].lower()))
    stamp=datetime.now(timezone.utc).isoformat(timespec="seconds")
    payload={"generatedAt":stamp,"sources":[s["url"] for s in SOURCES],"counts":stats,"fragrances":items}
    with open("brand-catalog.json","w",encoding="utf-8") as f:
        json.dump(payload,f,ensure_ascii=False,indent=2)
        f.write("\n")
    with open("brand-catalog.js","w",encoding="utf-8") as f:
        f.write("window.BRAND_CATALOG = ")
        json.dump(payload,f,ensure_ascii=False,separators=(",",":"))
        f.write(";\n")
    print(json.dumps({"generatedAt":stamp,"counts":stats,"total":len(items)}))

if __name__=="__main__":
    main()
