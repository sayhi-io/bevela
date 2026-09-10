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
 // A fixed 15-minute window, matching the observer's retained numeric history.
 // Never bridge unknown samples, lease epochs, or long reporting gaps.
 function sparkline(points=[],now=Date.now()){
  const end=now/1000,start=end-900,segments=[];
  let segment=[],previous=null;
  const flush=()=>{if(segment.length)segments.push(segment);segment=[];};
  for(const p of points){
   if(!p||!Number.isFinite(p.at)||p.at<start||p.at>end){flush();previous=null;continue;}
   if(p.break_before||(previous!==null&&(p.at<=previous||p.at-previous>120)))flush();
   if(Number.isFinite(p.value)&&p.value>=0)segment.push(p);else flush();
   previous=p.at;
  }
  flush();
  const maximum=Math.max(1,...segments.flat().map(p=>p.value));
  const paths=segments.filter(s=>s.length>1).map(s=>{
   const xy=s.map(p=>({x:2+(p.at-start)/900*596,y:28-p.value/maximum*24}));
   const slopes=xy.slice(1).map((p,i)=>(p.y-xy[i].y)/(p.x-xy[i].x));
   // Limited tangents keep every curve inside its neighboring sample range:
   // smoothing cannot manufacture spikes or negative throughput.
   const tangents=xy.map((_,i)=>{
    if(i===0)return slopes[0];if(i===xy.length-1)return slopes.at(-1);
    const a=slopes[i-1],b=slopes[i];
    return a*b<=0?0:Math.sign(a)*Math.min(Math.abs(a),Math.abs(b));
   });
   const n=v=>v.toFixed(3);
   let d=`M${n(xy[0].x)} ${n(xy[0].y)}`;
   for(let i=1;i<xy.length;i++){
    const a=xy[i-1],b=xy[i],dx=(b.x-a.x)/3;
    d+=` C${n(a.x+dx)} ${n(a.y+dx*tangents[i-1])} ${n(b.x-dx)} ${n(b.y-dx*tangents[i])} ${n(b.x)} ${n(b.y)}`;
   }
   return d;
  });
  return {paths,maximum};
 }
 const api={sessions,assignments,sparkline};if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.WorkerGroupFacts=api;
})(typeof globalThis!=='undefined'?globalThis:this);
