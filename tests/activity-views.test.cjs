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

test('calendar adds usable PR observations and scoped local Git commits without inventing work links',()=>{
 const observed=local(2026,8,10,10),committed=local(2026,8,10,9),result={workstreams:[work('a:one',{pull_requests:[{repository:'https://github.com/sayhi-io/bevela',number:14,url:'https://github.com/sayhi-io/bevela/pull/14',relationship:'implementation',observation_status:'last-known',observation:{observed_at:observed,state:'merged'}}]})],local_git:{status:'observed',commits:[{scope:'a',repository:'bevela',oid:'a'.repeat(40),committed_at:committed,subject:'Add calendar evidence',publication:'local-only'},{scope:'a',repository:'bad',oid:'short',committed_at:committed,subject:'invalid',publication:'unknown'}]}};
 const events=F.events(result),pr=events.find(event=>event.type==='pull-request'),commit=events.find(event=>event.type==='commit');
 assert.equal(events.length,2);assert.equal(pr.label,'Pull request observed · merged');assert.equal(pr.ref.number,14);
 assert.equal(commit.work,null);assert.equal(commit.commit.publication,'local-only');assert.equal(commit.summary,'Add calendar evidence');
});

test('PR references without usable observations and malformed local commits stay off calendar',()=>{
 const result={workstreams:[work('a:one',{pull_requests:[{observation_status:'not-observed',observation:{observed_at:local(2026,8,10)}}]})],local_git:{commits:[null,{scope:'a',repository:'repo',oid:'b'.repeat(40),committed_at:'bad',subject:'bad',publication:'local-only'}]}};
 assert.deepEqual(F.events(result),[]);
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
