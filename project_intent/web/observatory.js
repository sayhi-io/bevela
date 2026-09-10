/* Opt-in presentation boundary over the same read model and classic components. */
'use strict';
if(location.pathname==='/workstream-map'&&!location.hash)history.replaceState(null,'','#map');
const views={home:['Overview','intent','Live observations, recent releases and the next judgment.'],developers:['Developers','worker','Observed current work, recent releases and latest recorded evidence.'],calendar:['Calendar','readiness','Timestamped handoffs, reports, releases, pull request observations and scoped local Git commits.'],map:['Map','scope','Architectural surfaces from existing declarations. A projection, not a workflow.'],work:['Work','scope','Every enrolled workstream, with execution and durable readiness kept separate.'],architecture:['Architecture','architecture','Applicable constraints and explainable revision comparisons.'],environments:['Environments','environment','Declared requirements, not measured capacity or permission.'],handoffs:['Handoffs','handoff','Worker reports alongside durable provider handoffs.'],sources:['Sources','proof','Coverage, freshness and independent observation sources.']};
for(const [key,[label,name]] of Object.entries(views)){const a=el('a');a.href='#'+key;a.title=key==='map'?'Workstream Map':label;const glyph=icon(name);if(key==='map')glyph.querySelector('path').setAttribute('d','M3 6l6-3 6 3 6-3v15l-6 3-6-3-6 3V6m6-3v15m6-12v15');if(key==='calendar')glyph.querySelector('path').setAttribute('d','M5 3v4m14-4v4M3 9h18M5 5h14a2 2 0 0 1 2 2v14H3V7a2 2 0 0 1 2-2m3 8h2m4 0h2m-8 4h2m4 0h2');a.append(glyph,el('span',label));$('view-nav').append(a);}
const bell=icon('handoff');bell.querySelector('path').setAttribute('d','M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4');$('notifications').prepend(bell);
function selectView(focus=false){const key=location.hash.slice(1)||'home',selected=views[key]?key:'home',[label,,description]=views[selected];document.documentElement.dataset.currentView=selected;document.querySelector('main').dataset.currentView=selected;for(const section of document.querySelectorAll('[data-view]'))section.hidden=!section.dataset.view.split(' ').includes(selected);for(const a of $('view-nav').children){if(a.hash==='#'+selected)a.setAttribute('aria-current','page');else a.removeAttribute('aria-current');}for(const [i,card] of [...$('rested').children].entries())card.hidden=selected==='home'&&i>=6;for(const [i,card] of [...$('convergence').children].entries())card.hidden=selected==='home'&&i>=3;$('product-context').textContent=selected==='home'?'SAYHI / PROJECT INTENT':'MISSION CONTROL / READ ONLY';$('product-title').textContent=selected==='home'?'Mission Control':label;$('product-description').textContent=description;$('product-description').hidden=selected==='home';$('view-title').textContent=label;$('view-description').textContent=description;$('view-description').hidden=true;if(focus)$('product-title').focus();}
window.addEventListener('hashchange',()=>selectView(true));selectView();
$('open-attention').onclick=()=>$('attention-dialog').showModal();
$('highlight-key').addEventListener('keydown',event=>{if(event.key==='Escape'){$('highlight-key').open=false;$('highlight-key').querySelector('summary').focus();event.stopPropagation();}});
document.addEventListener('pointerdown',event=>{const key=$('highlight-key');if(event.button===0&&key.open&&!key.contains(event.target))key.open=false;});
function renderHighlightKey(result){const examples=clear('highlight-key-examples');for(const scope of result.scopes)examples.append(scopeName('div',scope.id));const work=result.workstreams[0];if(work)examples.append(workstreamName('div',{...work,title:work.id}));if(!examples.children.length)examples.append(el('p','No identity examples in this observation.','quiet'));}
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
let calendarAnchor=new Date(),calendarMode='week',calendarSelected=ActivityViewsFacts.dateKey(Date.now()),activityResult=null;calendarAnchor.setHours(12,0,0,0);
const displayTime=at=>new Date(at).toLocaleString(undefined,{dateStyle:'medium',timeStyle:'short'});
function boardCard(item,kind){
 const work=item.work,card=el('article',undefined,'developer-card');card.dataset.workstream=work.key;
 card.append(qualifiedName('div',work.key));
 if(kind==='active')card.append(el('span','Observed active','board-state active'),el('h3',item.worker.session),el('p',item.worker.working||'No working declaration recorded.'),el('time',displayTime(item.at),'identifier'));
 if(kind==='released')card.append(el('span','Reported inactive','board-state released'),el('h3',item.release.session),el('p',item.release.working||'No working declaration recorded.'),el('time',displayTime(item.at),'identifier'));
 if(kind==='evidence')card.append(el('span',item.kind==='report'?'Worker report':'Provider handoff','board-state evidence'),workstreamName('h3',work),el('p',short(item.summary,180)),el('time',displayTime(item.at),'identifier'));
 card.append(workButton(work,'Open Workstream'));return card;
}
function renderDeveloperBoard(result){
 const facts=ActivityViewsFacts.board(result,Date.parse(result.observed_at),true),sets=[['active','developer-active'],['released','developer-released'],['evidence','developer-evidence']];
 for(const [kind,id] of sets){const target=clear(id);for(const item of facts[kind].slice(0,12))target.append(boardCard(item,kind));if(!target.children.length)empty(target,kind==='active'?'No fresh worker registrations. This does not establish that nobody is working.':kind==='released'?'No explicit inactive registrations in the bounded recent feed.':'No timestamped handoff or worker report available.');$(id+'-count').textContent=String(facts[kind].length);}
 const coverage=result.rested_coverage;$('developer-board-coverage').textContent='Working now uses fresh registrations at the observation time. Recently released is '+(coverage?`a bounded feed showing ${facts.released.length} of ${coverage.total} latest inactive registrations`:'unavailable')+'. Recorded evidence uses the latest available timestamped worker report or provider handoff per Workstream. A report does not itself establish delivery, and lifecycle alone never places work on this board.';
}
function selectCalendarDay(key,focus=false){calendarSelected=key;renderCalendar(activityResult,focus);}
function calendarRangeTitle(days){
 if(calendarMode==='month')return calendarAnchor.toLocaleDateString(undefined,{month:'long',year:'numeric'});
 const first=days[0]?.date,last=days.at(-1)?.date;if(!first||!last)return 'Work calendar';
 if(first.getFullYear()!==last.getFullYear())return `${first.toLocaleDateString(undefined,{month:'short',day:'numeric',year:'numeric'})}–${last.toLocaleDateString(undefined,{month:'short',day:'numeric',year:'numeric'})}`;
 if(first.getMonth()!==last.getMonth())return `${first.toLocaleDateString(undefined,{month:'short',day:'numeric'})}–${last.toLocaleDateString(undefined,{month:'short',day:'numeric'})}, ${last.getFullYear()}`;
 return `${first.toLocaleDateString(undefined,{month:'short'})} ${first.getDate()}–${last.getDate()}, ${last.getFullYear()}`;
}
function renderCalendar(result,focus=false){
 if(!result)return;activityResult=result;const facts=ActivityViewsFacts.events(result),view=calendarMode==='month'?ActivityViewsFacts.month(calendarAnchor.getFullYear(),calendarAnchor.getMonth(),facts):ActivityViewsFacts.week(calendarAnchor,facts),today=ActivityViewsFacts.dateKey(Date.now());
 $('calendar-view').dataset.mode=calendarMode;$('calendar-grid').dataset.mode=calendarMode;$('calendar-week').setAttribute('aria-pressed',String(calendarMode==='week'));$('calendar-month-view').setAttribute('aria-pressed',String(calendarMode==='month'));
 $('calendar-month').textContent=calendarRangeTitle(view.days);$('calendar-previous').setAttribute('aria-label',`Previous ${calendarMode}`);$('calendar-next').setAttribute('aria-label',`Next ${calendarMode}`);
 $('calendar-timezone').textContent='Dates use '+(Intl.DateTimeFormat().resolvedOptions().timeZone||'your browser time zone')+'.';
 const handoffs=facts.filter(event=>event.type==='handoff').length,reports=facts.filter(event=>event.type==='report').length,releases=facts.filter(event=>event.type==='release').length,prs=facts.filter(event=>event.type==='pull-request').length,commits=facts.filter(event=>event.type==='commit').length;
 const typeCounts={handoff:handoffs,report:reports,release:releases,'pull-request':prs,commit:commits},types=clear('calendar-evidence-types');for(const type of ['handoff','report','release','pull-request','commit']){const chip=el('span',undefined,'calendar-evidence-chip '+type);chip.append(el('i','',`event-dot ${type}`),el('span',ActivityViewsFacts.eventLabels[type]),el('strong',String(typeCounts[type])));types.append(chip);}
 const gitCoverage=result.local_git?.status||'not authorized/configured';$('calendar-coverage-summary').textContent=`${facts.length} dated records · coverage details`;$('calendar-coverage').textContent=`Available evidence: ${handoffs} provider handoffs · ${reports} worker reports · ${releases} recent release observations · ${prs} pull request observations · ${commits} local Git commits. Local Git coverage: ${gitCoverage}. Empty days mean no dated evidence in this scoped response; they are not evidence that no work occurred.`;
 const grid=clear('calendar-grid');for(const day of view.days){const button=el('button',undefined,'calendar-day');button.type='button';button.dataset.date=day.key;button.setAttribute('aria-pressed',String(day.key===calendarSelected));button.classList.toggle('outside-month',calendarMode==='month'&&!day.inMonth);button.classList.toggle('today',day.key===today);button.append(el('span',String(day.day),'calendar-day-number'));const counts={};if(day.events.length){const marks=el('span',undefined,'calendar-event-marks');for(const type of ['handoff','report','release','pull-request','commit']){const count=day.events.filter(event=>event.type===type).length;counts[type]=count;if(count){const mark=el('i',String(count),'event-mark '+type);mark.title=ActivityViewsFacts.eventLabels[type];marks.append(mark);}}button.append(marks);}const evidence=day.events.length?` · ${counts.handoff||0} handoffs, ${counts.report||0} worker reports, ${counts.release||0} recent releases, ${counts['pull-request']||0} pull request observations, ${counts.commit||0} Git commits`:' · no dated evidence';button.setAttribute('aria-label',day.date.toLocaleDateString(undefined,{dateStyle:'full'})+evidence);button.onclick=()=>{calendarAnchor=new Date(day.date);calendarAnchor.setHours(12,0,0,0);selectCalendarDay(day.key,true);};grid.append(button);}
 const selected=facts.filter(event=>event.date===calendarSelected),selectedDate=new Date(calendarSelected+'T12:00:00');$('calendar-day-title').textContent=Number.isFinite(selectedDate.getTime())?selectedDate.toLocaleDateString(undefined,{dateStyle:'full'}):'No day selected';$('calendar-day-summary').textContent=selected.length?`${selected.length} dated record${selected.length===1?'':'s'} in the available scoped response.`:'No dated evidence in the available scoped response. This is not evidence of inactivity.';
 const list=clear('calendar-day-events');for(const event of selected){const card=el('article',undefined,'calendar-event '+event.type);card.append(el('span',event.label,'board-state '+event.type));if(event.work)card.append(qualifiedName('div',event.work.key));else card.append(el('div',`${event.scope} · ${event.commit.repository}`,'identifier'));card.append(el('time',displayTime(event.at),'identifier'),el('p',short(event.summary,220)));if(event.type==='commit')card.append(el('p',`${event.commit.oid.slice(0,12)} · ${event.commit.publication}`,'identifier'));if(event.type==='pull-request'){const link=pullRequestChip(event.ref);if(link)card.append(link);}if(event.work)card.append(workButton(event.work,'Open Workstream'));list.append(card);}if(!selected.length)empty(list,'Choose a marked day to review recorded work.');
 if(focus)grid.querySelector(`[data-date="${calendarSelected}"]`)?.focus({preventScroll:true});
}
function selectedCalendarDate(){const selected=new Date(calendarSelected+'T12:00:00');return Number.isFinite(selected.getTime())?selected:new Date(calendarAnchor);}
$('calendar-week').onclick=()=>{calendarMode='week';calendarAnchor=selectedCalendarDate();renderCalendar(activityResult,true);};
$('calendar-month-view').onclick=()=>{calendarMode='month';const selected=selectedCalendarDate();calendarAnchor=new Date(selected.getFullYear(),selected.getMonth(),1,12);renderCalendar(activityResult,true);};
function moveCalendar(direction){if(calendarMode==='week')calendarAnchor=new Date(calendarAnchor.getFullYear(),calendarAnchor.getMonth(),calendarAnchor.getDate()+direction*7,12);else calendarAnchor=new Date(calendarAnchor.getFullYear(),calendarAnchor.getMonth()+direction,1,12);calendarSelected=ActivityViewsFacts.dateKey(calendarAnchor.getTime());renderCalendar(activityResult,true);}
$('calendar-previous').onclick=()=>moveCalendar(-1);
$('calendar-next').onclick=()=>moveCalendar(1);
$('calendar-today').onclick=()=>{calendarAnchor=new Date();calendarAnchor.setHours(12,0,0,0);calendarSelected=ActivityViewsFacts.dateKey(calendarAnchor.getTime());renderCalendar(activityResult,true);};
let detailKey=null;
const classicDetail=showDetail;
let reportSignature=null;
function appendReports(work){
 const signature=JSON.stringify([work.key,work.report_coverage,work.local_reports]);if($('worker-report-detail')&&signature===reportSignature)return;
 const prior=$('worker-report-detail'),open=new Set([...prior?.querySelectorAll('.report-branch[open]')||[]].map(n=>n.dataset.report));
 const focused=document.activeElement,focusBranch=focused?.closest('.report-branch'),focusId=focusBranch?.dataset.report,focusIndex=focusBranch?[...focusBranch.querySelectorAll('summary,button,a')].indexOf(focused):-1;
 const scroll=$('detail').scrollTop;reportSignature=signature;prior?.remove();
 const s=section($('detail-content'),'Worker reports · separate from provider readiness','handoff');s.id='worker-report-detail';s.append(el('p','Coverage: '+work.report_coverage,'quiet'));
 for(const report of work.local_reports||[]){const branch=el('details',undefined,'value-tree report-branch');branch.dataset.report=report.id;branch.open=open.has(report.id);branch.append(el('summary',report.created_at+' · '+(report.publication?.state||'local')+' · worker report'),reportCard(report,work,true));s.append(branch);if(report.id===focusId)(branch.querySelectorAll('summary,button,a')[focusIndex]||branch.querySelector('summary')).focus({preventScroll:true});}
 if(!work.local_reports?.length)empty(s,'No local worker reports in the available feed.');if(prior)$('detail').scrollTop=scroll;
}
function readinessTree(work){const old=$('detail-content').querySelector('.readiness-cards');if(!old)return;const tree=el('details',undefined,'value-tree');tree.open=true;tree.append(el('summary','Provider-declared readiness'));const rows=el('dl',undefined,'value-rows');for(const [name,value] of Object.entries(work.readiness||{}))rows.append(el('dt',name.replaceAll('_',' ')),el('dd',String(value).replaceAll('-',' ')));if(!rows.children.length)tree.append(el('p','No readiness values recorded.','quiet'));else tree.append(rows);tree.append(el('p','Source: durable provider metadata in this observation. Worker reports below are separate assertions; they do not overwrite these values.','section-note'));old.replaceWith(tree);}
showDetail=function(key){classicDetail(key);detailKey=key;const work=data?.workstreams.find(w=>w.key===key);if(work){readinessTree(work);appendReports(work);}};
const classicRender=render;
const workspaceSection=el('section',undefined,'workspace-inventory-panel');workspaceSection.id='workspace-inventory';$('workspace-panel-slot').replaceWith(workspaceSection);
const workspaceSummary=el('a',undefined,'workspace-coverage-link');workspaceSummary.href='#sources';workspaceSummary.hidden=true;document.querySelector('.status-tools').prepend(workspaceSummary);
function renderWorkspaceInventory(result){
 const inventory=result.workspace_inventory;workspaceSummary.hidden=!inventory;
 if(!inventory){workspaceSection.replaceChildren();return;}
 const signature=JSON.stringify([inventory.status,inventory.repositories,inventory.meaning]);
 const timestamp='Inventory: '+inventory.status+' · observed '+(inventory.observed_at||'unknown')+' · repositories without a mapping are visible gaps, not empty projects.';
 if(workspaceSection.dataset.inventory===signature&&$('workspace-inventory-time')){$('workspace-inventory-time').textContent=timestamp;return;}
 workspaceSection.replaceChildren();workspaceSection.dataset.inventory=signature;
 const heading=el('div',undefined,'section-head'),headingText=el('div');headingText.append(el('span','LOCAL WORKSPACE','section-kicker'),el('h2','Repository coverage'));heading.append(headingText);workspaceSection.append(heading);
 workspaceSummary.textContent=inventory.status==='observed'?inventory.repository_count+' repos · '+inventory.connected_count+' intent connections':'Workspace inventory · '+inventory.status;
 workspaceSection.append(el('p',inventory.meaning||'Workspace inventory not configured.','quiet'));
 const time=el('p',timestamp,'quiet');time.id='workspace-inventory-time';workspaceSection.append(time);
 const table=el('table',undefined,'inventory-table');const head=el('thead'),row=el('tr');for(const text of ['Repository / checkout','Intent coverage','Provider / execution'])row.append(el('th',text));head.append(row);table.append(head);const body=el('tbody');
 for(const repo of inventory.repositories||[]){const tr=el('tr'),name=el('td'),intent=el('td'),observations=el('td');name.append(el('strong',repo.repository));const detail=el('details');detail.append(el('summary','Checkout'),el('code',repo.checkout));name.append(detail);intent.append(el('span',repo.intent_status==='configured'?repo.scope:repo.intent_status==='not-mapped'?'Not enrolled here':'Scope not connected'));if(repo.enrolled_workstreams!==null)intent.append(el('small',repo.enrolled_workstreams+' enrolled Workstreams · scope-level'));observations.append(el('span','Provider: '+repo.provider_status),el('small','Execution: '+repo.execution_status));tr.append(name,intent,observations);body.append(tr);}
 table.append(body);workspaceSection.append(table);
}
render=function(result){
 classicRender(result);
 renderWorkspaceInventory(result);
 renderHighlightKey(result);
 renderDeveloperBoard(result);
 renderCalendar(result);
 // Work view includes completed/deferred intent too; home is observational only.
 const ordered=[...result.workstreams].sort((a,b)=>executionRank(b)-executionRank(a)||a.key.localeCompare(b.key));
 const all=clear('workstreams');for(const work of ordered)all.append(renderWorkCard(work));
 const live=clear('live-work');for(const work of ordered.filter(w=>executionRank(w)>0).slice(0,6))live.append(renderWorkCard(work));if(!live.children.length)empty(live,'No fresh worker observations. This does not establish that nobody is working.');
 const rested=clear('rested');for(const session of result.recently_rested||[]){const work=result.workstreams.find(w=>w.key===session.workstream);if(!work)continue;const tile=el('article',undefined,'tile rested-card');tile.append(qualifiedName('div',work.key),el('span','Reported inactive','rested-label'),el('h3',session.session),el('p',short(session.working,180)),el('p',new Date(session.reported_inactive_at).toLocaleString(),'identifier'),workButton(work,'Handoff & next gates'));rested.append(tile);}if(!rested.children.length)empty(rested,'No explicit inactive registrations reported in the last 24 hours.');
 const coverage=result.rested_coverage;$('rested-coverage').replaceChildren(el('span',coverage?`Overview shows up to 6; Developers shows ${result.recently_rested.length} of ${coverage.total} recent inactive registrations. Latest registration only, not transition history. `:'Recent-release projection unavailable. '));const more=el('a','All recent releases');more.href='#developers';$('rested-coverage').append(more);
 const attention=clear('home-attention');for(const item of result.attention.slice(0,3)){const tile=el('article',undefined,'tile');tile.append(el('span',item.kind,'identifier'),el('p',item.message));const work=result.workstreams.find(w=>w.key===item.workstream);if(work)tile.append(qualifiedName('div',work.key),workButton(work));attention.append(tile);}if(!attention.children.length)empty(attention,'No explainable attention conditions in this observation. Not a correctness guarantee.');
 const feed=clear('reports');const entries=result.workstreams.flatMap(work=>(work.local_reports||[]).map(report=>({work,report}))).sort(reportOrder);for(const {work,report} of entries.slice(0,24))feed.append(reportCard(report,work));if(!entries.length)empty(feed,'No worker reports available in the selected scope.');
 $('report-coverage').textContent=`Showing ${Math.min(entries.length,24)} of ${entries.length} available reports. `+result.workstreams.map(w=>w.id+': '+w.report_coverage).join(' · ');
 if($('detail').open&&detailKey){const work=result.workstreams.find(w=>w.key===detailKey);if(work)appendReports(work);else $('detail').close();}
 selectView();
};
// Clear added surfaces synchronously on scope change; failed fetch cannot leak prior scope.
$('scope').addEventListener('change',()=>{for(const id of ['live-work','rested','rested-coverage','home-attention','reports','report-coverage','highlight-key-examples','workspace-inventory','developer-active','developer-released','developer-evidence','calendar-grid','calendar-day-events','calendar-evidence-types'])clear(id);for(const id of ['developer-active-count','developer-released-count','developer-evidence-count'])$(id).textContent='0';$('developer-board-coverage').textContent='Awaiting the selected scoped response.';$('calendar-coverage-summary').textContent='Evidence coverage';$('calendar-coverage').textContent='Awaiting the selected scoped response.';$('calendar-day-summary').textContent='';workspaceSummary.hidden=true;detailKey=null;activityResult=null;});
