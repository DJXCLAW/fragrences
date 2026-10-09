#!/usr/bin/env python3
"""Merge the catalog into the standalone site, preserving curated IDs and saved lists."""
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit


def key(brand, name):
    text = unicodedata.normalize('NFKD', str(name)).encode('ascii', 'ignore').decode().lower()
    text = re.sub(r"['`\u2019]", '', text)
    text = re.sub(r'\blattafa(?: pride)?\b|\bfrench avenue\b|\beau de parfum\b|\bedp\b|\b\d+(?:\.\d+)?\s*ml\b', ' ', text)
    text = re.sub(r'[^a-z0-9]+', ' ', text).strip()
    aliases = {'fakhar black':'fakhar men', 'fakhar lattafa black':'fakhar men', 'badee al oud oud for glory':'badee al oud for glory'}
    return brand.lower(), aliases.get(text, text)


def site_data(text):
    start = re.search(r'window\.ATLAS_DATA\s*=\s*', text)
    if not start:
        raise ValueError('ATLAS_DATA assignment not found; site not changed')
    data, size = json.JSONDecoder().raw_decode(text[start.end():])
    return data, start.end(), start.end() + size


def main():
    path = Path('index.html')
    text = path.read_text(encoding='utf-8')
    catalog = json.loads(Path('brand-catalog.json').read_text(encoding='utf-8'))
    if not catalog.get('fragrances'):
        raise ValueError('Empty supplemental catalog; site not changed')
    data, start, end = site_data(text)
    originals = data['fragrances']
    records = {i['id']: dict(i) for i in originals}
    names = {key(i['brand'], i['name']): i['id'] for i in originals}
    urls = {urlsplit(i.get('profileSource') or '').path.rstrip('/'): i['id'] for i in originals if i.get('profileSource')}
    catalog_ids = {(i.get('catalogGroup'), i.get('catalogId')): i['id'] for i in originals if i.get('catalogId')}
    active = set()
    for source in catalog['fragrances']:
        item = dict(source)
        item_key = key(item['brand'], item['name'])
        old_id = catalog_ids.get((item['brand'], item.get('catalogId'))) or names.get(item_key)
        if old_id is None:
            possible = urls.get(urlsplit(item.get('profileSource') or '').path.rstrip('/'))
            if possible and records[possible]['brand'] == item['brand']:
                old_id = possible
        if old_id:
            old = records[old_id]
            item['id'] = old_id
            if not old.get('catalogOnly'):
                # Keep curated assessments and identity; update only variant-bound facts.
                facts = ['catalogGroup','catalogId','liveCatalog','price','size','concentration','perMl','nativePrice','currency','deal','stock','researched','priceBasis','priceCaveat','priceSource','sourceCatalog']
                item = dict(old, **{field:item.get(field) for field in facts})
                item['catalogOnly'] = False
        records[item['id']] = item
        names[item_key] = item['id']
        active.add(item['id'])
    # A delisting must not destroy someone's saved fragrance or testing notes.
    for item in records.values():
        if item.get('catalogOnly') and item['id'] not in active:
            item.update(price=None, perMl=None, stock='Not in the latest selected storefront catalog', priceBasis='Current bottle quote unavailable')
    data['fragrances'] = list(records.values())
    data['catalogSnapshot'] = catalog['generatedAt']
    data['catalogCounts'] = catalog['counts']
    data['catalogCoverage'] = catalog['coverage']
    data['edition'] = '003'
    encoded = json.dumps(data, ensure_ascii=False, separators=(',', ':'), allow_nan=False).replace('<', '\\u003c')
    text = text[:start] + encoded + text[end:]
    if '/* catalog-ui-v2 */' not in text:
        def replace(old, new):
            nonlocal text
            if old not in text:
                raise ValueError('Site structure changed; missing patch anchor: ' + old[:90])
            text = text.replace(old, new)
        # Put the house filter in the main toolbar, not behind several menus.
        replace('<div class="filter-row"><div class="segment-tabs"', '<div class="house-row"><label for="house-filter">Explore a house</label><select id="house-filter"><option value="all">All houses</option><option value="Lattafa">Lattafa &amp; Lattafa Pride</option><option value="French Avenue">French Avenue</option></select><span>New catalog profiles show unrated fields honestly.</span></div><div class="filter-row"><div class="segment-tabs"')
        replace("const state = {query:'',", "/* catalog-ui-v2 */\n  const rating = value => Number.isFinite(value) && value >= 1 && value <= 5 ? `${value}/5` : 'Not rated';\n  const state = {house:'all',query:'',")
        replace("Object.assign(state,{query:'',", "Object.assign(state,{house:'all',query:'',")
        replace("if (state.category !== 'all'", "if (state.house !== 'all' && (item.catalogGroup || item.brand) !== state.house) return false;\n      if (state.category !== 'all'")
        replace("!state.query && state.category==='all'", "!state.query && state.house==='all' && state.category==='all'")
        replace("$('#search').value=state.query;", "$('#house-filter').value=state.house;$('#search').value=state.query;")
        replace("const filterBindings={", "const filterBindings={'house-filter':['house',String],")
        replace('const shape = Number(item.id.slice(1)) % 4;', "const shape = [...item.id].reduce((sum,c)=>sum+c.charCodeAt(0),0) % 4;")
        replace('(editorialOrder.get(a.id) ?? Number(a.id.slice(1))+100) - (editorialOrder.get(b.id) ?? Number(b.id.slice(1))+100)', '(editorialOrder.get(a.id) ?? (Number(a.id.slice(1)) || 10000)+100) - (editorialOrder.get(b.id) ?? (Number(b.id.slice(1)) || 10000)+100) || a.name.localeCompare(b.name)')
        replace("${item[season]??'?'}/5", '${rating(item[season])}')
        for field in ['spring','summer','fall','winter','night','weirdness','ease']:
            replace('${item.' + field + '}/5', '${rating(item.' + field + ')}')
        replace('${hours(item)} est.', "${hours(item)}${item.hoursLow==null?'':' est.'}")
        replace('${hours(item)} estimated', "${hours(item)}${item.hoursLow==null?'':' estimated'}")
        replace('bottle prices dated September 19, 2026.', 'reference dates are shown in each profile.')
        replace('item.profileSource,data.snapshot', 'item.profileSource,item.researched || data.snapshot')
        replace('Prices were researched on September 19, 2026 and are not live.', 'Original quotes date to September 19, 2026; catalog additions have their own sync date in each profile. Neither is a live price feed.')
        replace('REFERENCE PRICES &middot; SEP 19, 2026', 'REFERENCE PRICES &middot; DATES IN PROFILES')
        replace('Source links are carried over from the supplied workbook and have not been re-verified for this site.', 'Original sources come from the workbook; catalog sources come from the selected US storefront feeds. Check the profile date and current product page.')
        replace('Season filters require an editorial fit of 4/5 or higher.', 'Season filters require an editorial fit of 4/5 or higher; unrated catalog entries are excluded from rated filters.')
        replace('These are editorial judgments, not quality or attractiveness scores.', 'These are editorial judgments, not quality or attractiveness scores. Not rated means evidence is missing, not that the fragrance scored zero.')
        replace('This edition adds 100 editorial profiles;', 'This edition also imports the selected Lattafa and French Avenue US catalogs. It does not claim every regional or discontinued release. Imported performance fields stay unrated unless an existing curated assessment is retained. This edition adds 100 editorial profiles;')
        replace('All performance ranges, seasonal fits, and scent descriptions are editorial estimates or interpretations, not firsthand testing.', 'Published catalog notes come from the source; performance and suitability ratings, where present, are editorial estimates, not firsthand testing. Unrated means not assessed.')
        replace('</head>', '<style>.house-row{display:flex;align-items:center;gap:12px;flex-wrap:wrap;margin-top:18px;font-size:12px}.house-row select{min-height:44px;padding:8px 12px;background:var(--white);border:1px solid var(--line);border-radius:4px;color:var(--ink);max-width:100%}.house-row span{color:var(--muted);font-size:11px}.fit-row{grid-template-columns:60px 1fr 76px}.metric-tile b{overflow-wrap:anywhere}@media(max-width:600px){.house-row select{font-size:16px;flex:1;min-width:0}.house-row span{width:100%}.fit-row{grid-template-columns:55px 1fr 70px}}</style></head>')
    count = len(records)
    text = re.sub(r'(Explore |Discover |guide to )\d+( fragrances| basic)', lambda m:m[1]+str(count)+m[2], text)
    text = re.sub(r'(All fragrances <span>)\d+', lambda m:m[1]+str(count), text)
    for segment, number in Counter(i['segment'] for i in records.values()).items():
        text = re.sub(r'(data-segment="' + re.escape(segment) + r'"><span class="stat-number">)\d+', lambda m:m[1]+str(number), text)
    text = re.sub(r'Edition \d+ &middot; Catalog expanded: [^<]+', 'Edition 003 &middot; House catalog synced: ' + catalog['generatedAt'], text)
    path.write_text(text, encoding='utf-8')
    report = dict(snapshot=catalog['generatedAt'], sourceCounts=catalog['counts'], totalFragrances=count,
                  catalogProfilesInSite=len(active), addedThisRun=count-len(originals), coverage=catalog['coverage'])
    print(json.dumps(report))


if __name__ == '__main__':
    main()
