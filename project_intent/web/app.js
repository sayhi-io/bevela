/* Read model consumer only. No provider calls, Markdown scraping or mutations. */
'use strict';
let data = null;
let scopeOptionsLoaded = false;
let generation = 0;
const $ = id => document.getElementById(id);
function el(tag, text, cls) { const n=document.createElement(tag); if(text!==undefined)n.textContent=text; if(cls)n.className=cls; return n; }
function workstreamName(tag, work) {
 const label=work.title||work.id;
 const node=el(tag,undefined,'workstream-name');
 // Identity only: fixed hash, independent of ordering, scope filtering or status.
 let hash=0;for(const c of work.key||work.id)hash=(Math.imul(hash,31)+c.charCodeAt(0))>>>0;
 const match=label===work.id?label.match(/^([A-Z0-9]+-)(.+?)(-\d+)$/):null;
 if(match)node.append(el('span',match[1],'identity-context'));
 node.append(el('mark',match?match[2]:label,'identity-highlight identity-hue-'+hash%4));
 if(match)node.append(el('span',match[3],'identity-context'));
 return node;
}
function scopeName(tag, scope) {
 const node=el(tag,undefined,'scope-name');
 // Naming only; splitting the displayed path never implies permission inheritance.
 const split=scope.lastIndexOf('/')+1;
 let hash=0;for(const c of scope)hash=(Math.imul(hash,31)+c.charCodeAt(0))>>>0;
 if(split)node.append(el('span',scope.slice(0,split),'identity-context'));
 node.append(el('mark',scope.slice(split),'identity-highlight identity-hue-'+hash%4));
 return node;
}
function qualifiedName(tag,key) {
 const split=key.indexOf(':');if(split<0)return scopeName(tag,key);
 const node=el(tag,undefined,'qualified-name');node.append(scopeName('span',key.slice(0,split)),el('span',':','identity-context'),el('span',key.slice(split+1),'qualified-id'));return node;
}
function executionObservation(work, now=Date.now()/1000) {
 const a=work.activity||{};
 const age=typeof a.last_report_at==='number'?now-a.last_report_at:null;
 const fresh=age!==null&&age>=0&&age<=90&&a.status==='recent';
 const present=(work.workers||[]).some(p=>p.status==='active'&&Date.parse(p.expires_at)/1000>now);
 const ago=age===null?'':age<60?Math.floor(age)+'s ago':Math.floor(age/60)+'m ago';
 if(fresh)return {label:'Live reports · '+ago,kind:'reporting',explanation:'Token usage reported within 90 seconds. This is recent telemetry, not proof the model is generating this instant.'};
 if(present)return {label:'Worker present · inference unknown',kind:'present',explanation:'A worker lease is fresh, but there is no recent inference report. The worker may be using tools, waiting, or executing elsewhere.'};
 if(age!==null&&age>=0)return {label:'Not observed live · last report '+ago,kind:'unknown',explanation:'Historical telemetry remains available. No fresh inference report or worker lease is observed.'};
 return {label:'Not observed live',kind:'unknown',explanation:'No fresh worker lease or inference report in the connected feeds. This does not prove the worker is idle.'};
}
function executionBadge(work) {const observed=executionObservation(work);const n=el('span',observed.label,'execution-badge '+observed.kind);n.title=observed.explanation;n.dataset.workstream=work.key;return n;}
function executionRank(work) {
 const observation=executionObservation(work);
 // Live inference reports outrank a fresh lease; both outrank lifecycle-only work.
 return observation.kind==='reporting'?2:observation.kind==='present'?1:0;
}
function workerCheckout(worker) {
 const box=el('div',undefined,'worker-checkout');const c=worker.checkout;
 box.append(el('span',worker.session+' · '+worker.status,'identifier'));
 if(!c){box.append(el('p','Execution checkout not registered','section-note'));return box;}
 box.append(el('strong',c.root,'checkout-path'),el('p',c.host+' · '+(c.branch||'detached HEAD')+' · intent: '+(worker.access||'unspecified'),'checkout-meta'));
 box.append(el('p','Touching: '+((worker.touching_paths||[]).join(', ')||'paths unspecified'),'checkout-meta'));
 return box;
}
function empty(target, text) { target.append(el('p',text,'empty')); }
function activityChart(work) {
 const activity=work.activity||{status:'not-connected',points:[]};
 const shell=el('div',undefined,'activity-chart');
 if(activity.sessions){shell.append(el('span',activity.sessions.length+' enrolled telemetry sessions · separate rates','activity-caption'));for(const session of activity.sessions){shell.append(el('span',session.session,'identifier'),activityChart({...work,activity:session}));}return shell;}
 if(!activity.points?.length){shell.append(el('span','Inference activity · '+activity.status.replaceAll('-',' '),'activity-caption'));return shell;}
 const points=activity.points;
 const now=Date.parse(data.observed_at)/1000;
 const maximum=Math.max(1,...points.map(p=>p.value??0));
 const x=p=>Math.max(0,Math.min(640,(p.at-(now-900))/900*640));
 const y=p=>76-(p.value/maximum)*64;
 function svgNode(tag,attributes){const n=document.createElementNS('http://www.w3.org/2000/svg',tag);for(const [k,v] of Object.entries(attributes))n.setAttribute(k,String(v));return n;}
 const svg=svgNode('svg',{viewBox:'0 0 640 84',preserveAspectRatio:'none',role:'img','aria-label':'Reported output-token rate over 15 minutes; gaps mean unknown. Scale 0 to '+maximum.toFixed(1)+' tokens per second.'});
 let hash=0;for(const c of work.key)hash=(Math.imul(hash,31)+c.charCodeAt(0))>>>0;
 shell.classList.add('activity-hue-'+hash%4);
 for(const level of [12,44,76])svg.append(svgNode('path',{d:`M0 ${level}H640`,class:'activity-grid'}));
 let segment=[];
 const flush=()=>{if(!segment.length)return;const line=segment.map((p,i)=>(i?'L':'M')+x(p).toFixed(2)+' '+y(p).toFixed(2)).join(' ');svg.append(svgNode('path',{d:line+` L${x(segment.at(-1))} 76 L${x(segment[0])} 76 Z`,class:'activity-area'}),svgNode('path',{d:line,class:'activity-line'}));segment=[];};
 let last=null;for(const p of points){if(p.value===null||(last&&p.at-last.at>120))flush();if(p.value!==null){segment.push(p);const dot=svgNode('circle',{cx:x(p),cy:y(p),r:3,class:'activity-point'});const title=svgNode('title',{});title.textContent=new Date(p.at*1000).toLocaleTimeString()+' · '+p.value.toFixed(2)+' reported output tokens/s';dot.append(title);svg.append(dot);}last=p;}flush();
 const latest=points.at(-1);const value=activity.status==='recent'&&latest.value!==null?latest.value.toFixed(1)+' reported tok/s':activity.status+' · last reports';
 shell.append(svg,el('span',value+' · 15m · peak '+maximum.toFixed(1),'activity-caption'));
 return shell;
}
function clear(id) { const n=$(id);n.replaceChildren();return n; }
function short(value, limit=190) { const s=String(value||'');return s.length>limit?s.slice(0,limit)+'…':s; }
function safeLink(value) { try {const u=new URL(value);return ['https:','http:'].includes(u.protocol)&&!u.username&&!u.password?u.href:null;} catch{return null;} }
function list(parent, values) {const ul=el('ul');for(const value of values)ul.append(el('li',typeof value==='string'?value:JSON.stringify(value)));parent.append(ul);}
function icon(name) {
 const paths={intent:'M12 3 3 8l9 5 9-5-9-5M3 12l9 5 9-5M3 16l9 5 9-5',scope:'M8 3H3v5m13-5h5v5M3 16v5h5m13-5v5h-5',avoid:'M5 5l14 14M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0',proof:'M8 3h8l4 4v14H4V3h4m0 9 3 3 5-5',worker:'M16 7a4 4 0 1 1-8 0 4 4 0 0 1 8 0M4 21v-3a8 8 0 0 1 16 0v3',architecture:'M12 3 3 7v6c0 4 9 8 9 8s9-4 9-8V7l-9-4m-4 9 3 3 5-5',environment:'M3 4h18v12H3V4m5 17h8m-4-5v5',readiness:'M4 5h16M4 12h16M4 19h16M8 3v4m8 3v4m-6 3v4',nearby:'M5 5v14m14-14v14M5 8c7 0 7 8 14 8M2 5h6m8 0h6M2 19h6m8 0h6',handoff:'M3 12h18m-7-7 7 7-7 7'};
 const svg=document.createElementNS('http://www.w3.org/2000/svg','svg');
 for(const [k,v] of Object.entries({viewBox:'0 0 24 24',fill:'none',stroke:'currentColor','stroke-width':'1.5','stroke-linecap':'round','stroke-linejoin':'round','aria-hidden':'true',focusable:'false',class:'detail-icon'}))svg.setAttribute(k,v);
 const path=document.createElementNS(svg.namespaceURI,'path');path.setAttribute('d',paths[name]||paths.intent);svg.append(path);return svg;
}
function section(parent,title,name='intent') {const s=el('section',undefined,'detail-section');const h=el('h3');h.append(icon(name),el('span',title));s.append(h);parent.append(s);return s;}
function disclosure(parent,label,values) {const d=el('details',undefined,'technical');d.append(el('summary',label));for(const value of values)d.append(el('p',value));parent.append(d);return d;}
function tone(value) {return ['complete','approved-local','revision-current'].includes(value)?'current':['not-authorized','reconciliation-required','blocked','not-ready'].includes(value)?'caution':'neutral';}
function badge(value) {return el('span',value.replaceAll('-',' '),'status-badge '+tone(value));}
function showDetail(key) {
 const w=data?.workstreams.find(w=>w.key===key);if(!w)return;
 const body=clear('detail-content');const hero=el('div',undefined,'detail-hero');hero.append(scopeName('p',w.scope_id),workstreamName('h2',w),el('p',w.statement,'mission-statement'));body.append(hero);
 let s=section(body,'Readiness','readiness');s.append(el('p','Independent dimensions — not a release pipeline.','section-note'));const readiness=el('div',undefined,'readiness-cards');for(const [k,v] of Object.entries(w.readiness||{})){const card=el('div',undefined,'readiness-card');card.append(el('span',k,'readiness-label'),badge(v));readiness.append(card);}s.append(readiness,el('p','Local validation does not imply CI execution, merge, environment admission or production activation.','section-note'));
 const bounds=el('div',undefined,'boundary-grid');body.append(bounds);s=section(bounds,'In scope','scope');s.append(el('p',w.scope));s=section(bounds,'Out of scope','avoid');s.append(el('p',w.avoid||'Not recorded'));
 s=section(body,'What must be proven','proof');const acceptance=el('ol',undefined,'acceptance-list');for(const [i,text] of (w.acceptance||[]).entries()){const li=el('li');li.append(el('span',String(i+1).padStart(2,'0'),'criterion-number'),el('span',text));acceptance.append(li);}s.append(acceptance,el('p','Acceptance criteria, not completion checkmarks.','section-note'));
 s=section(body,'Execution','worker');s.append(el('p','Declared lifecycle: '+w.state,'section-note'),executionBadge(w),el('p',executionObservation(w).explanation,'section-note'));
 s.append(activityChart(w));
 for(const a of w.activity?.sessions||[w.activity||{}]){if(a.session){s.append(el('p','Telemetry session: '+a.session),el('p',a.meaning,'section-note'));disclosure(s,'Reported activity samples · '+a.session,(a.points||[]).map(p=>new Date(p.at*1000).toLocaleTimeString()+' · '+(p.value===null?'unknown':p.value+' reported output tokens/s')));}}
 const active=w.workers.filter(p=>p.status==='active');
 s.append(el('p',active.length?active.map(p=>p.session+' — '+p.working).join('\n'):'No live worker lease in the enrolled observation feeds. Activity elsewhere is unknown.'));
 for(const p of w.workers){s.append(workerCheckout(p));disclosure(s,'Granular scope and observation · '+p.session,['Last heartbeat: '+p.heartbeat_at,'Lease expires: '+p.expires_at,'Checkout observed: '+(p.checkout?.observed_at||'unknown'),'HEAD: '+(p.checkout?.head||'not observed / unborn'),'Repository identity: '+(p.checkout?.repository_common_dir||'unknown'),'Current semantic seams: '+((p.touching_seams||[]).join(', ')||'not declared'),'Approaching: '+((p.approaching||[]).join(', ')||'not declared'),'Avoid paths: '+((p.avoid_paths||[]).join(', ')||'not declared'),'Avoid: '+((p.avoid||[]).join(', ')||'not declared'),'Declared scope only; not detected edits or permission.']);}
 disclosure(s,'Workstream source reference — not necessarily an execution checkout',['Reference checkout: '+(w.source_checkout||'Not enrolled'),'Reference branch: '+(w.branch||'Not enrolled'),'Provider issue: '+(w.provider_identifier||'not projected'),'Declared delegate: '+(w.delegate_name||'not projected'),'Declared assignee: '+(w.assignee_name||'not assigned')]);
 s=section(body,'Applicable architecture','architecture');
 const stats=el('div',undefined,'architecture-strip');for(const [status,label] of [['revision-current','revision current'],['reconciliation-required','need reconciliation'],['no-bound-evidence','missing binding']]){const n=w.claims.filter(c=>c.status===status).length;stats.append(el('span',n+' '+label,tone(status)));}s.append(stats,el('p','Revision alignment is a declaration comparison, not verified conformance.','section-note'));
 if(!w.claims.length)s.append(el('p','No applicable invariant enrolled. This does not establish absence of architectural constraints.'));
 for(const c of w.claims){const card=el('div',undefined,'claim');const top=el('div',undefined,'claim-top');top.append(el('strong',c.invariant.split(':').pop()),badge(c.status));card.append(top,el('p',c.statement,'claim-statement'));const revisions=el('div',undefined,'revision-pair');revisions.append(el('span','Architecture r'+c.architecture_revision),el('span',c.evidence_revision===null?'Evidence missing':'Evidence r'+c.evidence_revision));card.append(revisions);disclosure(card,'Evidence binding and provenance',['Invariant: '+c.invariant,'Subject: '+(c.subject||'Not bound'),c.verification]);s.append(card);}
 for(const p of w.precedents)s.append(el('p',p.key+' r'+p.revision+' — '+p.statement));
 s.append(el('p',w.divergence_coverage));if(w.divergences.length)list(s,w.divergences);else s.append(el('p','No divergence proposals/review findings recorded; not a drift assessment.'));
 s=section(body,'Environment','environment');const req=w.environment.requirement;if(req&&typeof req==='object'){const fields=el('dl',undefined,'environment-fields');for(const [k,v] of Object.entries(req)){fields.append(el('dt',k.replaceAll('_',' ')),el('dd',typeof v==='string'?v:JSON.stringify(v)));}s.append(fields);}else s.append(el('p',req||'No environment requirement enrolled'));s.append(el('p',`Availability: ${w.environment.availability} / occupancy: ${w.environment.occupancy}`,'environment-status'),el('p',w.environment.meaning,'section-note'));
 s=section(body,'Evidence & provenance','proof');disclosure(s,'Source subject and evidence references',['Current subject: '+(w.completion_subject||'Not recorded'),...(w.completion_evidence||[])]);s.append(el('p',w.handoff_verification||'Declarations not independently verified by this service'));
 for(const ref of w.completion_evidence||[]){const href=safeLink(ref);if(href){const a=el('a','Open evidence ↗');a.href=href;a.target='_blank';a.rel='noopener noreferrer';s.append(a);}}
 if(w.provider_url){const href=safeLink(w.provider_url);if(href){const a=el('a','Open PM provider ↗');a.href=href;a.target='_blank';a.rel='noopener noreferrer';s.append(a);}}
 s=section(body,'Nearby work','nearby');const nearby=data.convergence.filter(c=>c.workstreams.includes(key));for(const c of nearby)s.append(el('p',c.boundary+' → '+c.workstreams.filter(k=>k!==key).join(', ')));if(!nearby.length)s.append(el('p','No declared same-scope seam convergence.'));
 s=section(body,'Latest handoff / next gates','handoff');s.append(el('p',w.handoff_summary||'No handoff recorded'));if(w.integration_dependency)s.append(el('p','Integration dependency: '+w.integration_dependency));
 if(!$('detail').open)$('detail').showModal();
}
const expandedCheckouts=new Set();
function renderWorkCard(w) {
 const card=el('article',undefined,'work-card compact-work-card');
 const top=el('div',undefined,'card-top');top.append(scopeName('span',w.scope_id),executionBadge(w));card.append(top);
 const title=el('button',undefined,'work-title');
 const descriptive=w.title&&w.title!==w.id;
 title.append(descriptive?workstreamName('h3',w):el('h3',w.statement));title.onclick=()=>showDetail(w.key);card.append(title);
 const identity=el('div',undefined,'work-reference');identity.append(workstreamName('span',{...w,title:w.id}),el('span','Lifecycle: '+w.state));card.append(identity);
 const fresh=(w.workers||[]).filter(p=>p.status==='active'&&Date.parse(p.expires_at)>Date.now());
 const action=fresh.map(p=>p.working).filter(Boolean).join(' · ');
 card.append(el('p',short(action||((w.readiness?.execution||'No fresh worker observation').replaceAll('-',' ')),180),'current-action'));
 const gates=el('div',undefined,'card-gates');
 for(const [name,value] of [['Review',w.readiness?.review],['Merge',w.readiness?.merge]]){const row=el('div');row.append(el('span',name),el('strong',(value||'Not reported').replaceAll('-',' ')));gates.append(row);}card.append(gates);
 const workers=fresh.length?fresh:(w.workers||[]).filter(p=>p.checkout).sort((a,b)=>Date.parse(b.heartbeat_at)-Date.parse(a.heartbeat_at)).slice(0,1);
 const details=el('details',undefined,'checkout-disclosure');
 const roots=workers.map(p=>p.checkout?.root?.split('/').filter(Boolean).at(-1)||'Unknown checkout');
 details.append(el('summary',(fresh.length?'Working in ':workers.length?'Last checkout · ':'Execution details · ')+(roots.join(', ')||'not registered')));
 for(const worker of workers){details.append(workerCheckout(worker));if(worker.working)details.append(el('p',worker.working));}
 if(!workers.length)details.append(el('p','No execution checkout registered. Reference: '+(w.source_checkout||'not enrolled')));
 details.append(el('p',w.statement));details.open=expandedCheckouts.has(w.key);
 details.ontoggle=()=>{if(details.isConnected){if(details.open)expandedCheckouts.add(w.key);else expandedCheckouts.delete(w.key);}};
 card.append(details,activityChart(w));
 card.onclick=e=>{if(!e.target.closest('button,details,a'))showDetail(w.key);};
 return card;
}
function render(result) {
 data=result;
 for(const badge of document.querySelectorAll('#detail .execution-badge')){const work=result.workstreams.find(w=>w.key===badge.dataset.workstream);const observation=work?executionObservation(work):{label:'Not observed live',kind:'unknown',explanation:'Workstream absent from latest observation.'};badge.textContent=observation.label;badge.className='execution-badge '+observation.kind;badge.title=observation.explanation;}
 const scopes=[...result.scopes,...(result.dependency_sources||[])];
 if(!scopeOptionsLoaded){for(const s of scopes){const o=el('option',s.label);o.value=s.id;$('scope').append(o);}scopeOptionsLoaded=true;}
 const cached=scopes.filter(s=>s.provider_status!=='live').length;
 $('connection-summary').textContent=cached?'Provider cache in use · '+cached+' scope(s)':'Connected · '+scopes.length+' scopes';
 $('connection').textContent=`Project Intent available · ${scopes.length} scoped source${scopes.length===1?'':'s'} · ${cached?'cached/offline provider state in '+cached+' scope(s)':'provider reads successful'} · execution observed separately`;
 $('observed').textContent='OBSERVED '+new Date(result.observed_at).toLocaleTimeString();
 const m=clear('metrics');const active=result.workstreams.filter(w=>['active','blocked','ready'].includes(w.state));
 for(const [n,label,note,name] of [[active.length,'Open workstreams','Declared lifecycle, not observed execution','intent'],[result.sessions.filter(p=>p.status==='active').length,'Fresh leases','Observed worker leases, not proof of inference','worker'],[result.attention.length,'Attention items','Explainable conditions, not unread messages','handoff'],[result.architecture.filter(a=>a.kind==='invariant'&&a.state==='accepted').length,'Accepted invariants','Accepted declarations, not an architecture score','architecture']]){const tile=el('div',undefined,'metric');tile.title=note;tile.setAttribute('aria-label',`${n} ${label}. ${note}`);tile.append(icon(name),el('strong',String(n)),el('span',label));m.append(tile);}
 $('notification-count').textContent=String(result.attention.length);$('notifications').setAttribute('aria-label',`Needs attention: ${result.attention.length} conditions`);
 const works=clear('workstreams');for(const w of active.slice().sort((a,b)=>executionRank(b)-executionRank(a)))works.append(renderWorkCard(w));if(!active.length)empty(works,'No active workstreams declared in this scope.');
 const att=clear('attention');const attentionGroups=new Map();for(const a of result.attention){if(!attentionGroups.has(a.message))attentionGroups.set(a.message,[]);attentionGroups.get(a.message).push(a);}
 for(const [message,items] of attentionGroups){const group=el('section',undefined,'attention-group');const heading=el('div',undefined,'attention-heading');heading.append(icon('handoff'),el('h3',message),el('span',String(items.length),'attention-count'));group.append(heading);for(const a of items){if(a.workstream){const w=result.workstreams.find(w=>w.key===a.workstream);const button=el('button',undefined,'attention-workstream');const identity=el('span',undefined,'attention-identity');identity.append(workstreamName('strong',w||{id:a.workstream.split(':').pop(),key:a.workstream}),scopeName('span',w?.scope_id||a.workstream.split(':')[0]));if(w?.title&&w.title!==w.id)identity.append(el('span',w.id,'attention-scope'));button.append(identity,icon('handoff'));button.onclick=()=>showDetail(a.workstream);group.append(button);}else group.append(scopeName('p',a.scope));}att.append(group);}if(!result.attention.length)empty(att,'No attention condition found in enrolled data. This is not a health certification.');
 const conv=clear('convergence');for(const c of result.convergence){const tile=el('article',undefined,'tile');tile.append(scopeName('span',c.scope),el('h3',c.boundary));list(tile,c.workstreams.map(k=>k.split(':').slice(1).join(':')));tile.append(el('div',`${c.workstreams.length} declared workstreams · ${c.approaching_sessions.length} approaching sessions`,'count'));conv.append(tile);}if(!result.convergence.length)empty(conv,'No declared semantic overlap within the visible scopes. Cross-product work requires explicit relations, not matching words.');
 const arch=clear('architecture');for(const a of result.architecture){const tile=el('article',undefined,'tile');tile.append(el('span',a.kind.toUpperCase()+' · '+a.state+' · r'+a.revision,'identifier'),el('h3',a.key.split(':').slice(1).join(':')),el('p',a.statement),el('div',a.workstreams.length+' applicable workstreams','count'),scopeName('span',a.scope));arch.append(tile);}if(!result.architecture.length)empty(arch,'No architectural records enrolled for this scope.');
 const claims=result.workstreams.flatMap(w=>w.claims);$('architecture-summary').textContent=`${claims.filter(c=>c.status==='revision-current').length} revision-current · ${claims.filter(c=>c.status==='reconciliation-required').length} require reconciliation · ${claims.filter(c=>c.status==='no-bound-evidence').length} missing bindings. All are declared assertions.`;
 const environments=clear('environments');for(const w of result.workstreams.filter(w=>w.environment.requirement)){const r=w.environment.requirement;const tile=el('article',undefined,'tile');tile.append(qualifiedName('div',w.key),el('h3',typeof r==='string'?r:(r.profile||r.requirement||'Declared environment requirement')),el('p','Availability unknown · occupancy unknown'));if(Array.isArray(r.known_limitations))list(tile,r.known_limitations);else tile.append(el('p',short(typeof r==='string'?r:JSON.stringify(r),240)));const button=el('button','Read requirement ↗');button.onclick=()=>showDetail(w.key);tile.append(button);environments.append(tile);}if(!environments.children.length)empty(environments,'No environment requirements enrolled.');
 const initiatives=clear('initiatives');for(const i of result.initiatives){const tile=el('article',undefined,'tile');tile.append(scopeName('span',i.scope),el('span',i.status,'identifier'),el('h3',i.title));const members=el('ul');for(const key of i.workstreams)members.append(qualifiedName('li',key));tile.append(members);tile.append(el('p','Membership shown only for authorized, selected scopes.'));initiatives.append(tile);}if(!result.initiatives.length)empty(initiatives,'No visible initiatives supplied by the provider.');
 const handoffs=clear('handoffs');for(const w of result.recent_handoffs){const tile=el('article',undefined,'tile');tile.append(el('span',new Date(w.handoff_at).toLocaleString(),'identifier'),scopeName('span',w.scope_id),workstreamName('h3',w),el('p',short(w.handoff_summary,260)));const b=el('button','Read handoff ↗');b.onclick=()=>showDetail(w.key);tile.append(b);handoffs.append(tile);}if(!result.recent_handoffs.length)empty(handoffs,'No handoffs recorded.');
 const sources=clear('sources');for(const s of scopes){const tile=el('article',undefined,'tile');tile.append(scopeName('span',s.id),el('h3',s.label),el('p','Provider: '+s.provider_status),el('p',s.source?'Snapshot captured '+s.source.captured_at+' · '+s.age_seconds+'s old · non-authoritative cache':'No cached durable state'),el('p','Execution: '+s.execution.status),el('p',s.execution.meaning));sources.append(tile);}
}
async function refresh(){const request=++generation;try{const selected=$('scope').value;const response=await fetch('/api/v1/observatory'+(selected?'?scope='+encodeURIComponent(selected):''),{cache:'no-store'});if(!response.ok)throw new Error(response.status===401?'Project Intent authentication required':'Projection unavailable ('+response.status+')');const next=await response.json();if(request!==generation)return;render(next);$('error').hidden=true;}catch(error){if(request!==generation)return;for(const badge of document.querySelectorAll('.execution-badge')){badge.textContent='Live observation disconnected';badge.className='execution-badge unknown';badge.title='Retained view only; current execution is unknown.';}$('connection-summary').textContent='Connection unavailable · retained view';$('connection').textContent='Project Intent connection unavailable';$('error').textContent=error.message+(data?'. Retaining the last displayed observation; it is not live.':'. No state has been loaded.');$('error').hidden=false;}}
$('notifications').onclick=()=>$('attention-dialog').showModal();
$('attention-close').onclick=()=>$('attention-dialog').close();
$('attention-dialog').addEventListener('click',event=>{if(event.target!==$('attention-dialog'))return;const r=event.target.getBoundingClientRect();if(event.clientX<r.left||event.clientX>r.right||event.clientY<r.top||event.clientY>r.bottom)event.target.close();});
$('refresh').onclick=refresh;$('scope').onchange=()=>{$('detail').close();$('attention-dialog').close();$('notification-count').textContent='—';$('notifications').setAttribute('aria-label','Needs attention: awaiting selected scope');data=null;for(const id of ['metrics','workstreams','attention','convergence','architecture','architecture-summary','handoffs','sources','environments','initiatives'])clear(id);refresh();};$('close').onclick=()=>$('detail').close();refresh();setInterval(refresh,5000);
