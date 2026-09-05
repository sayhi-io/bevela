/* Measured-history rendering contract; no service or telemetry access. */
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const node=tag=>({tag,children:[],attributes:{},classList:{add(){}},append(...items){this.children.push(...items);},setAttribute(k,v){this.attributes[k]=v;}});
const context={data:{observed_at:'1970-01-01T00:16:40Z'},document:{createElementNS:(_,tag)=>node(tag)},el:(tag,text,className)=>Object.assign(node(tag),{textContent:text,className})};
vm.createContext(context);
const source=fs.readFileSync(path.join(__dirname,'../project_intent/web/app.js'),'utf8');
vm.runInContext(source.slice(source.indexOf('function activityChart('),source.indexOf('function clear(')),context);
const chart=(points,status='recent')=>context.activityChart({key:'scope:work',activity:{status,points}});
const paths=chart=>chart.children[0].children.filter(n=>n.attributes.class==='activity-line');
const points=[{at:940,value:4},{at:950,value:5},{at:970,value:3},{at:980,value:4}];
assert.equal(paths(chart(points)).length,1);
assert.equal(paths(chart(points.map((p,i)=>({...p,break_before:i===2})))).length,2);
assert.equal(paths(chart(points.map((p,i)=>({...p,value:i===2?null:p.value})))).length,2);
assert.equal(paths(chart([{at:700,value:4},{at:990,value:4}])).length,2);
for(const status of ['stale','unavailable','inactive','expired','not-observed']){
  const rendered=chart(points,status);
  assert.equal(paths(rendered).length,1);
  assert.ok(rendered.children[1].textContent.startsWith(status+' · last reports'));
  assert.ok(!rendered.children[1].textContent.includes('reported tok/s'));
}
console.log('History chart checks passed: retained stale/inactive history, explicit lease breaks, unknown/time gaps, no live-rate revival.');
