/* Transient indexes over observatory/v1, never provider state or inferred semantics. */
(function(root){
 'use strict';
 const order=(a,b)=>a<b?-1:a>b?1:0;
 const key=(scope,boundary)=>JSON.stringify([scope,boundary]);
 function fresh(worker,now=Date.now()){
  return worker.status==='active'&&Date.parse(worker.heartbeat_at)<=now&&Date.parse(worker.expires_at)>now;
 }
 function ports(work,now=Date.now(),connected=true){
  const names=new Set(work.boundaries||[]);
  if(connected)for(const p of work.workers||[])if(fresh(p,now))for(const name of [...(p.touching_seams||[]),...(p.approaching||[])])names.add(name);
  return [...names].sort(order).map(boundary=>({boundary,declared:(work.boundaries||[]).includes(boundary),
   touching:connected?(work.workers||[]).filter(p=>fresh(p,now)&&(p.touching_seams||[]).includes(boundary)):[],
   approaching:connected?(work.workers||[]).filter(p=>fresh(p,now)&&(p.approaching||[]).includes(boundary)):[]}));
 }
 function seams(result,works,now=Date.now(),connected=true){
  const map=new Map();
  for(const work of works)for(const port of ports(work,now,connected)){
   const id=key(work.scope_id,port.boundary);
   if(!map.has(id))map.set(id,{key:id,scope:work.scope_id,boundary:port.boundary,members:[],convergence:null});
   map.get(id).members.push({work,port});
  }
  for(const seam of map.values())seam.convergence=(result.convergence||[]).find(c=>c.scope===seam.scope&&c.boundary===seam.boundary)||null;
  return [...map.values()].sort((a,b)=>order(a.scope,b.scope)||order(a.boundary,b.boundary));
 }
 function architecture(result,seam){
  const members=new Set(seam.members.map(m=>m.work.key));
  // The API computes applicability. Boundary match alone is never an authority grant.
  return (result.architecture||[]).filter(a=>(a.boundaries||[]).includes(seam.boundary)&&(a.workstreams||[]).some(k=>members.has(k)));
 }
 const api={key,fresh,ports,seams,architecture,order};
 if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.WorkstreamMapFacts=api;
})(typeof globalThis!=='undefined'?globalThis:this);
