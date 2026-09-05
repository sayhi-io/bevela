/* Opt-in presentation boundary over the same read model and classic components. */
'use strict';
const views={home:['Overview','intent','Live observations, recent releases and the next judgment.'],work:['Work','scope','Every enrolled workstream, with execution and durable readiness kept separate.'],architecture:['Architecture','architecture','Applicable constraints and explainable revision comparisons.'],environments:['Environments','environment','Declared requirements, not measured capacity or permission.'],handoffs:['Handoffs','handoff','Worker reports alongside durable provider handoffs.'],sources:['Sources','proof','Coverage, freshness and independent observation sources.']};
for(const [key,[label,name]] of Object.entries(views)){const a=el('a');a.href='#'+key;a.title=label;a.append(icon(name),el('span',label));$('view-nav').append(a);}
const bell=icon('handoff');bell.querySelector('path').setAttribute('d','M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4');$('notifications').prepend(bell);
function selectView(focus=false){const key=location.hash.slice(1)||'home';const selected=views[key]?key:'home';for(const section of document.querySelectorAll('[data-view]'))section.hidden=!section.dataset.view.split(' ').includes(selected);for(const a of $('view-nav').children){if(a.hash==='#'+selected)a.setAttribute('aria-current','page');else a.removeAttribute('aria-current');}for(const [i,card] of [...$('rested').children].entries())card.hidden=selected==='home'&&i>=6;for(const [i,card] of [...$('convergence').children].entries())card.hidden=selected==='home'&&i>=3;$('view-title').textContent=views[selected][0];$('view-description').textContent=views[selected][2];if(focus)$('view-title').focus();}
window.addEventListener('hashchange',()=>selectView(true));selectView();
$('open-attention').onclick=()=>$('attention-dialog').showModal();
function workButton(work,label='Open context'){const button=el('button',label);button.onclick=()=>showDetail(work.key);return button;}
function reportCard(report,work,full=false){
 const tile=el('article',undefined,'tile report-card');const packet=report.payload.packet;
 const state=report.publication?.state||'local';
 tile.append(qualifiedName('div',work.key),badge(state),el('p','Worker report · '+(report.created_at||'time unavailable'),'identifier'),el('p',full?packet.summary:short(packet.summary,240)));
 if(!full){tile.append(workButton(work,'Read report & evidence'));return tile;}
 tile.append(el('p',report.meaning||'Worker assertion, not verified conformance','quiet'),el('p','Session: '+report.payload.session));
 const readiness=el('dl',undefined,'environment-fields');for(const [key,value] of Object.entries(packet.readiness||{}))readiness.append(el('dt',key),el('dd',value));tile.append(readiness);
 if(packet.next_step)tile.append(el('p','Next: '+packet.next_step));
 for(const evidence of packet.evidence||[]){const href=safeLink(evidence.ref);if(href){const a=el('a',evidence.ref);a.href=href;a.target='_blank';a.rel='noopener noreferrer';tile.append(a);}else tile.append(el('p',evidence.ref));tile.append(el('p','SHA-256: '+evidence.sha256,'identifier'));}
 disclosure(tile,'Report identity, assertions and publication receipt',['Report: '+report.id,...(packet.assertions||[]).map(a=>JSON.stringify(a)),JSON.stringify(report.publication||{state:'local'})]);return tile;
}
function reportOrder(a,b){const time=x=>{const v=Date.parse(x.report.created_at);return Number.isFinite(v)?v:-Infinity;};return time(b)-time(a)||String(a.report.id).localeCompare(String(b.report.id));}
let detailKey=null;
const classicDetail=showDetail;
let reportSignature=null;
function appendReports(work){const signature=JSON.stringify([work.key,work.report_coverage,work.local_reports]);if($('worker-report-detail')&&signature===reportSignature)return;reportSignature=signature;$('worker-report-detail')?.remove();const s=section($('detail-content'),'Worker reports · separate from provider readiness','handoff');s.id='worker-report-detail';s.append(el('p','Coverage: '+work.report_coverage,'quiet'));for(const report of work.local_reports||[])s.append(reportCard(report,work,true));if(!work.local_reports?.length)empty(s,'No local worker reports in the available feed.');}
showDetail=function(key){classicDetail(key);detailKey=key;const work=data?.workstreams.find(w=>w.key===key);if(work)appendReports(work);};
const classicRender=render;
render=function(result){
 classicRender(result);
 // Work view includes completed/deferred intent too; home is observational only.
 const ordered=[...result.workstreams].sort((a,b)=>executionRank(b)-executionRank(a)||a.key.localeCompare(b.key));
 const all=clear('workstreams');for(const work of ordered)all.append(renderWorkCard(work));
 const live=clear('live-work');for(const work of ordered.filter(w=>executionRank(w)>0).slice(0,6))live.append(renderWorkCard(work));if(!live.children.length)empty(live,'No fresh worker observations. This does not establish that nobody is working.');
 const rested=clear('rested');for(const session of result.recently_rested||[]){const work=result.workstreams.find(w=>w.key===session.workstream);if(!work)continue;const tile=el('article',undefined,'tile rested-card');tile.append(qualifiedName('div',work.key),el('span','Reported inactive','rested-label'),el('h3',session.session),el('p',short(session.working,180)),el('p',new Date(session.reported_inactive_at).toLocaleString(),'identifier'),workButton(work,'Handoff & next gates'));rested.append(tile);}if(!rested.children.length)empty(rested,'No explicit inactive registrations reported in the last 24 hours.');
 const coverage=result.rested_coverage;$('rested-coverage').replaceChildren(el('span',coverage?`Overview shows up to 6; Handoffs shows ${result.recently_rested.length} of ${coverage.total} recent inactive registrations. Latest registration only, not transition history. `:'Recent-release projection unavailable. '));const more=el('a','All recent releases');more.href='#handoffs';$('rested-coverage').append(more);
 const attention=clear('home-attention');for(const item of result.attention.slice(0,3)){const tile=el('article',undefined,'tile');tile.append(el('span',item.kind,'identifier'),el('p',item.message));const work=result.workstreams.find(w=>w.key===item.workstream);if(work)tile.append(qualifiedName('div',work.key),workButton(work));attention.append(tile);}if(!attention.children.length)empty(attention,'No explainable attention conditions in this observation. Not a correctness guarantee.');
 const feed=clear('reports');const entries=result.workstreams.flatMap(work=>(work.local_reports||[]).map(report=>({work,report}))).sort(reportOrder);for(const {work,report} of entries.slice(0,24))feed.append(reportCard(report,work));if(!entries.length)empty(feed,'No worker reports available in the selected scope.');
 $('report-coverage').textContent=`Showing ${Math.min(entries.length,24)} of ${entries.length} available reports. `+result.workstreams.map(w=>w.id+': '+w.report_coverage).join(' · ');
 if($('detail').open&&detailKey){const work=result.workstreams.find(w=>w.key===detailKey);if(work)appendReports(work);else $('detail').close();}
 selectView();
};
// Clear added surfaces synchronously on scope change; failed fetch cannot leak prior scope.
$('scope').addEventListener('change',()=>{for(const id of ['live-work','rested','rested-coverage','home-attention','reports','report-coverage'])clear(id);detailKey=null;});
