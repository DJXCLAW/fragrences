const fs=require('fs'),vm=require('vm'),assert=require('assert/strict');
const h=fs.readFileSync(__dirname+'/index.html','utf8');
const scripts=[...h.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(m=>m[1]);
for(const s of scripts)new vm.Script(s);
const context={window:{}};vm.runInNewContext(scripts[0],context);
const d=context.window.ATLAS_DATA;
assert.equal(d.fragrances.length,172);assert.equal(new Set(d.fragrances.map(x=>x.id)).size,172);assert.equal(d.picks.length,40);assert.equal(d.fragrances.filter(x=>x.lab).length,36);
assert(!/data-field="cost"|sampleBudget|updateBudgetUI|shortlistTotals|Unit sample USD/.test(h));
assert(context.window.ATLAS_WORKBOOK_BASE64.length>1000);
console.log('PASS: scripts parse; 172 unique fragrances, 40 seasonal picks, 36 avant-garde profiles, embedded workbook, no sample-cost logic.');



