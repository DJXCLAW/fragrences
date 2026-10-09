const fs=require('fs'),vm=require('vm'),assert=require('assert/strict');
const h=fs.readFileSync(__dirname+'/index.html','utf8');
const scripts=[...h.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m=>m[1]);
for(const s of scripts)new vm.Script(s);
const context={window:{}};vm.runInNewContext(scripts[0],context);
const d=context.window.ATLAS_DATA,ids=new Set(d.fragrances.map(x=>x.id));
assert(d.fragrances.length>=172);assert.equal(ids.size,d.fragrances.length);
for(let n=1;n<=172;n++)assert(ids.has('F'+String(n).padStart(3,'0')),'Lost original ID '+n);
assert.equal(d.picks.length,40);assert.equal(d.fragrances.filter(x=>x.lab).length,36);
assert(d.picks.every(p=>ids.has(p.id)));
assert(!/data-field="cost"|sampleBudget|updateBudgetUI|shortlistTotals|Unit sample USD/.test(h));
assert(context.window.ATLAS_WORKBOOK_BASE64.length>1000);
if(d.catalogSnapshot){
 assert(h.includes('id="house-filter"'));assert(h.includes('const rating ='));
 const fresh=d.fragrances.filter(x=>x.catalogOnly);
 assert(fresh.some(x=>x.brand==='Lattafa'));assert(fresh.some(x=>x.brand==='French Avenue'));
 for(const item of fresh){
  for(const key of ['hoursLow','hoursHigh','projection','spring','summer','fall','winter','night','weirdness','ease'])assert.equal(item[key],null,item.id+' '+key+' must be unrated');
  assert(/^https:\/\//.test(item.profileSource));assert(item.price==null||Number.isFinite(item.price));
  if(item.perMl!=null)assert(Math.abs(item.perMl-item.price/item.size)<1e-8);
 }
 assert(h.includes('All fragrances <span>'+d.fragrances.length+'</span>'));
}
console.log(JSON.stringify({status:'PASS',total:d.fragrances.length,originals:172,seasonalPicks:d.picks.length,avantGarde:36,catalogSnapshot:d.catalogSnapshot||null,sourceCounts:d.catalogCounts||{},checks:'Syntax, preserved IDs, unique IDs, source links, null ratings, variant pricing, counters, embedded workbook, no sample-cost UI'}));
