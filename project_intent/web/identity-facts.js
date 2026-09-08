/* Deterministic visual identity only; not a unique identifier or security proof. */
(function(root,factory){const api=factory();if(typeof module==='object'&&module.exports)module.exports=api;else root.IntentIdentity=api;})(typeof globalThis!=='undefined'?globalThis:this,()=>{
 function pattern(scope,id){
  const seed=JSON.stringify([String(scope),String(id)]);let state=2166136261;
  for(const c of seed)state=Math.imul(state^c.charCodeAt(0),16777619)>>>0;
  const hue=state%360,cells=[];
  const next=()=>{state^=state<<13;state^=state>>>17;state^=state<<5;return state>>>0;};
  for(let y=0;y<5;y++)for(let x=0;x<3;x++)if(next()%2){cells.push([x,y]);if(x<2)cells.push([4-x,y]);}
  if(!cells.length)cells.push([2,2]);
  return {hue,cells};
 }
 function design(value){return ['plan','studio','console'].includes(value)?value:'default';}
 return {pattern,design};
});
