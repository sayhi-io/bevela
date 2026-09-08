(function(root){
 'use strict';
 function sessions(work,now=Date.now(),connected=true){
  const rows=new Map();
  for(const p of work.workers||[]){if(!p.session)continue;const old=rows.get(p.session);rows.set(p.session,{id:p.session,presence:p,ambiguous:!!old});}
  const metrics=work.activity?.sessions||[work.activity||{}];
  for(const a of metrics){if(!a.session)continue;const r=rows.get(a.session)||{id:a.session};if(r.metric)r.ambiguous=true;r.metric=a;rows.set(a.session,r);}
  for(const r of rows.values()){
   const p=r.presence,a=r.metric,age=now/1000-a?.last_report_at;
   r.present=connected&&!r.ambiguous&&p?.status==='active'&&Date.parse(p.heartbeat_at)<=now&&Date.parse(p.expires_at)>now;
   const last=a?.points?.at(-1),sampleAge=now/1000-last?.at;
   const recent=connected&&!r.ambiguous&&a?.status==='recent'&&Number.isFinite(a.last_report_at)&&age>=0&&age<=90&&(!p||r.present);
   r.rate=recent&&Number.isFinite(last?.value)&&last.value>=0&&sampleAge>=0&&sampleAge<=90?last.value:null;
   r.reporting=recent;
   r.kind=!connected?'unknown':r.ambiguous?'unknown':recent?'reporting':r.present?'present':'historical';
   r.label=!connected?'Observation disconnected':r.ambiguous?'Ambiguous registration':r.rate!==null?r.rate.toFixed(1)+' tok/s':recent?'Recent report · rate unknown':r.present?'Present · unmeasured':p?.status==='inactive'?'Released':p?.status==='expired'||p?.status==='active'?'Lease expired · activity unknown':'Last observation';
  }
  return [...rows.values()].sort((a,b)=>Number(b.reporting)-Number(a.reporting)||Number(b.present)-Number(a.present)||a.id.localeCompare(b.id));
 }
 function assignments(result,scope,session){return (result.workstreams||[]).filter(w=>w.scope_id===scope&&sessions(w).some(r=>r.id===session));}
 const api={sessions,assignments};if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.WorkerGroupFacts=api;
})(typeof globalThis!=='undefined'?globalThis:this);
