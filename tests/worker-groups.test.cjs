const {test}=require('node:test'),assert=require('node:assert/strict');
const F=require('../project_intent/web/worker-group-facts.js');
const now=1800000000000,at=now/1000;
const p={session:'s',status:'active',heartbeat_at:new Date(now-1000).toISOString(),expires_at:new Date(now+60000).toISOString()};
const a={session:'s',status:'recent',last_report_at:at-2,points:[{at:at-2,value:12.34}]};
test('rate is attached to exact session, never work aggregate',()=>{const r=F.sessions({workers:[p],activity:{sessions:[a,{...a,session:'other'}]}},now);assert.equal(r.length,2);assert(r.every(x=>x.rate===12.34));assert.equal(r.find(x=>x.id==='s').label,'12.3 tok/s');});
test('presence-only remains unmeasured; not zero rate',()=>{const r=F.sessions({workers:[p]},now)[0];assert.equal(r.label,'Present · unmeasured');assert.equal(r.rate,null);});
test('stale, disconnected, released, missing and invalid samples never look live',()=>{for(const metric of [{...a,last_report_at:at-91},{...a,points:[{at:at-100,value:1}]},{...a,points:[{at:at+5,value:1}]},{...a,points:[{at:at-2,value:null}]},{...a,points:[{at:at-2,value:-3}]}])assert.equal(F.sessions({workers:[p],activity:metric},now)[0].rate,null);assert.equal(F.sessions({workers:[p],activity:a},now,false)[0].kind,'unknown');assert.equal(F.sessions({workers:[{...p,status:'inactive'}],activity:a},now)[0].label,'Released');});
test('zero is a measured rate, duplicates ambiguous, no fake session from anonymous metric',()=>{assert.equal(F.sessions({activity:{...a,points:[{at:at-2,value:0}]}},now)[0].rate,0);assert.equal(F.sessions({workers:[p,p],activity:a},now)[0].label,'Ambiguous registration');assert.equal(F.sessions({activity:{...a,session:null}},now).length,0);});
test('sharing uses exact identity within authorized scope; input unchanged',()=>{const data={workstreams:[{key:'a:1',scope_id:'a',workers:[p]},{key:'a:2',scope_id:'a',workers:[p]},{key:'b:3',scope_id:'b',workers:[p]},{key:'a:4',scope_id:'a',workers:[{...p,session:'similar-s'}]}]};const before=JSON.stringify(data);assert.equal(F.assignments(data,'a','s').length,2);assert.equal(JSON.stringify(data),before);});
test('sparkline uses a fixed time window and cubic curves without mutating samples',()=>{
 const points=[{at:at-900,value:2},{at:at-800,value:20},{at:at-700,value:5}];
 const before=JSON.stringify(points),chart=F.sparkline(points,now);
 assert.equal(chart.paths.length,1);assert.equal(chart.maximum,20);
 assert.match(chart.paths[0],/^M2\.000 /);assert.equal(chart.paths[0].split(' C').length,3);
 assert.equal(JSON.stringify(points),before);
});
test('sparkline never fabricates a line for absent or single samples; zero remains flat',()=>{
 for(const points of [[],[{at:at-2,value:4}],[{at:at-2,value:null}]])assert.deepEqual(F.sparkline(points,now).paths,[]);
 const zero=F.sparkline([{at:at-20,value:0},{at:at-10,value:0}],now);
 assert.match(zero.paths[0],/28\.000/);assert.equal(zero.maximum,1);
 const numbers=zero.paths[0].match(/-?\d+\.\d+/g).map(Number);
 assert(numbers.filter((_,i)=>i%2).every(y=>y===28));
});
test('sparkline breaks on unknowns, invalid timestamps/rates, epochs and reporting gaps',()=>{
 const point=(offset,value=5)=>({at:at+offset,value});
 for(const separator of [point(-40,null),point(-40,-1),point(-40,NaN),point(-40,Infinity),{at:NaN,value:5},point(1),point(-901),null]){
  const chart=F.sparkline([point(-60),point(-50),separator,point(-30),point(-20)],now);
  assert.equal(chart.paths.length,2);assert(!chart.paths.join('').match(/NaN|Infinity/));
 }
 for(const points of [[point(-60),point(-50),{...point(-40),break_before:true},point(-30)],[point(-300),point(-290),point(-40),point(-30)],[point(-60),point(-50),point(-50),point(-40)]])assert.equal(F.sparkline(points,now).paths.length,2);
});
test('curve controls stay bounded by each pair of samples, including sharp reversals',()=>{
 const points=[0,30,1,29,29,0].map((value,i)=>({at:at-120+i*i*4,value}));
 const chart=F.sparkline(points,now),parts=chart.paths[0].split(' C');
 for(let i=1;i<parts.length;i++){
  const coords=parts[i].split(' ').map(Number),ys=coords.filter((_,j)=>j%2);
  const startY=28-points[i-1].value/30*24,endY=28-points[i].value/30*24;
  assert(ys.every(y=>y>=Math.min(startY,endY)-.001&&y<=Math.max(startY,endY)+.001));
 }
});
