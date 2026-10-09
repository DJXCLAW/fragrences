#!/usr/bin/env python3
"""Import paginated public US storefront catalogs; no invented wear-test scores."""
import html
import json
import math
import re
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

SOURCES = [
    ('Lattafa', 'https://www.lattafa-usa.com', 'all'),
    ('French Avenue', 'https://usa.shopfrenchavenue.com', 'french-avenue'),
]
EXCLUDE = re.compile(r'\b(bundle|gift\s*set|set of|deodorant|deo\s*spray|air\s*freshener|body\s*mist|hair\s*mist|room\s*spray|bakhoor|bukhoor|incense sticks|perfume oil|concentrated oil|gift card|sample|discovery set)\b', re.I)
FAMILIES = {'amber','aromatic','aquatic','citrus','floral','fresh','fruity','gourmand','green','leather','musky','musk','oud','powdery','smoky','spicy','sweet','tobacco','vanilla','woody'}
RATINGS = ['spring','summer','fall','winter','night','weirdness','ease','hoursLow','hoursHigh','projection']


def clean(value):
    value = re.sub(r'<(?:script|style)\b[^>]*>.*?</(?:script|style)>', '', value or '', flags=re.I | re.S)
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', value))).strip()


def tags_of(product):
    tags = product.get('tags') or []
    return [str(t).strip() for t in (tags.split(',') if isinstance(tags, str) else tags)]


def size_ml(text):
    match = re.search(r'(?<!\d)(\d{1,3}(?:\.\d+)?)\s*ml\b', str(text), re.I)
    return float(match[1]) if match else None


def fetch_json(url):
    for attempt in range(3):
        try:
            request = urllib.request.Request(url, headers={'User-Agent': 'FragranceAtlasCatalogSync/2.0', 'Accept': 'application/json'})
            with urllib.request.urlopen(request, timeout=30) as response:
                payload = json.load(response)
            if not isinstance(payload, dict) or not isinstance(payload.get('products'), list):
                raise ValueError('Storefront did not return a products array: ' + url)
            return payload
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
            if attempt == 2:
                raise
            time.sleep(2 ** attempt)


def products(base, collection, fetch=fetch_json):
    seen = set()
    for page in range(1, 41):
        url = f'{base}/collections/{collection}/products.json?limit=250&page={page}'
        batch = fetch(url)['products']
        if not batch:
            return
        added = 0
        for product in batch:
            key = product.get('id') or product.get('handle')
            if not key:
                raise ValueError('Product is missing its stable ID/handle')
            if key not in seen:
                seen.add(key)
                added += 1
                yield product
        if not added:
            raise ValueError('Pagination repeated a page; refusing an incomplete catalog')
        if len(batch) < 250:
            return
        time.sleep(0.2)
    raise ValueError('Pagination safety limit reached; refusing a truncated catalog')


def eligible(brand, product):
    title = product.get('title') or ''
    kind = product.get('product_type') or ''
    vendor = str(product.get('vendor') or '').lower()
    if not title or EXCLUDE.search(title + ' ' + kind):
        return False
    if brand == 'Lattafa' and vendor and 'lattafa' not in vendor:
        return False
    # Exact category tags, not words in scent descriptions (e.g. incense notes).
    if any(EXCLUDE.fullmatch(t.strip()) for t in tags_of(product)):
        return False
    return True


def quote(product):
    variants = product.get('variants') or []
    candidates = []
    common_sizes = {size_ml(t) for t in tags_of(product)} - {None}
    fallback_size = size_ml(product.get('title', ''))
    if fallback_size is None and len(common_sizes) == 1:
        fallback_size = common_sizes.pop()
    for variant in variants:
        label = ' '.join(str(variant.get(k) or '') for k in ('title','option1','option2','option3'))
        size = size_ml(label) or fallback_size
        if EXCLUDE.search(label) or (size is not None and size < 20):
            continue
        try:
            price = float(variant['price'])
            if not math.isfinite(price) or price <= 0:
                price = None
        except (ValueError, TypeError, KeyError):
            price = None
        candidates.append((bool(variant.get('available')), size or 0, variant, size, price))
    if not candidates:
        return None, None, None
    # One consistent bottle variant: available first, then largest listed bottle.
    _, _, variant, size, price = max(candidates, key=lambda q: (q[0], q[1]))
    return variant, size, price


def normalize(brand, base, collection, product, date):
    body = clean(product.get('body_html'))
    tags = tags_of(product)
    title = clean(product['title'])
    variant, size, price = quote(product)
    if variant is None:
        return None
    searchable = ' '.join([title, product.get('product_type') or '', *tags]).lower().replace('-', ' ')
    concentration = None
    for pattern, label in [(r'extrait', 'Extrait de Parfum'), (r'eau de toilette|\bedt\b', 'EDT'), (r'eau de parfum|\bedp\b', 'EDP'), (r'\bparfum\b', 'Parfum')]:
        if re.search(pattern, searchable):
            concentration = label
            break
    sections = {}
    markers = list(re.finditer(r'\b(top|heart|middle|base)\s*notes?\s*[:\-]?\s*', body, re.I))
    for i, match in enumerate(markers):
        end = markers[i + 1].start() if i + 1 < len(markers) else len(body)
        text = body[match.end():end]
        text = re.split(r'\b(?:ingredients|directions|how to use|fragrance (?:type|family)|gender|size|caution|warning)\s*:', text, flags=re.I)[0]
        text = text.strip(' .;:-')[:220]
        if text:
            sections[match[1].lower().replace('middle', 'heart')] = text
    family = ' / '.join(t.title() for t in tags if t.lower() in FAMILIES) or 'Scent family not published in feed'
    notes = '; '.join(f'{k.title()}: {v}' for k, v in sections.items())
    if not notes:
        notes = ', '.join(t for t in tags if t.lower() in FAMILIES) or 'Published notes not available in this feed; open the product source.'
    description = (f'Brand-published profile: {notes}' if sections else f'{title} by {brand}. {family}. Open the source for the full published profile.')[:380]
    url = f'{base}/products/{product["handle"]}'
    quote_url = url + (f'?variant={variant["id"]}' if variant.get('id') else '')
    prefix = 'LTF' if brand == 'Lattafa' else 'FAV'
    return dict(id=f'{prefix}-{product.get("id") or product["handle"]}', brand=brand, name=title,
                catalogGroup=brand, catalogId=str(product.get('id') or product['handle']), catalogOnly=True,
                liveCatalog=True, segment='Basic / value', concentration=concentration, size=size, price=price,
                nativePrice=None, currency='USD', perMl=price / size if price and size else None, deal=None,
                family=family, notes=notes, description=description,
                development='Brand note pyramid: ' + notes if sections else 'Development not assessed; see the product source.',
                setting='Season and occasion fit have not yet been rated.', context='Sample first; fit depends on setting and personal preference.',
                caution='New catalog entry. Missing performance and suitability ratings are deliberately left unrated.',
                projectionLabel='Not rated', performanceEvidence='No independent wear-test evidence was added by this import.',
                performanceSource=None, researched=date, priceBasis='US storefront quote for the selected bottle variant at sync time.',
                stock='Listed in stock at sync' if variant.get('available') else 'Listed out of stock at sync',
                priceCaveat='A dated USD reference, not a live offer. Confirm the selected variant, taxes, shipping and checkout total.',
                priceSource=quote_url, profileSource=url, noteBasis='Storefront note pyramid or scent tags; these are not ingredient lists or wear tests.',
                sourceCatalog=f'{base}/collections/{collection}', **dict.fromkeys(RATINGS))


def main():
    date = datetime.now(timezone.utc).date().isoformat()
    items, counts = [], {}
    for brand, base, collection in SOURCES:
        records = [normalize(brand, base, collection, p, date) for p in products(base, collection) if eligible(brand, p)]
        records = [p for p in records if p]
        if not records:
            raise ValueError(f'{brand}: empty catalog; existing files left untouched')
        counts[brand] = len(records)
        items.extend(records)
    if len({i['id'] for i in items}) != len(items):
        raise ValueError('Duplicate product IDs; existing files left untouched')
    previous = Path('brand-catalog.json')
    if previous.exists():
        old = json.loads(previous.read_text())
        for brand, count in counts.items():
            if count < old.get('counts', {}).get(brand, 0) * 0.6:
                raise ValueError(f'{brand}: suspicious catalog shrink; existing files left untouched')
    items.sort(key=lambda x: (x['brand'], x['name'].casefold()))
    payload = dict(generatedAt=date, counts=counts, fragrances=items,
                   coverage='Wearable full-bottle fragrances in the selected US storefront catalogs; not a verified worldwide/discontinued catalog.',
                   sources=[f'{b}/collections/{c}' for _, b, c in SOURCES])
    text = json.dumps(payload, ensure_ascii=False, separators=(',', ':'), allow_nan=False).replace('<', '\\u003c')
    Path('brand-catalog.json').write_text(json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    Path('brand-catalog.js').write_text('window.BRAND_CATALOG = ' + text + ';\n', encoding='utf-8')
    print(json.dumps(dict(date=date, counts=counts, total=len(items))))


if __name__ == '__main__':
    main()
