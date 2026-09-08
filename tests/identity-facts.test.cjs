const {test}=require('node:test');
const assert=require('node:assert/strict');
const {pattern,design}=require('../project_intent/web/identity-facts.js');
test('same exact scoped identity has stable mirrored cells',()=>{
 const a=pattern('sayhi/project-intent','PI-MISSION-01');
 assert.deepEqual(a,pattern('sayhi/project-intent','PI-MISSION-01'));
 assert.ok(a.cells.length>0);
 for(const [x,y] of a.cells){assert.ok(x>=0&&x<5&&y>=0&&y<5);assert.ok(a.cells.some(([xx,yy])=>xx===4-x&&yy===y));}
});
test('scopes are explicit and different identities vary, not title/status dependent',()=>{
 assert.notDeepEqual(pattern('a','b'),pattern('b','a'));
 assert.notDeepEqual(pattern('a:b','c'),pattern('a','b:c'));
 const patterns=new Set(Array.from({length:100},(_,i)=>JSON.stringify(pattern('sayhi/sparkops','work-'+i))));assert.equal(patterns.size,100);
});
test('design flag is a closed allowlist; unknown input preserves default',()=>{
 for(const id of ['plan','studio','console'])assert.equal(design(id),id);
 for(const id of [null,'','PLAN','<script>','../../x','default'])assert.equal(design(id),'default');
});
