const {test}=require('node:test'),assert=require('node:assert/strict');
const F=require('../project_intent/web/activity-views-facts.js');

const local=(year,month,day,hour=12)=>new Date(year,month,day,hour).toISOString();
const work=(key,extra={})=>({key,scope_id:key.split(':')[0],id:key.split(':')[1],title:key,...extra});

test('calendar indexes only valid handoffs, reports and known recent releases',()=>{
 const result={workstreams:[
  work('a:one',{handoff_at:local(2026,8,8),handoff_summary:'Shipped one',local_reports:[{id:'r1',created_at:local(2026,8,9),payload:{packet:{summary:'Checked one'}}}]}),
  work('a:two',{handoff_at:'not-a-date',local_reports:[{id:'bad',created_at:null,payload:{packet:{summary:'No time'}}}]})
 ],recently_rested:[{workstream:'a:one',session:'s1',working:'Wrapped up',reported_inactive_at:local(2026,8,10)},{workstream:'a:missing',session:'orphan',reported_inactive_at:local(2026,8,10)}]};
 const before=JSON.stringify(result),events=F.events(result);
 assert.deepEqual(events.map(event=>event.type),['release','report','handoff']);
 assert.deepEqual(events.map(event=>event.summary),['Wrapped up','Checked one','Shipped one']);
 assert.equal(JSON.stringify(result),before);
});

test('developer board requires fresh observation and never promotes lifecycle alone',()=>{
 const now=new Date(2026,8,10,12).getTime(),fresh={session:'fresh',status:'active',heartbeat_at:new Date(now-1000).toISOString(),expires_at:new Date(now+60000).toISOString()},expired={session:'expired',status:'active',heartbeat_at:new Date(now-90000).toISOString(),expires_at:new Date(now-1).toISOString()};
 const result={workstreams:[work('a:active',{state:'active',workers:[fresh],handoff_at:local(2026,8,8)}),work('a:lifecycle',{state:'active',workers:[]}),work('a:old',{workers:[expired]})],recently_rested:[]};
 assert.deepEqual(F.board(result,now).active.map(item=>item.worker.session),['fresh']);
 assert.deepEqual(F.board(result,now).evidence.map(item=>item.work.key),['a:active']);
 assert.deepEqual(F.board(result,now,false).active,[]);
});

test('latest evidence is one timestamped item per workstream',()=>{
 const result={workstreams:[work('a:one',{handoff_at:local(2026,8,8),local_reports:[{id:'new',created_at:local(2026,8,10),payload:{packet:{summary:'Newest report'}}},{id:'old',created_at:local(2026,8,7),payload:{packet:{summary:'Old report'}}}]}),work('a:two',{handoff_at:local(2026,8,9),handoff_summary:'Second handoff'})]};
 const evidence=F.board(result).evidence;
 assert.equal(evidence.length,2);assert.equal(evidence[0].work.key,'a:one');assert.equal(evidence[0].kind,'report');assert.equal(evidence[0].summary,'Newest report');
});

test('month is a Monday-first six-week grid with events on exact local dates',()=>{
 const date=local(2026,8,10),events=[{id:'one',date:F.dateKey(date)}],view=F.month(2026,8,events);
 assert.equal(view.days.length,42);assert.equal(view.days[0].date.getDay(),1);
 assert.equal(view.days.find(day=>day.key===F.dateKey(date)).events.length,1);
 assert.equal(view.days.filter(day=>day.inMonth).length,30);
});

test('empty and invalid timestamps remain absent rather than becoming epoch activity',()=>{
 assert.equal(F.dateKey(''),null);assert.equal(F.dateKey(null),null);assert.equal(F.time(undefined),null);
 assert.deepEqual(F.events({workstreams:[work('a:none')]}),[]);
});
