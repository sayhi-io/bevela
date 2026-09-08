/* Opt-in visual surface; consumes the existing normalized result only. */
(() => {
 'use strict';
 const F=window.WorkstreamMapFacts, NS='http://www.w3.org/2000/svg';
 let observation=null, selected=null, focused='', includeClosed=false, connected=true, dialogKey=null, dialogSignature=null;
 const host=$('workstream-map'), rail=$('map-seams'), canvas=$('map-canvas'), modal=$('seam-detail');
 function svg(tag,attrs={},text){const n=document.createElementNS(NS,tag);for(const [k,v]of Object.entries(attrs))n.setAttribute(k,v);if(text!==undefined)n.textContent=text;return n;}
 function action(n,label,fn,id){n.setAttribute('role','button');n.setAttribute('tabindex','0');n.setAttribute('aria-label',label);n.dataset.mapFocus=id;n.addEventListener('click',fn);n.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();fn();}});return n;}
 function button(text,fn,cls=''){const b=el('button',text,cls);b.type='button';b.onclick=fn;return b;}
 function works(){return (observation?.workstreams||[]).filter(w=>includeClosed||['active','blocked','ready'].includes(w.state)).sort((a,b)=>F.order(a.key,b.key));}
 function index(){return F.seams(observation,works(),Date.now(),connected);}
 function wrap(text,max=25){const words=String(text).split(/\s+/),lines=[''];for(const word of words){const i=lines.length-1;if(lines[i].length+word.length+1>max&&lines[i])lines.push(word);else lines[i]+=(lines[i]?' ':'')+word;}return lines;}
 function choose(id){selected=id;focused='';$('map-focus').value='';draw();}
 function details(seam){
  if(!seam)return;
  dialogKey=seam.key;
  const architecture=F.architecture(observation,seam);
  const signature=JSON.stringify([seam,architecture,observation.attention,connected]);
  if(signature===dialogSignature&&modal.open)return;
  dialogSignature=signature;
  const body=clear('seam-content');$('seam-title').textContent=seam.boundary;
  body.append(el('p',seam.scope,'identifier'),el('p',seam.convergence?.meaning||'Boundary declarations only. No normalized convergence relationship is available.','map-caveat'));
  if(!connected)body.append(el('p','Retained observation. Worker activity is unknown until the API reconnects.','map-caveat'));
  const asec=section(body,'Architecture on this boundary','architecture');
  if(!architecture.length)asec.append(el('p','No architecture with this exact boundary and API-declared applicability is available. Other Workstream constraints may still apply.'));
  for(const a of architecture){const d=el('details',undefined,'technical');d.append(el('summary',a.kind+' · '+a.key+' · r'+a.revision+' · '+a.state),el('p',a.statement));
   for(const {work}of seam.members){const claim=(work.claims||[]).find(c=>c.invariant===a.key);if(claim)d.append(el('p',work.id+' · '+claim.status+' · architecture r'+claim.architecture_revision+' / evidence '+(claim.evidence_revision===null?'not bound':'r'+claim.evidence_revision)),el('p','Subject: '+(claim.subject||'not bound')),el('p',claim.verification));}
   asec.append(d);
  }
  asec.append(el('p','Revision-current means matching declarations, not independently verified conformance.','quiet'));
  const nearby=section(body,'Workstreams & worker declarations','worker');
  for(const {work,port}of seam.members){const item=el('article',undefined,'map-member');item.append(el('h4',work.title||work.statement||work.id),el('p',work.id+' · lifecycle '+work.state+' / provider '+(work.provider_lifecycle||'unknown'),'identifier'),el('p',port.declared?'Workstream declares this boundary.':'Boundary is present only in a fresh worker declaration.'));
   for(const [name,rows]of [['Touching',port.touching],['Approaching',port.approaching]])for(const p of rows)item.append(el('p',name+' (declared): '+p.session+' · '+p.working),workerCheckout(p));
   if(!port.touching.length&&!port.approaching.length)item.append(el('p','No fresh touching/approaching declaration here. Activity elsewhere is unknown.','quiet'));
   item.append(button('Open full Workstream context',()=>showDetail(work.key)));
   const detail=el('details',undefined,'technical');detail.append(el('summary','Workstream-level evidence, reports & relationships — not seam adjudication'));
   detail.append(el('p','Readiness: '+JSON.stringify(work.readiness||{})),el('p','Integration dependency (as declared): '+(work.integration_dependency||'not recorded')));
   for(const ref of work.pull_requests||[])detail.append(el('p','PR relationship: '+ref.relationship+' · '+ref.url));
   const groups=(observation.initiatives||[]).filter(i=>(i.workstreams||[]).includes(work.key));for(const i of groups)detail.append(el('p','Initiative membership: '+i.title+' · '+i.scope));
   detail.append(el('p',work.divergence_coverage));for(const d of work.divergences||[])detail.append(el('p','Workstream divergence: '+JSON.stringify(d)));
   if(!work.divergences?.length)detail.append(el('p','No divergence recorded; not proof of no drift.'));
   for(const e of work.completion_evidence||[])detail.append(el('p',e));
   detail.append(el('p','Latest provider handoff: '+(work.handoff_summary||'not recorded')),el('p','Report coverage: '+work.report_coverage));
   for(const r of work.local_reports||[])detail.append(reportCard(r,work,true));
   item.append(detail);nearby.append(item);
  }
  const attention=section(body,'Existing Needs Attention','proof');
  const relevant=(observation.attention||[]).filter(a=>a.scope===seam.scope&&(!a.workstream||seam.members.some(m=>m.work.key===a.workstream)));
  for(const a of relevant)attention.append(el('p',a.kind+' · '+a.message));
  if(!relevant.length)attention.append(el('p','No matching attention item in this observation. Not a safety assessment.'));
  body.append(el('p','No seam-level coordination outcome is available. Reports, integration notes and divergence proposals above remain Workstream-level facts; none mean this seam is mended.','map-caveat'));
  if(!modal.open)modal.showModal();
 }
 function jelly(work,position,seamList,now){
  const {x,y}=position, group=svg('g',{transform:`translate(${x},${y})`,class:'map-jelly'});
  const body=svg('path',{d:'M-126 -30 C-124 -86 -79 -111 -21 -112 C33 -126 108 -96 124 -46 C148 3 125 69 80 92 C36 121 -28 111 -77 99 C-132 84 -151 27 -126 -30Z',class:'jelly-body'});
  group.append(body);
  const center=action(svg('g',{class:'jelly-center'}),'Open '+(work.title||work.statement||work.id),()=>showDetail(work.key),'work:'+work.key);
  center.append(svg('rect',{x:-100,y:-58,width:200,height:121,fill:'transparent',rx:12}));
  if(window.workIdenticon){const mark=window.workIdenticon(work);mark.setAttribute('x','-14');mark.setAttribute('y','-88');mark.setAttribute('width','28');mark.setAttribute('height','28');center.append(mark);}
  const lines=wrap(work.title||work.statement||work.id,24);
  const title=svg('text',{'text-anchor':'middle',class:'jelly-title',y:-31});
  for(const [i,line]of lines.slice(0,3).entries())title.append(svg('tspan',{x:0,dy:i?20:0},line.length>27?line.slice(0,26)+'…':line));
  center.append(title,svg('title',{},work.statement),svg('text',{'text-anchor':'middle',y:40,class:'jelly-id'},work.id));group.append(center);
  const fresh=connected?(work.workers||[]).filter(p=>F.fresh(p,now)):[];
  group.append(svg('text',{'text-anchor':'middle',y:61,class:'jelly-status'},fresh.length?`${fresh.length} fresh lease${fresh.length===1?'':'s'}`:'Activity not observed live'));
  group.append(svg('text',{'text-anchor':'middle',y:152,class:'jelly-lifecycle'},'Lifecycle · '+work.state));
  const attention=(observation.attention||[]).filter(a=>a.workstream===work.key);
  if(attention.length){const b=action(svg('g',{class:'jelly-attention'}),attention.length+' attention items for '+work.id,()=>$('attention-dialog').showModal(),'attention:'+work.key);b.append(svg('rect',{x:67,y:-115,width:42,height:24,rx:12}),svg('text',{x:88,y:-98,'text-anchor':'middle'},String(attention.length)));group.append(b);}
  const ports=F.ports(work,now,connected), endpoints=[];
  for(const [i,p]of ports.slice(0,12).entries()){
   const a=-Math.PI/2+i*2*Math.PI/Math.min(ports.length,12),px=Math.cos(a)*132,py=Math.sin(a)*117;
   const seam=seamList.find(s=>s.scope===work.scope_id&&s.boundary===p.boundary),number=seamList.indexOf(seam)+1;
   const port=action(svg('g',{class:'map-port'+(selected===seam.key?' selected':'')}),`${p.boundary}; ${p.declared?'declared boundary':'worker declaration'}; ${p.touching.length} touching; ${p.approaching.length} approaching`,()=>{choose(seam.key);details(index().find(s=>s.key===seam.key));},'port:'+work.key+':'+p.boundary);
   port.append(svg('circle',{cx:px,cy:py,r:13,class:p.declared?'port-declared':'port-worker'}),svg('text',{x:px,y:py+4,'text-anchor':'middle',class:'port-number'},String(number)),svg('title',{},p.boundary));
   if(p.touching.length)port.append(svg('circle',{cx:px*0.77,cy:py*0.77,r:5,class:'worker-touching'}));
   if(p.approaching.length)port.append(svg('circle',{cx:px*0.64,cy:py*0.64,r:8,class:'worker-approaching'}));
   group.append(port);endpoints.push({boundary:p.boundary,x:x+px,y:y+py,work:work.key});
  }
  if(ports.length>12)group.append(svg('text',{'text-anchor':'middle',y:173,class:'jelly-status'},`${ports.length-12} more boundaries in index / full context`));
  return {group,endpoints};
 }
 function draw(){
  if(!observation)return;
  const activeFocus=document.activeElement?.dataset?.mapFocus;
  const all=works(),seamList=index(),selection=seamList.find(s=>s.key===selected);
  if(selected&&!selection)selected=null;
  rail.replaceChildren();canvas.replaceChildren();
  for(const [i,s]of seamList.entries()){
   const b=button('',()=>choose(s.key),'seam-choice');b.dataset.mapFocus='seam:'+s.key;b.setAttribute('aria-pressed',String(selected===s.key));
   b.append(el('span',String(i+1).padStart(2,'0'),'seam-index'),el('span',s.boundary,'seam-name'),el('small',s.scope+' · '+s.members.length+' visible'+(s.convergence?' · convergence':'')));
   rail.append(b);
  }
  if(!seamList.length)rail.append(el('p','No boundary declarations in this view.','quiet'));
  const shown=all.filter(w=>(!focused||w.key===focused)&&(!selection||selection.members.some(m=>m.work.key===w.key)));
  $('map-summary').textContent=`${shown.length} of ${all.length} Workstreams · ${seamList.length} scoped boundaries · ${seamList.filter(s=>s.convergence).length} normalized convergence groups`;
  $('map-selection').textContent=selection?selection.boundary:focused?'Workstream focus':'Architectural surfaces';
  $('map-inspect').hidden=!selection;
  $('map-inspect').onclick=()=>details(selection);
  $('map-observation').textContent=(connected?'Observed ':'Disconnected · retained observation ')+observation.observed_at+'. Positions and size are layout only; nothing is scored.';
  for(const scope of observation.scopes||[]){
   const members=shown.filter(w=>w.scope_id===scope.id);if(!members.length)continue;
   const block=el('section',undefined,'map-scope');block.append(el('h3',scope.label||scope.id),el('p',scope.id+' · provider '+scope.provider_status+' · captured '+(scope.source?.captured_at||'unknown')+' · execution '+scope.execution.status,'map-source'));
   const columns=Math.max(1,Math.min(3,Math.floor((canvas.clientWidth||760)/340))),width=columns*350,rows=Math.ceil(members.length/columns);
   const picture=svg('svg',{viewBox:`0 0 ${width} ${rows*340+15}`,class:'map-picture',role:'group','aria-label':scope.id+' Workstream architectural surfaces'});
   const links=svg('g',{'aria-hidden':'true',class:'map-links'}),nodes=svg('g');picture.append(links,nodes);
   const ends=[];for(const [i,w]of members.entries()){const item=jelly(w,{x:(i%columns)*350+175,y:Math.floor(i/columns)*340+145},seamList,Date.now());nodes.append(item.group);ends.push(...item.endpoints);}
   if(selection?.scope===scope.id&&selection.convergence){
    const endpoints=ends.filter(p=>p.boundary===selection.boundary&&selection.convergence.workstreams.includes(p.work));
    // A visual bus, not a directional dependency. Only the selected server-declared group.
    for(let i=1;i<endpoints.length;i++){const a=endpoints[i-1],b=endpoints[i];links.append(svg('path',{d:`M${a.x} ${a.y} C${a.x} ${a.y+50} ${b.x} ${b.y+50} ${b.x} ${b.y}`,class:'convergence-band'}));}
   }
   block.append(picture);canvas.append(block);
  }
  if(!shown.length)canvas.append(el('p','No Workstreams match these display filters. Reset focus or include other lifecycle states.','empty'));
  if(activeFocus){const target=[...host.querySelectorAll('[data-map-focus]')].find(n=>n.dataset.mapFocus===activeFocus);target?.focus({preventScroll:true});}
  if(modal.open&&dialogKey){const seam=seamList.find(s=>s.key===dialogKey);if(seam)details(seam);else modal.close();}
 }
 function update(result){observation=result;connected=true;const focus=$('map-focus'),previous=focus.value;focus.replaceChildren(el('option','All Workstreams'));focus.firstChild.value='';for(const w of result.workstreams){const o=el('option',w.id+' · '+short(w.title||w.statement,60));o.value=w.key;focus.append(o);}focus.value=previous;focused=focus.value;draw();}
 $('map-focus').onchange=()=>{focused=$('map-focus').value;selected=null;if(focused){const w=observation.workstreams.find(w=>w.key===focused);if(w&&!['active','blocked','ready'].includes(w.state)){$('map-closed').checked=true;includeClosed=true;}}draw();};
 $('map-closed').onchange=()=>{includeClosed=$('map-closed').checked;draw();};
 $('map-reset').onclick=()=>{selected=null;focused='';$('map-focus').value='';draw();};
 $('seam-close').onclick=()=>modal.close();modal.addEventListener('close',()=>{dialogKey=null;dialogSignature=null;});
 const original=render;render=function(result){original(result);update(result);};
 $('scope').addEventListener('change',()=>{observation=null;selected=null;focused='';rail.replaceChildren();canvas.replaceChildren();$('map-summary').textContent='Loading selected scope…';$('map-observation').textContent='';$('map-selection').textContent='Architectural surfaces';$('map-focus').replaceChildren();$('map-inspect').hidden=true;modal.close();});
 new MutationObserver(()=>{if(observation&&!$('error').hidden){connected=false;draw();}}).observe($('error'),{attributes:true,attributeFilter:['hidden']});
 let resize;new ResizeObserver(()=>{clearTimeout(resize);resize=setTimeout(()=>{if(!host.hidden)draw();},120);}).observe(canvas);
 window.addEventListener('hashchange',()=>{if(location.hash==='#map')draw();});
 if(data)update(data);
})();
