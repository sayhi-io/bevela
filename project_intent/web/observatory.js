/* Opt-in presentation boundary over the same read model and classic components. */
'use strict';
if(location.pathname==='/workstream-map'&&!location.hash)history.replaceState(null,'','#map');
const views={home:['Overview','intent','Live observations, recent releases and the next judgment.'],developers:['Developers','worker','Observed current work, recent releases and latest recorded evidence.'],calendar:['Calendar','readiness','Timestamped handoffs, reports, releases, pull request observations and scoped local Git commits.'],map:['Map','scope','Architectural surfaces from existing declarations. A projection, not a workflow.'],work:['Work','scope','Every enrolled workstream, with execution and durable readiness kept separate.'],architecture:['Architecture','architecture','Applicable constraints and explainable revision comparisons.'],environments:['Environments','environment','Declared requirements, not measured capacity or permission.'],handoffs:['Handoffs','handoff','Worker reports alongside durable provider handoffs.'],sources:['Sources','proof','Coverage, freshness and independent observation sources.']};
for(const [key,[label,name]] of Object.entries(views)){const a=el('a');a.href='#'+key;a.setAttribute('aria-label',label);a.title=key==='map'?'Workstream Map':label;const glyph=icon(name);if(key==='map')glyph.querySelector('path').setAttribute('d','M3 6l6-3 6 3 6-3v15l-6 3-6-3-6 3V6m6-3v15m6-12v15');if(key==='calendar')glyph.querySelector('path').setAttribute('d','M5 3v4m14-4v4M3 9h18M5 5h14a2 2 0 0 1 2 2v14H3V7a2 2 0 0 1 2-2m3 8h2m4 0h2m-8 4h2m4 0h2');a.append(glyph,el('span',label));$('view-nav').append(a);}
const bell=icon('handoff');bell.querySelector('path').setAttribute('d','M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4');$('notifications').prepend(bell);
function selectView(focus=false){const key=location.hash.slice(1)||'home',selected=views[key]?key:'home',[label,,description]=views[selected];document.documentElement.dataset.currentView=selected;document.querySelector('main').dataset.currentView=selected;for(const section of document.querySelectorAll('[data-view]'))section.hidden=!section.dataset.view.split(' ').includes(selected);for(const a of $('view-nav').children){if(a.hash==='#'+selected)a.setAttribute('aria-current','page');else a.removeAttribute('aria-current');}for(const [i,card] of [...$('rested').children].entries())card.hidden=selected==='home'&&i>=6;for(const [i,card] of [...$('convergence').children].entries())card.hidden=selected==='home'&&i>=3;$('product-context').textContent=selected==='home'?'SAYHI / PROJECT INTENT':'MISSION CONTROL / READ ONLY';$('product-title').textContent=label;$('product-description').textContent=description;$('product-description').hidden=selected==='home';$('view-title').textContent=label;$('view-description').textContent=description;$('view-description').hidden=true;if(focus)$('product-title').focus();}
window.addEventListener('hashchange',()=>selectView(true));selectView();
$('open-attention').onclick=()=>$('attention-dialog').showModal();
$('highlight-key').addEventListener('keydown',event=>{if(event.key==='Escape'){$('highlight-key').open=false;$('highlight-key').querySelector('summary').focus();event.stopPropagation();}});
document.addEventListener('pointerdown',event=>{const key=$('highlight-key');if(event.button===0&&key.open&&!key.contains(event.target))key.open=false;});
function renderHighlightKey(result){const examples=clear('highlight-key-examples');for(const scope of result.scopes)examples.append(scopeName('div',scope.id));const work=result.workstreams[0];if(work)examples.append(workstreamName('div',{...work,title:work.id}));if(!examples.children.length)examples.append(el('p','No identity examples in this observation.','quiet'));}
function workButton(work,label='Open context'){const button=el('button',label);button.onclick=()=>showDetail(work.key);return button;}
function reportCard(report,work,full=false){
 const tile=el('article',undefined,'tile report-card');const packet=report.payload.packet;
 const state=report.publication?.state||'local';
 tile.append(el('div',work.scope_id+' · '+(work.provider_identifier||work.id),'report-identity'),badge(state),el('p','Worker report · '+(report.created_at?new Date(report.created_at).toLocaleString(undefined,{dateStyle:'medium',timeStyle:'short'}):'time unavailable'),'identifier'),el('p',packet.summary));
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
 const record=kind==='active'?item.worker:kind==='released'?item.release:item;
 const label=kind==='active'?'Observed active':kind==='released'?'Reported inactive':item.kind==='report'?'Worker report':'Provider handoff';
 card.append(el('span',label,'board-state '+(kind==='evidence'?item.kind:kind)));
 card.append(el('h3',ActivityViewsFacts.preview(work.title||work.statement||work.id,95)));
 const description=el('details',undefined,'record-description'),full=record.working||record.summary||'No working declaration recorded.';
 description.append(el('summary',ActivityViewsFacts.preview(full,150)),el('p',full));card.append(description);
 if(record.session){const session=el('span',record.session,'developer-session');session.title=record.session;card.append(session);}
 card.append(el('time',displayTime(item.at),'identifier'),el('div',work.scope_id+' · '+(work.provider_identifier||work.id),'qualified-name'),workButton(work,'Open workstream'));
 return card;
}
function renderDeveloperBoard(result){
 const facts=ActivityViewsFacts.board(result,Date.parse(result.observed_at),true),sets=[['active','developer-active'],['released','developer-released'],['evidence','developer-evidence']];
 for(const [kind,id] of sets){const target=clear(id);for(const item of facts[kind].slice(0,12))target.append(boardCard(item,kind));if(!target.children.length)empty(target,kind==='active'?'No fresh worker registrations. This does not establish that nobody is working.':kind==='released'?'No explicit inactive registrations in the bounded recent feed.':'No timestamped handoff or worker report available.');$(id+'-count').textContent=String(facts[kind].length);}
 const coverage=result.rested_coverage;$('developer-board-coverage').textContent='Working now uses fresh registrations at the observation time. Recently released is '+(coverage?`a bounded feed showing ${facts.released.length} of ${coverage.total} latest inactive registrations`:'unavailable')+'. Recorded evidence uses the latest available timestamped worker report or provider handoff per Workstream. A report does not itself establish delivery, and lifecycle alone never places work on this board.';
}
function selectCalendarDay(key,focus=false){calendarSelected=key;calendarPageSize=40;$('calendar-event-range').value='day';renderCalendar(activityResult,focus);}
function calendarRangeTitle(days){
 if(calendarMode==='month')return calendarAnchor.toLocaleDateString(undefined,{month:'long',year:'numeric'});
 const first=days[0]?.date,last=days.at(-1)?.date;if(!first||!last)return 'Work calendar';
 if(first.getFullYear()!==last.getFullYear())return `${first.toLocaleDateString(undefined,{month:'short',day:'numeric',year:'numeric'})}–${last.toLocaleDateString(undefined,{month:'short',day:'numeric',year:'numeric'})}`;
 if(first.getMonth()!==last.getMonth())return `${first.toLocaleDateString(undefined,{month:'short',day:'numeric'})}–${last.toLocaleDateString(undefined,{month:'short',day:'numeric'})}, ${last.getFullYear()}`;
 return `${first.toLocaleDateString(undefined,{month:'short'})} ${first.getDate()}–${last.getDate()}, ${last.getFullYear()}`;
}
let selectedCalendarEvents=[],calendarPageSize=40,selectedEventId=null,eventTrigger=null;
function calendarEventsForRange(){
 if(!activityResult)return [];
 const events=ActivityViewsFacts.events(activityResult),range=$('calendar-event-range').value;
 if(range==='all')return events;
 if(range==='day')return events.filter(event=>event.date===calendarSelected);
 const view=calendarMode==='month'?ActivityViewsFacts.month(calendarAnchor.getFullYear(),calendarAnchor.getMonth(),events):ActivityViewsFacts.week(calendarAnchor,events);
 const dates=new Set(view.days.map(day=>day.key));return events.filter(event=>dates.has(event.date));
}
function closeEventDetail(){selectedEventId=null;$('event-detail').close();clear('event-detail-content');}
function showEventDetail(event,open=true){
 selectedEventId=event.id;if(open)eventTrigger=document.activeElement;
 const content=clear('event-detail-content'),title=el('h2',ActivityViewsFacts.preview(event.summary,140));title.id='event-detail-title';
 content.append(el('span',event.label,'board-state event-detail-kind '+event.type),title);
 const properties=el('dl',undefined,'event-properties');
 const property=(key,value)=>{if(value!==undefined&&value!==null&&value!=='')properties.append(el('dt',key),el('dd',String(value)));};
 property('Recorded',displayTime(event.at));property('Project',event.work?.scope_id||event.scope);property('Workstream',event.work?.title||event.work?.statement);
 property('Reference',event.work?.provider_identifier||event.work?.id);property('Session',event.session||event.report?.payload?.session);
 property('Repository',event.commit?.repository||event.ref?.repository);property('Commit',event.commit?.oid);
 property('Publication',event.commit?.publication||event.report?.publication?.state);property('Observed state',event.ref?.observation?.state);
 content.append(properties,el('p',event.summary,'event-full-summary'));
 const source=el('details',undefined,'event-source'),{work,...record}=event;
 source.append(el('summary','Source record & identifiers'),el('pre',JSON.stringify({...record,workstream:work?.key},null,2)));content.append(source);
 const actions=el('div',undefined,'event-context-action');
 if(event.work){const button=workButton(event.work,'Open workstream');button.onclick=()=>{closeEventDetail();showDetail(event.work.key);};actions.append(button);}
 if(event.type==='pull-request'){const link=pullRequestChip(event.ref);if(link)actions.append(link);}
 content.append(actions);
 if(open&&!$('event-detail').open)$('event-detail').showModal();
}
$('event-detail-close').onclick=closeEventDetail;
$('event-detail').addEventListener('close',()=>{selectedEventId=null;if(!activityResult||document.querySelector('dialog[open]'))return;if(eventTrigger?.isConnected)eventTrigger.focus({preventScroll:true});else if(document.documentElement.dataset.currentView==='calendar')$('calendar-event-search').focus({preventScroll:true});});
$('event-detail').addEventListener('click',event=>{if(event.target!==$('event-detail'))return;const bounds=event.target.getBoundingClientRect();if(event.clientX<bounds.left||event.clientX>bounds.right)closeEventDetail();});
function renderCalendarEvidence(){
 selectedCalendarEvents=calendarEventsForRange();
 const focusedId=document.activeElement?.closest('[data-event-id]')?.dataset.eventId;
 const filtered=ActivityViewsFacts.filterEvents(selectedCalendarEvents,{query:$('calendar-event-search').value,type:$('calendar-event-type').value,sort:$('calendar-event-sort').value}),body=clear('calendar-day-events');
 $('calendar-event-result-count').textContent=filtered.length===selectedCalendarEvents.length?`${filtered.length} record${filtered.length===1?'':'s'}`:`${filtered.length} of ${selectedCalendarEvents.length} records`;
 for(const event of filtered.slice(0,calendarPageSize)){
  const row=el('tr');row.dataset.eventType=event.type;row.dataset.eventId=event.id;row.dataset.at=String(event.at);
  const type=el('td'),evidence=el('td'),recorded=el('td'),actions=el('td');
  type.append(el('span',ActivityViewsFacts.eventLabels[event.type],'board-state '+event.type));
  const title=el('button',ActivityViewsFacts.preview(event.summary,160),'evidence-title');title.title=event.summary;title.onclick=()=>showEventDetail(event);
  title.setAttribute('aria-haspopup','dialog');title.setAttribute('aria-controls','event-detail');
  const context=el('div',undefined,'evidence-context');
  context.append(el('span',event.work?.scope_id||event.scope));
  const reference=event.commit?event.commit.oid.slice(0,7)+' · '+event.commit.publication:event.work?.provider_identifier||event.work?.id;
  if(reference)context.append(el('span',reference,'event-reference'));
  evidence.append(title,context);
  const time=el('time',new Date(event.at).toLocaleString(undefined,$('calendar-event-range').value==='day'?{hour:'numeric',minute:'2-digit'}:{month:'short',day:'numeric',hour:'numeric',minute:'2-digit'}));
  time.dateTime=new Date(event.at).toISOString();time.title=displayTime(event.at);recorded.append(time);actions.append(el('span','›','event-chevron'));
  row.onclick=event=>{if(!event.target.closest('button,a'))title.click();};
  row.append(type,evidence,recorded,actions);body.append(row);
 }
 if(!filtered.length){const row=el('tr',undefined,'calendar-ledger-empty'),cell=el('td',selectedCalendarEvents.length?'No activity matches your filters.':activityResult?'No recorded activity for this range. Try another day or all recorded dates.':'Awaiting the selected project.');cell.colSpan=4;row.append(cell);body.append(row);}
 $('calendar-load-more').hidden=filtered.length<=calendarPageSize;
 $('calendar-page-status').textContent=filtered.length>calendarPageSize?`Showing ${calendarPageSize} of ${filtered.length} matching records`:'';
 if(focusedId){const row=[...body.children].find(row=>row.dataset.eventId===focusedId);row?.querySelector('button')?.focus({preventScroll:true});}
 const range=$('calendar-event-range').value;
 $('calendar-day-title').textContent=range==='all'?'All recorded activity':range==='period'?'Activity this '+calendarMode:new Date(calendarSelected+'T12:00:00').toLocaleDateString(undefined,{weekday:'long',month:'long',day:'numeric'});
 $('calendar-day-summary').textContent=selectedCalendarEvents.length?'':'No dated evidence in this range; this does not establish inactivity.';
 if(selectedEventId&&$('event-detail').open){const current=ActivityViewsFacts.events(activityResult).find(event=>event.id===selectedEventId);if(!current)closeEventDetail();}
}
$('calendar-load-more').onclick=()=>{calendarPageSize+=40;renderCalendarEvidence();};
$('calendar-event-range').onchange=()=>{calendarPageSize=40;renderCalendarEvidence();};
function renderCalendar(result,focus=false){
 if(!result)return;activityResult=result;const facts=ActivityViewsFacts.events(result),view=calendarMode==='month'?ActivityViewsFacts.month(calendarAnchor.getFullYear(),calendarAnchor.getMonth(),facts):ActivityViewsFacts.week(calendarAnchor,facts),today=ActivityViewsFacts.dateKey(Date.now());
 $('calendar-view').dataset.mode=calendarMode;$('calendar-grid').dataset.mode=calendarMode;$('calendar-week').setAttribute('aria-pressed',String(calendarMode==='week'));$('calendar-month-view').setAttribute('aria-pressed',String(calendarMode==='month'));
 $('calendar-month').textContent=calendarRangeTitle(view.days);$('calendar-previous').setAttribute('aria-label',`Previous ${calendarMode}`);$('calendar-next').setAttribute('aria-label',`Next ${calendarMode}`);
 $('calendar-timezone').textContent=(Intl.DateTimeFormat().resolvedOptions().timeZone||'Browser local time').replaceAll('_',' ');
 const handoffs=facts.filter(event=>event.type==='handoff').length,reports=facts.filter(event=>event.type==='report').length,releases=facts.filter(event=>event.type==='release').length,prs=facts.filter(event=>event.type==='pull-request').length,commits=facts.filter(event=>event.type==='commit').length;
 const typeCounts={handoff:handoffs,report:reports,release:releases,'pull-request':prs,commit:commits},types=clear('calendar-evidence-types');for(const type of ['handoff','report','release','pull-request','commit']){const chip=el('span',undefined,'calendar-evidence-chip '+type);chip.append(el('i','',`event-dot ${type}`),el('span',({handoff:'Handoffs',report:'Reports',release:'Inactive','pull-request':'PRs',commit:'Commits'})[type]),el('strong',String(typeCounts[type])));types.append(chip);}
 const gitCoverage=result.local_git?.status||'not authorized/configured';$('calendar-coverage-summary').textContent=`${facts.length.toLocaleString()} records · Coverage`;$('calendar-coverage').textContent=`Available evidence: ${handoffs} provider handoffs · ${reports} worker reports · ${releases} recent release observations · ${prs} pull request observations · ${commits} local Git commits. Local Git coverage: ${gitCoverage}. Empty days mean no dated evidence in this scoped response; they are not evidence that no work occurred.`;
 const grid=clear('calendar-grid');for(const day of view.days){const button=el('button',undefined,'calendar-day');button.type='button';button.dataset.date=day.key;button.setAttribute('aria-pressed',String(day.key===calendarSelected));button.classList.toggle('outside-month',calendarMode==='month'&&!day.inMonth);button.classList.toggle('today',day.key===today);button.append(el('span',String(day.day),'calendar-day-number'));const counts={};if(day.events.length){const marks=el('span',undefined,'calendar-event-marks');for(const type of ['handoff','report','release','pull-request','commit']){const count=day.events.filter(event=>event.type===type).length;counts[type]=count;if(count){const mark=el('i',String(count),'event-mark '+type);mark.title=ActivityViewsFacts.eventLabels[type]+': '+count;mark.style.flexGrow=String(count);marks.append(mark);}}button.append(marks);}const total=el('span',String(day.events.length||'—'),'calendar-day-count');if(day.events.length)total.append(el('span',day.events.length===1?' record':' records','calendar-day-count-label'));button.insertBefore(total,button.querySelector('.calendar-event-marks'));const evidence=day.events.length?` · ${counts.handoff||0} handoffs, ${counts.report||0} worker reports, ${counts.release||0} recent releases, ${counts['pull-request']||0} pull request observations, ${counts.commit||0} Git commits`:' · no dated evidence';button.setAttribute('aria-label',day.date.toLocaleDateString(undefined,{dateStyle:'full'})+evidence);button.onclick=()=>{calendarAnchor=new Date(day.date);calendarAnchor.setHours(12,0,0,0);selectCalendarDay(day.key,true);};grid.append(button);}
 const selected=facts.filter(event=>event.date===calendarSelected),selectedDate=new Date(calendarSelected+'T12:00:00');$('calendar-day-title').textContent=Number.isFinite(selectedDate.getTime())?selectedDate.toLocaleDateString(undefined,{dateStyle:'full'}):'No day selected';$('calendar-day-summary').textContent=selected.length?`${selected.length} dated record${selected.length===1?'':'s'} in the available scoped response.`:'No dated evidence in the available scoped response. This is not evidence of inactivity.';$('calendar-event-range').querySelector('[value="period"]').textContent='Visible '+calendarMode;renderCalendarEvidence();
 if(focus)grid.querySelector(`[data-date="${calendarSelected}"]`)?.focus({preventScroll:true});
}
function selectedCalendarDate(){const selected=new Date(calendarSelected+'T12:00:00');return Number.isFinite(selected.getTime())?selected:new Date(calendarAnchor);}
$('calendar-week').onclick=()=>{calendarMode='week';calendarAnchor=selectedCalendarDate();renderCalendar(activityResult,true);};
$('calendar-month-view').onclick=()=>{calendarMode='month';const selected=selectedCalendarDate();calendarAnchor=new Date(selected.getFullYear(),selected.getMonth(),1,12);renderCalendar(activityResult,true);};
function moveCalendar(direction){if(calendarMode==='week')calendarAnchor=new Date(calendarAnchor.getFullYear(),calendarAnchor.getMonth(),calendarAnchor.getDate()+direction*7,12);else calendarAnchor=new Date(calendarAnchor.getFullYear(),calendarAnchor.getMonth()+direction,1,12);calendarSelected=ActivityViewsFacts.dateKey(calendarAnchor.getTime());renderCalendar(activityResult,true);}
$('calendar-previous').onclick=()=>moveCalendar(-1);
$('calendar-next').onclick=()=>moveCalendar(1);
$('calendar-today').onclick=()=>{calendarAnchor=new Date();calendarAnchor.setHours(12,0,0,0);calendarSelected=ActivityViewsFacts.dateKey(calendarAnchor.getTime());renderCalendar(activityResult,true);};
for(const id of ['calendar-event-search','calendar-event-type','calendar-event-sort'])$(id).addEventListener(id==='calendar-event-search'?'input':'change',()=>{calendarPageSize=40;renderCalendarEvidence();});
let detailKey=null;
function filterWorkstreams(){const query=$('work-search').value.toLocaleLowerCase().trim();for(const row of $('workstreams').children)row.hidden=!(row.dataset.search+' '+row.textContent.toLocaleLowerCase()).includes(query);}
$('work-search').oninput=filterWorkstreams;
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
 const all=clear('workstreams');for(const work of ordered){const card=renderWorkCard(work),reference=card.querySelector('.work-reference .workstream-name');if(reference&&work.provider_identifier){reference.textContent=work.provider_identifier;reference.title=work.key;}card.dataset.search=[work.key,work.title,work.statement,work.provider_identifier].join(' ').toLocaleLowerCase();all.append(card);}filterWorkstreams();
 const live=clear('live-work');for(const work of ordered.filter(w=>executionRank(w)>0).slice(0,6))live.append(renderWorkCard(work));if(!live.children.length)empty(live,'No fresh worker observations. This does not establish that nobody is working.');
 const rested=clear('rested');for(const event of ActivityViewsFacts.events(result).filter(event=>event.type==='release').slice(0,4)){const row=el('article',undefined,'tile rested-card');const title=el('button',ActivityViewsFacts.preview(event.summary,120),'evidence-title');title.onclick=()=>showEventDetail(event);title.setAttribute('aria-haspopup','dialog');row.append(el('span','Reported inactive','board-state release'),title,el('p',event.work.scope_id+' · '+(event.work.provider_identifier||event.work.id)+' · '+displayTime(event.at),'identifier'));rested.append(row);}if(!rested.children.length)empty(rested,'No explicit inactive registrations reported in the last 24 hours.');
 const coverage=result.rested_coverage;$('rested-coverage').replaceChildren(el('span',coverage?`Overview shows up to 4 of ${result.recently_rested.length} available recent inactive registrations; bounded source total ${coverage.total}. Latest registration only, not transition history. `:'Recent-release projection unavailable. '));const more=el('a','All recent releases');more.href='#developers';$('rested-coverage').append(more);
 const attention=clear('home-attention');for(const item of result.attention.slice(0,3)){const tile=el('article',undefined,'tile');tile.append(el('span',item.kind,'identifier'),el('p',item.message));const work=result.workstreams.find(w=>w.key===item.workstream);if(work)tile.append(el('div',work.scope_id+' · '+(work.provider_identifier||work.id),'identifier'),workButton(work));attention.append(tile);}if(!attention.children.length)empty(attention,'No explainable attention conditions in this observation. Not a correctness guarantee.');
 const feed=clear('reports');const entries=result.workstreams.flatMap(work=>(work.local_reports||[]).map(report=>({work,report}))).sort(reportOrder);for(const {work,report} of entries.slice(0,24))feed.append(reportCard(report,work));if(!entries.length)empty(feed,'No worker reports available in the selected scope.');
 $('report-coverage').textContent=`Showing ${Math.min(entries.length,24)} of ${entries.length} available reports. `+result.workstreams.map(w=>w.id+': '+w.report_coverage).join(' · ');
 if($('detail').open&&detailKey){const work=result.workstreams.find(w=>w.key===detailKey);if(work)appendReports(work);else $('detail').close();}
 selectView();
};
// Clear added surfaces synchronously on scope change; failed fetch cannot leak prior scope.
$('scope').addEventListener('change',()=>{for(const id of ['live-work','rested','rested-coverage','home-attention','reports','report-coverage','highlight-key-examples','workspace-inventory','developer-active','developer-released','developer-evidence','calendar-grid','calendar-day-events','calendar-evidence-types'])clear(id);for(const id of ['developer-active-count','developer-released-count','developer-evidence-count'])$(id).textContent='0';$('developer-board-coverage').textContent='Awaiting the selected scoped response.';$('calendar-coverage-summary').textContent='Evidence coverage';$('calendar-coverage').textContent='Awaiting the selected scoped response.';$('calendar-day-summary').textContent='';selectedCalendarEvents=[];calendarPageSize=40;closeEventDetail();$('calendar-page-status').textContent='';$('calendar-load-more').hidden=true;$('calendar-event-result-count').textContent='0 records';workspaceSummary.hidden=true;detailKey=null;activityResult=null;});
