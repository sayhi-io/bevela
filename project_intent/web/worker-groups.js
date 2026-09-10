/* Observatory-only presentation adapter. Classic cards and all API semantics remain. */
(() => {
 const F=window.WorkerGroupFacts;
 let connected=true,selected=null,historyKey=null,redrawHistory=null;
 const modal=el('dialog');modal.id='worker-detail';modal.setAttribute('aria-labelledby','worker-detail-title');document.body.append(modal);
 function label(id){return id.length>25?id.slice(0,12)+'…'+id.slice(-6):id;}
 function agentIcon(){const g=icon('environment');g.querySelector('path').setAttribute('d','M5 5h14v14H5zM9 9h6v6H9zM9 2v3m6-3v3M9 19v3m6-3v3M2 9h3m-3 6h3m14-6h3m-3 6h3');return g;}
 function hint(button,text){button.setAttribute('aria-label',text);button.append(el('span',text,'card-tooltip'));return button;}
 function copyButton(id){const b=el('button','Copy ID');b.onclick=async()=>{try{await navigator.clipboard.writeText(id);b.textContent='Copied';}catch{b.textContent='Select ID to copy';}};return b;}
 const historyModal=el('dialog');historyModal.id='session-history';historyModal.setAttribute('aria-labelledby','session-history-title');document.body.append(historyModal);
 function history(work){historyKey=work.key;historyModal.replaceChildren();const top=el('div',undefined,'detail-top'),h=el('h2','Session history');h.id='session-history-title';const close=el('button','Close ×');close.onclick=()=>historyModal.close();top.append(h,close);historyModal.append(top,el('p',work.title||work.statement),el('p','Historical registrations, not a count of people or distinct agents. Released means the registration ended; unknown means observation is unavailable.','section-note'));const search=el('input');search.type='search';search.placeholder='Find session or working declaration';search.setAttribute('aria-label','Search session history');const list=el('div',undefined,'session-history-list');const draw=()=>{const current=data?.workstreams.find(w=>w.key===historyKey);if(!current){historyModal.close();return;}const focused=document.activeElement,focusRow=focused?.closest('.session-history-row')?.dataset.session,focusLabel=focused?.textContent,scroll=historyModal.scrollTop;list.replaceChildren();for(const row of F.sessions(current,Date.now(),connected).filter(r=>(r.id+' '+(r.presence?.working||'')).toLowerCase().includes(search.value.toLowerCase()))){const item=el('div',undefined,'session-history-row');item.dataset.session=row.id;const id=el('code',row.id);const open=el('button','Inspect');open.onclick=()=>inspect(current.scope_id,row.id,current.key);item.append(id,el('span',row.label),copyButton(row.id),open,el('p',row.presence?.working||'No working declaration recorded.'));list.append(item);}if(!list.children.length)list.append(el('p','No matching registrations.'));if(focusRow){const row=[...list.children].find(n=>n.dataset.session===focusRow);([...row?.querySelectorAll('button')||[]].find(b=>b.textContent===focusLabel)||search).focus({preventScroll:true});}historyModal.scrollTop=scroll;};redrawHistory=draw;search.oninput=draw;historyModal.append(search,list);draw();historyModal.showModal();search.focus();}
 historyModal.addEventListener('close',()=>{const key=historyKey;historyKey=null;redrawHistory=null;[...document.querySelectorAll('.work-group')].find(n=>n.dataset.group===key&&n.getClientRects().length)?.querySelector('.history-trigger')?.focus({preventScroll:true});});
 historyModal.addEventListener('click',event=>{if(event.target===historyModal){const r=historyModal.getBoundingClientRect();if(event.clientX<r.left||event.clientX>r.right||event.clientY<r.top||event.clientY>r.bottom)historyModal.close();}});
 function visibleChip(id,key){return [...document.querySelectorAll('.worker-chip')].find(n=>n.dataset.session===id&&n.dataset.group===key&&n.getClientRects().length);}
 function inspect(scope,id,workKey){
  const scroll=modal.scrollTop,focusIndex=[...modal.querySelectorAll('button')].indexOf(document.activeElement);selected={scope,id,workKey:workKey||selected?.workKey};modal.replaceChildren();
  const top=el('div',undefined,'detail-top'),title=el('h2','Session observation');title.id='worker-detail-title';const close=el('button','Close ×');close.onclick=()=>modal.close();top.append(title,close);modal.append(top,el('p',id,'identifier'),scopeName('p',scope));
  const works=F.assignments(data,scope,id);
  if(!works.length){modal.close();return;}
  modal.append(el('p','A session observation, not a Workstream or execution grant. Rates are reported output-token deltas per reporting interval—not instantaneous inference speed or per-Workstream allocation.','section-note'));
  if(works.length>1)modal.append(el('p','Shared registration across '+works.length+' visible Workstreams. Do not add these rates together.','worker-shared-note'));
  for(const w of works){const r=F.sessions(w,Date.now(),connected).find(r=>r.id===id);const s=section(modal,w.title||w.statement||w.id,'worker');s.append(el('strong',r.label),el('p',r.presence?.working||'No current working declaration.'));
   if(r.presence)s.append(workerCheckout(r.presence));
   if(r.metric){s.append(el('p','Last report: '+(Number.isFinite(r.metric.last_report_at)?new Date(r.metric.last_report_at*1000).toISOString():'not observed'),'identifier'),el('p',r.metric.history_coverage||r.metric.meaning||'Available reported history only.','section-note'));s.append(activityChart({...w,activity:{...r.metric,status:r.rate===null?'Retained history · '+r.label:r.metric.status}}));}
   else s.append(el('p','No telemetry attachment for this exact registration. Presence does not measure inference.','section-note'));
   const open=el('button','Open Workstream context');open.onclick=()=>showDetail(w.key);s.append(open);
  }
  if(!modal.open)modal.showModal();else {modal.scrollTop=scroll;if(focusIndex>=0)modal.querySelectorAll('button')[focusIndex]?.focus({preventScroll:true});}
 }
 modal.addEventListener('close',()=>{const previous=selected;selected=null;if(previous){if(historyModal.open){const row=[...historyModal.querySelectorAll('.session-history-row')].find(n=>n.dataset.session===previous.id);(row?.querySelector('button:last-of-type')||historyModal.querySelector('input'))?.focus({preventScroll:true});}else visibleChip(previous.id,previous.workKey)?.focus({preventScroll:true});}});
 modal.addEventListener('click',event=>{if(event.target!==modal)return;const r=modal.getBoundingClientRect();if(event.clientX<r.left||event.clientX>r.right||event.clientY<r.top||event.clientY>r.bottom)modal.close();});
 function chip(work,row){
  const b=el('button',undefined,'worker-chip '+row.kind);b.type='button';b.dataset.session=row.id;b.dataset.group=work.key;
  const shared=F.assignments(data,work.scope_id,row.id).length;
  b.append(el('span',label(row.id),'worker-short-id'),el('strong',row.label,'worker-rate'));
  if(row.rate!==null){
   b.classList.add('worker-throughput');
   const chart=F.sparkline(row.metric.points),svg=document.createElementNS('http://www.w3.org/2000/svg','svg');
   svg.setAttribute('class','worker-sparkline');svg.setAttribute('viewBox','0 0 600 32');svg.setAttribute('preserveAspectRatio','none');svg.setAttribute('aria-hidden','true');svg.setAttribute('focusable','false');
   for(const d of chart.paths){const path=document.createElementNS(svg.namespaceURI,'path');path.setAttribute('d',d);path.setAttribute('vector-effect','non-scaling-stroke');svg.append(path);}
   b.append(svg);
  }else b.prepend(agentIcon());
  if(shared>1)b.append(el('span','Shared · '+shared,'worker-shared'));
  const historyDescription=row.rate!==null?' · reported output-token rate over the last 15 minutes; gaps are unknown; open session history':'';
  b.setAttribute('aria-label',row.id+' · '+row.label+(shared>1?' · shared across '+shared+' visible Workstreams':'')+historyDescription);b.title=row.id+' — '+(row.presence?.working||'No working declaration')+historyDescription+' — click for exact checkout and telemetry history';b.onclick=()=>inspect(work.scope_id,row.id,work.key);return b;
 }
 const classicCard=renderWorkCard;
 renderWorkCard=function(work){
  const card=classicCard(work);card.classList.add('work-group');card.dataset.group=work.key;
  card.querySelector('.activity-chart')?.remove();card.querySelector('.current-action')?.remove();card.querySelector('.checkout-disclosure')?.remove();
  card.querySelector('.card-top').remove();
  card.querySelector('.work-reference').prepend(scopeName('span',work.scope_id));
  const rows=F.sessions(work,Date.now(),connected),active=rows.filter(r=>r.present||r.reporting);
  const strip=el('div',undefined,'worker-strip');strip.setAttribute('aria-label','Session observations for '+work.id);
  // One exact session gets the available chart width. Other active sessions
  // remain in history; squeezing several curves can hide both rates and lines.
  const chips=el('div',undefined,'worker-chips');for(const r of active.slice(0,1))chips.append(chip(work,r));strip.append(chips);
  if(!active.length)strip.append(el('p',connected?'No live observation':'Observation unavailable','quiet'));
  const historyButton=hint(el('button',undefined,'compact-field history-trigger'),'Session history · '+rows.length+' registrations');const clock=icon('handoff');clock.querySelector('path').setAttribute('d','M3 12a9 9 0 1 0 3-6.7M3 3v5h5m4-1v5l3 2');historyButton.append(clock);historyButton.onclick=()=>history(work);strip.append(historyButton);
  if(active.length>1){historyButton.classList.add('has-more-sessions');historyButton.prepend(el('span','+'+(active.length-1)));historyButton.setAttribute('aria-label','Session history · '+rows.length+' registrations · '+(active.length-1)+' other active session observations');}
  if(!rows.length&&work.activity?.points?.length)strip.append(el('p','Unattributed history available in Workstream context; no session identity inferred.','quiet'));
  card.insertBefore(strip,card.querySelector('.card-gates'));
  const gates=card.querySelector('.card-gates');gates.replaceChildren();for(const [name,key,glyph] of [['Review','review','architecture'],['Merge','merge','nearby']]){const b=hint(el('button',undefined,'compact-field'),name+' · '+(work.readiness?.[key]||'Not reported').replaceAll('-',' ')+' · provider declared');b.append(icon(glyph));b.onclick=()=>showDetail(work.key);gates.append(b);}const context=el('button','Details','group-context');context.onclick=()=>showDetail(work.key);gates.append(context);
  return card;
 };
 const previousRender=render;
 render=function(result){const focus=document.activeElement;const id=focus?.dataset?.session,key=focus?.dataset?.group;connected=true;previousRender(result);if(selected&&modal.open)inspect(selected.scope,selected.id);if(historyModal.open)redrawHistory?.();if(id&&!modal.open&&!historyModal.open)visibleChip(id,key)?.focus({preventScroll:true});};
 $('scope').addEventListener('change',()=>{modal.close();modal.replaceChildren();historyModal.close();historyModal.replaceChildren();});
 new MutationObserver(()=>{if(!$('error').hidden){connected=false;for(const card of document.querySelectorAll('.work-group')){const work=data?.workstreams.find(w=>w.key===card.dataset.group);if(work)card.replaceWith(renderWorkCard(work));}if(selected&&modal.open)inspect(selected.scope,selected.id);if(historyModal.open)redrawHistory?.();}}).observe($('error'),{attributes:true,attributeFilter:['hidden']});
})();
