/* Derived presentation facts only; never infer work from an empty timestamp. */
(function(root){
 'use strict';
 const eventLabels={handoff:'Provider handoff',report:'Worker report',release:'Reported inactive','pull-request':'Pull request observation',commit:'Git commit'};
 const time=value=>{const parsed=Date.parse(value);return Number.isFinite(parsed)?parsed:null;};
 const dateKey=value=>{
  const at=typeof value==='number'?value:time(value);if(at===null||!Number.isFinite(at))return null;
  const date=new Date(at),part=n=>String(n).padStart(2,'0');
  return `${date.getFullYear()}-${part(date.getMonth()+1)}-${part(date.getDate())}`;
 };
 function events(result){
  const rows=[],works=new Map((result.workstreams||[]).map(work=>[work.key,work]));
  const add=(type,at,work,extra={})=>{const value=time(at);if(value===null||(!work&&type!=='commit'))return;rows.push({type,label:eventLabels[type],at:value,date:dateKey(value),work,...extra});};
  for(const work of works.values()){
   add('handoff',work.handoff_at,work,{id:`handoff:${work.key}:${work.handoff_at}`,summary:work.handoff_summary||work.statement||'Handoff recorded.'});
   for(const report of work.local_reports||[])add('report',report.created_at,work,{id:`report:${work.key}:${report.id||report.created_at}`,summary:report.payload?.packet?.summary||'Worker report recorded.',report});
   for(const ref of work.pull_requests||[]){const observation=ref.observation_status==='last-known'?ref.observation:null;if(observation)add('pull-request',observation.observed_at,work,{id:`pull-request:${work.key}:${ref.repository}:${ref.number}:${observation.observed_at}`,label:`Pull request observed · ${observation.state||'state unknown'}`,summary:`${ref.repository.replace('https://','')} #${ref.number} · ${ref.relationship}`,ref});}
  }
  for(const release of result.recently_rested||[]){const work=works.get(release.workstream);add('release',release.reported_inactive_at,work,{id:`release:${release.workstream}:${release.session}:${release.reported_inactive_at}`,summary:release.working||'Registration reported inactive.',session:release.session,release});}
  for(const commit of result.local_git?.commits||[]){if(!commit||typeof commit.repository!=='string'||typeof commit.scope!=='string'||!/^[a-f0-9]{40}$|^[a-f0-9]{64}$/.test(commit.oid||'')||!['local-only','remote-tracking','unknown'].includes(commit.publication))continue;add('commit',commit.committed_at,null,{id:`commit:${commit.repository}:${commit.oid}`,scope:commit.scope,summary:commit.subject||'Commit without a subject',commit});}
  return rows.sort((a,b)=>b.at-a.at||a.id.localeCompare(b.id));
 }
 function filterEvents(rows,options={}){
  const query=String(options.query||'').trim().toLocaleLowerCase(),type=String(options.type||''),sort=String(options.sort||'newest');
  const identity=row=>row.work?.key||`${row.scope||''} ${row.commit?.repository||''}`;
  const searchable=row=>[row.label,row.type,row.summary,identity(row),row.work?.title,row.work?.statement,row.work?.provider_identifier,row.id,row.session,row.report?.payload?.session,row.commit?.oid,row.commit?.publication,row.ref?.repository,row.ref?.number,row.ref?.relationship,row.ref?.observation?.state].filter(value=>value!==undefined&&value!==null).join(' ').toLocaleLowerCase();
  const result=rows.filter(row=>(!type||row.type===type)&&(!query||searchable(row).includes(query))).slice();
  if(sort==='oldest')result.sort((a,b)=>a.at-b.at||a.id.localeCompare(b.id));
  else if(sort==='type')result.sort((a,b)=>a.label.localeCompare(b.label)||b.at-a.at||a.id.localeCompare(b.id));
  else if(sort==='workstream')result.sort((a,b)=>identity(a).localeCompare(identity(b))||b.at-a.at||a.id.localeCompare(b.id));
  else result.sort((a,b)=>b.at-a.at||a.id.localeCompare(b.id));
  return result;
 }
 const fresh=(worker,now)=>worker?.status==='active'&&time(worker.heartbeat_at)!==null&&time(worker.expires_at)!==null&&time(worker.heartbeat_at)<=now&&time(worker.expires_at)>now;
 function board(result,now=Date.now(),connected=true){
  const works=new Map((result.workstreams||[]).map(work=>[work.key,work])),active=[];
  if(connected)for(const work of works.values())for(const worker of work.workers||[])if(fresh(worker,now))active.push({id:`active:${work.key}:${worker.session}`,work,worker,at:time(worker.heartbeat_at)});
  active.sort((a,b)=>b.at-a.at||a.id.localeCompare(b.id));
  const released=(result.recently_rested||[]).flatMap(release=>{const work=works.get(release.workstream),at=time(release.reported_inactive_at);return work&&at!==null?[{id:`release:${release.workstream}:${release.session}:${release.reported_inactive_at}`,work,release,at}]:[];}).sort((a,b)=>b.at-a.at||a.id.localeCompare(b.id));
  const evidence=[];
  for(const work of works.values()){
   const candidates=[];
   if(time(work.handoff_at)!==null)candidates.push({kind:'handoff',at:time(work.handoff_at),summary:work.handoff_summary||work.statement||'Handoff recorded.'});
   for(const report of work.local_reports||[])if(time(report.created_at)!==null)candidates.push({kind:'report',at:time(report.created_at),summary:report.payload?.packet?.summary||'Worker report recorded.',report});
   candidates.sort((a,b)=>b.at-a.at||a.kind.localeCompare(b.kind));
   if(candidates[0])evidence.push({id:`evidence:${work.key}`,work,...candidates[0]});
  }
  evidence.sort((a,b)=>b.at-a.at||a.id.localeCompare(b.id));
  return {active,released,evidence};
 }
 function month(year,monthIndex,rows=[]){
  const first=new Date(year,monthIndex,1,12),mondayOffset=(first.getDay()+6)%7,byDate=new Map();
  for(const row of rows){if(!row.date)continue;if(!byDate.has(row.date))byDate.set(row.date,[]);byDate.get(row.date).push(row);}
  const days=[];
  for(let index=0;index<42;index++){
   const date=new Date(year,monthIndex,1-mondayOffset+index,12),key=dateKey(date.getTime());
   days.push({date,key,day:date.getDate(),inMonth:date.getMonth()===monthIndex,events:byDate.get(key)||[]});
  }
  return {year,monthIndex,days};
 }
 function week(anchor,rows=[]){
  const date=new Date(anchor);if(!Number.isFinite(date.getTime()))return {days:[]};
  date.setHours(12,0,0,0);date.setDate(date.getDate()-((date.getDay()+6)%7));
  const byDate=new Map();
  for(const row of rows){if(!row.date)continue;if(!byDate.has(row.date))byDate.set(row.date,[]);byDate.get(row.date).push(row);}
  const days=[];
  for(let index=0;index<7;index++){const day=new Date(date);day.setDate(date.getDate()+index);const key=dateKey(day.getTime());days.push({date:day,key,day:day.getDate(),inMonth:true,events:byDate.get(key)||[]});}
  return {days};
 }
 function preview(value,limit=140){
  const normalized=String(value||'').replace(/\s+/g,' ').trim().replace(/\b[a-f0-9]{24,}\b/gi,hash=>hash.slice(0,8)+'…');
  const clause=normalized.match(/^(.{24,}?)(?:;\s+|\.\s+(?=[A-Z]))/);
  const text=clause?clause[1]+'…':normalized;
  if(text.length<=limit)return text;
  const cut=text.slice(0,limit),space=cut.lastIndexOf(' ');
  return (space>limit/2?cut.slice(0,space):cut)+'…';
 }
 const api={events,filterEvents,preview,board,month,week,dateKey,time,eventLabels};
 if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.ActivityViewsFacts=api;
})(typeof globalThis!=='undefined'?globalThis:this);
