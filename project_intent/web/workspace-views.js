/* Local database views over the already-authorized response. No write API. */
'use strict';
(function(root){
 const contains=(value,query)=>JSON.stringify(value).toLocaleLowerCase().includes(query.trim().toLocaleLowerCase());
 const quote=value=>"'"+String(value).replaceAll("'", "'\"'\"'")+"'";
 function repositoryPlan(repo){
  const mapped=Boolean(repo.scope),connected=repo.intent_status==='configured';
  return [
   {title:'Map repository to a scope',state:mapped?'Observed':'Needs setup',description:mapped?repo.scope:'Choose the provider-owned project scope. Directory names do not establish this relationship.'},
   {title:'Connect the provider',state:connected?'Configured':'Needs setup',description:connected?'Latest provider read: '+repo.provider_status+'. A configured connection does not prove complete coverage.':'An operator must configure the project, observer credential, snapshot and authorized readers.'},
   {title:'Enable local worker discovery',state:'Not checked',description:'The browser cannot inspect the local worker scope map. Run the read-only discovery command from the actual task checkout.'},
   {title:'Register a worker on assigned work',state:'Explicit step',description:'Select the matching assignment, read its orientation and run the printed enrollment command. Repository connection alone does not register workers.'}
  ];
 }
 function discoveryCommand(scope,checkout){
  if(!scope?.trim()||!checkout?.trim())return '';
  return 'project-intent onboard --scope '+quote(scope.trim())+' --checkout '+quote(checkout.trim());
 }
 const facts={contains,quote,repositoryPlan,discoveryCommand};
 if(typeof module!=='undefined'&&module.exports)module.exports=facts;
 root.WorkspaceViewFacts=facts;
 if(typeof document==='undefined')return;

 function select(id,label,options){
  const control=el('select');control.id=id;control.setAttribute('aria-label',label);
  for(const [value,text] of options){const option=el('option',text);option.value=value;control.append(option);}return control;
 }
 function search(id,label){const input=el('input');input.id=id;input.type='search';input.placeholder=label+'…';input.setAttribute('aria-label',label);return input;}
 function toolbar(id,label){const bar=el('div',undefined,'database-toolbar');bar.id=id;bar.append(el('span',label,'database-view-name'));return bar;}
 function count(id){const text=el('span',undefined,'database-count');text.id=id;text.setAttribute('role','status');return text;}
 function setCount(id,value){if($(id).textContent!==value)$(id).textContent=value;}
 function note(summary,text){const details=el('details',undefined,'view-note');details.append(el('summary',summary),el('p',text,'quiet'));return details;}
 function emptyView(parent,text){parent.append(el('p',text,'empty database-empty'));}
 function inspectButton(label,action){const button=el('button',label,'record-link');button.onclick=action;button.setAttribute('aria-haspopup','dialog');return button;}

 // One contextual pane for reference records and setup guidance.
 const pane=el('dialog',undefined,'workspace-inspector');pane.id='workspace-detail';pane.setAttribute('aria-labelledby','workspace-detail-title');
 const paneTop=el('div',undefined,'detail-top'),paneClose=el('button','×');paneClose.setAttribute('aria-label','Close reference details');paneClose.onclick=()=>pane.close();
 paneTop.append(el('span','Workspace details','kicker'),paneClose);const paneBody=el('div');paneBody.id='workspace-detail-content';pane.append(paneTop,paneBody);document.body.append(pane);
 let paneOrigin=null,paneIdentity=null;
 function focusToken(element){const row=element?.closest('[data-ui-record]');return {element,id:element?.id,record:row?.dataset.uiRecord,index:row?[...row.querySelectorAll('button,summary,a,input,select')].indexOf(element):-1};}
 function recordNode(key){return [...document.querySelectorAll('[data-ui-record]')].find(row=>row.dataset.uiRecord===key);}
 function restoreFocus(token){const target=token?.element?.isConnected?token.element:token?.id?$(token.id):token?.record?recordNode(token.record)?.querySelectorAll('button,summary,a,input,select')[token.index]:null;target?.focus({preventScroll:true});}
 function paneRecord(result,identity){
  if(identity.kind==='picker')return result.workspace_inventory?.repositories;
  if(identity.kind==='repository')return result.workspace_inventory?.repositories.find(repo=>repo.repository===identity.key);
  if(identity.kind==='architecture')return result.architecture.find(record=>record.key===identity.key);
  const work=result.workstreams.find(work=>work.key===identity.key);if(!work)return undefined;
  if(identity.kind!=='report')return work;
  const report=work.local_reports?.find(report=>report.id===identity.reportId);
  return report?{report,scope:work.scope_id,title:work.title,id:work.id}:undefined;
 }
 function openPane(title,identity){if(!pane.open)paneOrigin=focusToken(document.activeElement);paneIdentity={...identity,signature:JSON.stringify(paneRecord(data,identity))};paneBody.replaceChildren();const heading=el('h2',title);heading.id='workspace-detail-title';paneBody.append(heading);if(!pane.open)pane.showModal();return paneBody;}
 pane.addEventListener('close',()=>{paneIdentity=null;paneBody.replaceChildren();if(!document.querySelector('dialog[open]'))restoreFocus(paneOrigin);});
 function sourceRecord(parent,record){const details=el('details',undefined,'event-source');details.append(el('summary','Full source record'),el('pre',JSON.stringify(record,null,2)));parent.append(details);}
 function properties(parent,values){const list=el('dl',undefined,'event-properties');for(const [key,value] of values)list.append(el('dt',key),el('dd',String(value??'Not recorded')));parent.append(list);}
 function copyable(parent,title,value){
  const section=el('section',undefined,'setup-snippet'),button=el('button','Copy'),status=el('span',undefined,'quiet');status.setAttribute('role','status');
  section.append(el('h3',title),el('pre',value),button,status);
  button.onclick=async()=>{try{await navigator.clipboard.writeText(value);if(status.isConnected)status.textContent='Copied';}catch{if(status.isConnected)status.textContent='Clipboard unavailable. Select and copy the text above.';}};
  parent.append(section);
 }

 // Work: keep the existing session/rate affordances, add useful local views.
 const workBar=toolbar('work-toolbar','Workstreams'),workInput=$('work-search');workInput.parentElement.remove();workBar.append(workInput);
 const workFilter=select('work-filter','Filter workstreams',[['','All lifecycle states'],['open','Open lifecycle'],['blocked','Blocked lifecycle'],['ready','Ready lifecycle']]);
 const workGroup=select('work-group','Group workstreams',[['','No grouping'],['scope','Group by project'],['state','Group by lifecycle']]);
 const workSort=select('work-sort','Sort workstreams',[['observed','Observed execution first'],['title','Title A–Z']]);
 workBar.append(workFilter,workGroup,workSort,count('work-count'));
 document.querySelector('.work-panel>.section-head').replaceWith(workBar);
 const initiatives=el('details',undefined,'view-note initiative-disclosure');initiatives.append(el('summary','Provider initiatives'),$('initiatives'));
 document.querySelector('.initiative-rail').replaceWith(initiatives);
 document.querySelector('.work-layout').classList.add('database-layout');
 filterWorkstreams=function(){
  const host=$('workstreams');host.querySelectorAll('.work-group-heading,.database-empty').forEach(node=>node.remove());
  if(!data){setCount('work-count','Awaiting scope');return;}
  const rows=new Map([...host.querySelectorAll(':scope>.work-group[data-group]')].map(row=>{row.dataset.uiRecord='work:'+row.dataset.group;return [row.dataset.group,row];}));
  const works=data.workstreams.filter(work=>contains(work,workInput.value)&&(!workFilter.value||(workFilter.value==='open'?['active','blocked','ready'].includes(work.state):work.state===workFilter.value)));
  works.sort((a,b)=>(workSort.value==='observed'?executionRank(b)-executionRank(a):0)||(a.title||a.statement||a.id).localeCompare(b.title||b.statement||b.id)||a.key.localeCompare(b.key));
  const groupOf=work=>workGroup.value==='scope'?work.scope_id:workGroup.value==='state'?work.state:'';
  if(workGroup.value)works.sort((a,b)=>groupOf(a).localeCompare(groupOf(b)));
  const shown=new Set(works.map(work=>work.key));for(const [key,row] of rows)row.hidden=!shown.has(key);
  let lastGroup=null;for(const work of works){const row=rows.get(work.key);if(!row)continue;const group=groupOf(work);if(group&&group!==lastGroup){host.append(el('h3',group+' · '+works.filter(w=>groupOf(w)===group).length,'work-group-heading'));lastGroup=group;}host.append(row);}
  setCount('work-count',works.length+' of '+data.workstreams.length);
  if(!works.length)emptyView(host,'No workstreams match this view. Clear search or change the lifecycle filter.');
 };
 for(const control of [workInput,workFilter,workGroup,workSort])control.addEventListener(control===workInput?'input':'change',filterWorkstreams);

 // Developer lanes remain observations, with search before the display limit.
 const developerBar=toolbar('developer-toolbar','Activity board'),developerSearch=search('developer-search','Search developers and work');developerBar.append(developerSearch);
 $('developers-view').prepend(developerBar);let developerLimit=12;
 const developerMore=el('button','Show more in each lane');developerMore.id='developer-more';$('developers-view').append(developerMore);
 const originalBoard=renderDeveloperBoard;
 renderDeveloperBoard=function(result){
  const expanded=new Set([...$('developers-view').querySelectorAll('[data-ui-record]')].filter(row=>row.querySelector('details[open]')).map(row=>row.dataset.uiRecord));
  originalBoard(result);const board=ActivityViewsFacts.board(result,Date.parse(result.observed_at),true);
  let more=false;for(const [kind,id] of [['active','developer-active'],['released','developer-released'],['evidence','developer-evidence']]){
   const matches=board[kind].filter(item=>contains(item,developerSearch.value)),host=clear(id);
   for(const item of matches.slice(0,developerLimit)){const card=boardCard(item,kind);card.dataset.uiRecord='developer:'+kind+':'+item.work.key+':'+(item.worker?.session||item.release?.session||'evidence');if(expanded.has(card.dataset.uiRecord))card.querySelector('details').open=true;host.append(card);}
   $(id+'-count').textContent=matches.length>developerLimit?developerLimit+' / '+matches.length:String(matches.length);
   if(!matches.length)emptyView(host,developerSearch.value?'No matching observations.':kind==='active'?'No fresh registrations. Worker activity is unknown.':'No records in this observation.');more||=matches.length>developerLimit;
  }developerMore.hidden=!more;
 };
 developerSearch.oninput=()=>{developerLimit=12;if(data)renderDeveloperBoard(data);};developerMore.onclick=()=>{developerLimit+=12;if(data)renderDeveloperBoard(data);};

 // Handoffs: related records in selectable views instead of parallel long feeds.
 const handoffBar=toolbar('handoff-toolbar','Handoffs'),handoffSearch=search('handoff-search','Search reports and handoffs');
 const handoffType=select('handoff-type','Handoff source',[['report','Worker reports'],['handoff','Provider handoffs']]);
 const handoffState=select('handoff-state','Report publication',[['','All publication states'],['local','Local'],['pending','Pending'],['published','Published'],['uncertain','Uncertain']]);
 const handoffSort=select('handoff-sort','Sort handoffs',[['newest','Newest first'],['oldest','Oldest first']]);
 handoffBar.append(handoffSearch,handoffType,handoffState,handoffSort,count('handoff-count'));
 const handoffLayout=document.querySelector('.handoff-layout');handoffLayout.classList.add('database-layout');handoffLayout.prepend(handoffBar);
 const handoffFeed=document.querySelector('.handoff-feed');handoffFeed.querySelector('.section-head').remove();handoffFeed.querySelector(':scope>p').remove();
 document.querySelector('.handoff-rail').hidden=true;
 const handoffMore=el('button','Show more records');handoffMore.id='handoff-more';handoffFeed.append(handoffMore);let handoffLimit=40;
 function renderHandoffView(result){
  const type=handoffType.value;handoffState.hidden=type!=='report';
  // Keep undated records available here, even though Calendar cannot plot them.
  const records=type==='report'?result.workstreams.flatMap(work=>(work.local_reports||[]).map(report=>({work,report,at:report.created_at,summary:report.payload.packet.summary,state:report.publication?.state||'local'}))):result.workstreams.filter(work=>work.handoff_summary).map(work=>({work,at:work.handoff_at,summary:work.handoff_summary}));
  const matched=records.filter(record=>contains([record.summary,record.report,record.at,record.state,record.work.key,record.work.title,record.work.statement,record.work.provider_identifier],handoffSearch.value)&&(type!=='report'||!handoffState.value||record.state===handoffState.value));
  matched.sort((a,b)=>{const at=Date.parse(a.at),bt=Date.parse(b.at);if(!Number.isFinite(at))return Number.isFinite(bt)?1:0;if(!Number.isFinite(bt))return -1;return (handoffSort.value==='oldest'?1:-1)*(at-bt);});
  const host=clear('reports');host.classList.add('reference-feed');
  for(const record of matched.slice(0,handoffLimit)){
   const row=el('article',undefined,'reference-row'),main=el('div'),meta=el('div',undefined,'reference-meta');row.dataset.uiRecord=type+':'+record.work.key+':'+(record.report?.id||'handoff');
   const title=inspectButton(ActivityViewsFacts.preview(record.summary,160),()=>{
    const body=openPane(type==='report'?'Worker report':'Provider handoff',{kind:type,key:record.work.key,reportId:record.report?.id,recordKey:row.dataset.uiRecord});
    properties(body,[['Project',record.work.scope_id],['Workstream',record.work.title||record.work.id],['Recorded',record.at?displayTime(record.at):'No timestamp'],['Publication',record.state||'Provider record']]);
    if(record.report)body.append(reportCard(record.report,record.work,true));else body.append(el('p',record.summary,'event-full-summary'));
    const context=workButton(record.work,'Open workstream');context.onclick=()=>{pane.close();showDetail(record.work.key);};body.append(context);sourceRecord(body,record.report||record.work);
   });
   main.append(title,el('span',record.work.scope_id+' · '+(record.work.provider_identifier||record.work.id),'reference-subtitle'));
   meta.append(el('span',record.state||'Provider handoff','board-state'),el('time',Number.isFinite(Date.parse(record.at))?displayTime(record.at):'Undated'));
   row.append(main,meta);host.append(row);
  }
  if(!matched.length)emptyView(host,'No records match this view. Try another source or clear the filters.');
  setCount('handoff-count',matched.length+' records');handoffMore.hidden=matched.length<=handoffLimit;
  $('report-coverage').textContent='Showing '+Math.min(matched.length,handoffLimit)+' of '+matched.length+' matching records, from '+records.length+' available '+(type==='report'?'worker reports':'provider handoffs')+'. Reports are worker assertions; publication does not certify them. '+result.workstreams.map(w=>w.id+': '+w.report_coverage).join(' · ');
 }
 for(const control of [handoffSearch,handoffType,handoffState,handoffSort])control.addEventListener(control===handoffSearch?'input':'change',()=>{handoffLimit=40;if(data)renderHandoffView(data);});handoffMore.onclick=()=>{handoffLimit+=40;if(data)renderHandoffView(data);};

 // Reference ledgers: searchable declarations with long properties in a peek.
 const archBar=toolbar('architecture-toolbar','Constraints'),archSearch=search('architecture-search','Search constraints');
 const archState=select('architecture-state','Constraint state',[['','All states'],['accepted','Accepted'],['proposed','Proposed'],['superseded','Superseded']]);archBar.append(archSearch,archState,count('architecture-count'));
 document.querySelector('.architecture-view>.ledger-head').before(archBar);
 const environmentBar=toolbar('environment-toolbar','Requirements'),environmentSearch=search('environment-search','Search requirements');
 const environmentFilter=select('environment-filter','Requirement limitations',[['','All requirements'],['limited','Limitations recorded']]);environmentBar.append(environmentSearch,environmentFilter,count('environment-count'));document.querySelector('.matrix-head').before(environmentBar);
 function renderReferences(result){
  const arch=clear('architecture'),records=result.architecture.filter(record=>contains(record,archSearch.value)&&(!archState.value||record.state===archState.value));
  for(const record of records){
   const row=el('article',undefined,'architecture-row'),identity=el('div'),statement=el('div',undefined,'architecture-declaration'),reach=el('div',undefined,'architecture-reach');
   row.dataset.uiRecord='architecture:'+record.key;
   const show=()=>{const body=openPane(record.key.split(':').slice(1).join(':'),{kind:'architecture',key:record.key,recordKey:row.dataset.uiRecord});properties(body,[['Scope',record.scope],['Kind',record.kind],['State',record.state],['Revision',record.revision]]);body.append(el('p',record.statement,'event-full-summary'),el('h3','Applicable workstreams'));for(const key of record.workstreams){const work=result.workstreams.find(w=>w.key===key);if(work){const button=workButton(work,work.title||work.id);button.onclick=()=>{pane.close();showDetail(key);};body.append(button);}}sourceRecord(body,record);};
   identity.append(el('span',record.kind+' · '+record.state+' · r'+record.revision,'identifier'),inspectButton(record.key.split(':').slice(1).join(':'),show));
   statement.append(el('p',ActivityViewsFacts.preview(record.statement,160)));reach.append(el('strong',String(record.workstreams.length)),el('span','workstreams'),scopeName('span',record.scope));row.append(identity,statement,reach);arch.append(row);
  }
  setCount('architecture-count',records.length+' records');if(!records.length)emptyView(arch,'No constraints match this view.');
  const env=clear('environments'),requirements=result.workstreams.filter(w=>w.environment.requirement&&contains([w.title,w.statement,w.key,w.environment],environmentSearch.value)&&(!environmentFilter.value||w.environment.requirement.known_limitations?.length));
  for(const work of requirements){const requirement=work.environment.requirement,row=el('article',undefined,'environment-row'),identity=el('div'),profile=el('div'),limitations=el('div');identity.append(inspectButton(ActivityViewsFacts.preview(work.title||work.statement||work.id,95),()=>showDetail(work.key)),el('small',work.provider_identifier||work.id));profile.append(el('strong',typeof requirement==='string'?requirement:requirement.profile||requirement.requirement||'Declared requirement'));limitations.append(el('p',requirement.known_limitations?.length?ActivityViewsFacts.preview(requirement.known_limitations.join(' · '),120):'No limitations recorded'));row.append(identity,profile,limitations,workButton(work,'Inspect'));env.append(row);}
  for(const [index,row] of [...env.children].entries())row.dataset.uiRecord='environment:'+requirements[index].key;
  setCount('environment-count',requirements.length+' records');if(!requirements.length)emptyView(env,'No declared requirements match this view.');
 }
 for(const control of [archSearch,archState,environmentSearch,environmentFilter])control.addEventListener(control.type==='search'?'input':'change',()=>{if(data)renderReferences(data);});

 // Sources: repository setup is discoverable; provenance gets its own full view.
 const sourcesLayout=$('sources-layout');sourcesLayout.classList.add('database-layout');
 const sourceBar=toolbar('source-toolbar','Connections'),sourceSearch=search('source-search','Search connections');
 const sourceMode=select('source-mode','Connection view',[['repositories','Repositories'],['scopes','Provider & execution sources']]);
 const sourceFilter=select('source-filter','Repository connection',[['','All connections'],['needs-setup','Needs setup'],['configured','Configured']]);
 const setupButton=el('button','Set up repository');setupButton.id='repository-setup';setupButton.setAttribute('aria-haspopup','dialog');
 sourceBar.append(sourceSearch,sourceMode,sourceFilter,count('source-count'),setupButton);sourcesLayout.prepend(sourceBar);
 function setupRepository(repo){
  const body=openPane(repo.repository,{kind:'repository',key:repo.repository,recordKey:'repository:'+repo.repository});
  body.append(el('p','Repository enrollment','setup-eyebrow'),el('p','This guide prepares the steps. It does not change configuration or enroll anything from the browser.','quiet'));
  const steps=el('ol',undefined,'setup-steps');for(const step of repositoryPlan(repo)){const item=el('li'),head=el('div');head.append(el('h3',step.title),el('span',step.state,'board-state'));item.append(head,el('p',step.description));steps.append(item);}body.append(steps);
  const fields=el('div',undefined,'setup-fields');const scope=el('input'),checkout=el('input');scope.id='setup-scope';scope.value=repo.scope||'';scope.placeholder='organization/project';checkout.id='setup-checkout';checkout.value=repo.checkout||'';
  for(const [labelText,input] of [['Project scope',scope],['Actual task checkout',checkout]]){const label=el('label',labelText);label.htmlFor=input.id;fields.append(label,input);}body.append(fields);
  body.append(el('p','Use your task worktree if it differs from the canonical checkout. With the local scope map configured, run this in a terminal where project-intent is installed. In the SayHi workspace, the launcher is bin/project-intent.','quiet'));
  const command=el('div');body.append(command);const update=()=>{command.replaceChildren();const value=discoveryCommand(scope.value,checkout.value);if(value)copyable(command,'1. Discover existing assignments (read-only)',value);else command.append(el('p','Enter the provider-owned scope and task checkout to prepare the discovery command.','quiet'));};update();scope.oninput=update;checkout.oninput=update;
  body.append(note('2. Select and register on an assignment','Discovery returns exact scope and workstream IDs. Rerun onboard with --workstream and the selected ID, inspect the assignment, then use its printed enrollment command for your own session. If no assignment fits, use the documented task-register preview flow for work already assigned to you.'));
  const recipe=el('details',undefined,'setup-recipe');recipe.append(el('summary','Operator setup recipe · when a connection is missing'));
  recipe.append(el('p','These are individual entries, not replacement configuration files. Replace every REPLACE_* value and review existing entries first. Never paste credentials into this page.'));
  copyable(recipe,'Append this one entry to the existing service scopes array',JSON.stringify({id:repo.scope||'REPLACE_SCOPE',label:'REPLACE_LABEL',provider:{kind:'itsaplan',url:'REPLACE_PROVIDER_URL',project:'REPLACE_PROJECT_CODE',token_file:'/private/REPLACE_OBSERVER_TOKEN_FILE'},cache:'/private/REPLACE_SCOPE_SNAPSHOT.json',enrollment_sources:[{directory:'/private/REPLACE_SCOPE_ENROLLMENTS'}]},null,2));
  recipe.append(el('p','If this scope already exists, update that entry rather than adding a duplicate. Preserve all other scopes.'));
  copyable(recipe,'Add this key inside workspace_inventory.scope_by_repository',JSON.stringify({[repo.repository]:repo.scope||'REPLACE_SCOPE'},null,2));
  recipe.append(el('p','Keep the existing workspace_inventory.root and every other repository mapping. Do not replace workspace_inventory with this fragment.'));
  copyable(recipe,'Add this entry inside the credential-free worker map’s scopes object',JSON.stringify({[repo.scope||'REPLACE_SCOPE']:{snapshot:'/private/REPLACE_SCOPE_SNAPSHOT.json',enrollment_directory:'/private/REPLACE_SCOPE_ENROLLMENTS'}},null,2));
  recipe.append(el('p','An operator must first create or select the native provider project and issue its least-privilege observer credential. Add the scope only to intended principals’ existing scopes lists. The worker map and observer must use the same snapshot and enrollment directory. Keep private files outside Git.'));
  recipe.append(el('p','Apply through the established service configuration/restart procedure, then refresh Sources to verify provider reads. Local Git history and task creation each require separate opt-in configuration; neither follows from a repository mapping. The browser cannot verify those capabilities.'));body.append(recipe);
 }
 setupButton.onclick=()=>{const repos=data?.workspace_inventory?.repositories||[];const body=openPane('Set up a repository',{kind:'picker'});body.append(el('p','Choose an observed repository to inspect its connection and prepare the setup steps.','quiet'));for(const repo of repos)body.append(inspectButton(repo.repository+' · '+(repo.intent_status==='configured'?'Configured':'Needs setup'),()=>setupRepository(repo)));if(!repos.length)emptyView(body,'No repositories in this authorized inventory. An operator must configure the canonical repository root and inventory access first.');body.append(el('p','Only immediate canonical Git directories visible to this access and scope filter are listed. A missing repository must be added through the local workspace configuration.','quiet'));};
 renderWorkspaceInventory=function(result){
  const inventory=result.workspace_inventory;workspaceSummary.hidden=!inventory;setupButton.hidden=!inventory;
  const host=workspaceSection;host.replaceChildren();sourceFilter.hidden=sourceMode.value!=='repositories';host.hidden=sourceMode.value!=='repositories';document.querySelector('.source-coverage-panel').hidden=sourceMode.value!=='scopes';
  if(!inventory){emptyView(host,'Repository inventory is not available to this access. Provider sources remain available in the view selector.');return;}
  workspaceSummary.textContent=inventory.repository_count+' repos · '+inventory.connected_count+' intent connections';
  const repos=(inventory.repositories||[]).filter(repo=>contains(repo,sourceSearch.value)&&(!sourceFilter.value||(sourceFilter.value==='configured'?repo.intent_status==='configured':repo.intent_status!=='configured')));
  if(sourceMode.value==='repositories')setCount('source-count',repos.length+' repositories');
  const table=el('table',undefined,'inventory-table');const head=el('thead'),tr=el('tr');for(const title of ['Repository','Project scope','Connection',''])tr.append(el('th',title));head.append(tr);table.append(head);const rows=el('tbody');
  for(const repo of repos){const row=el('tr');row.dataset.repository=repo.repository;const name=el('td'),scope=el('td'),state=el('td'),action=el('td');name.append(inspectButton(repo.repository,()=>setupRepository(repo)));scope.append(el('span',repo.scope||'Not mapped'));if(repo.enrolled_workstreams!==null)scope.append(el('small',repo.enrolled_workstreams+' scope workstreams'));state.append(el('span',repo.intent_status==='configured'?'Configured':'Needs setup','board-state'),el('small',repo.intent_status==='configured'?'Provider: '+repo.provider_status:'Repository '+(repo.scope?'mapped; provider missing':'not mapped')));action.append(inspectButton(repo.intent_status==='configured'?'Details':'Set up',()=>setupRepository(repo)));row.append(name,scope,state,action);rows.append(row);}table.append(rows);host.append(table);
  for(const row of rows.children)row.dataset.uiRecord='repository:'+row.dataset.repository;
  if(!repos.length)emptyView(host,inventory.status==='observed'?'No repositories match this view.': 'Repository inventory is '+inventory.status+'. No complete inventory is available.');
  const coverage=note('Inventory coverage',inventory.meaning||'Inventory not configured.');const time=el('p','Inventory: '+inventory.status+' · observed '+(inventory.observed_at||'unknown'),'quiet');time.id='workspace-inventory-time';coverage.append(time);host.append(coverage);
 };
 function filterSources(){const items=[...$('sources').children];for(const item of items)item.hidden=!contains(item.textContent,sourceSearch.value);if(sourceMode.value==='scopes')setCount('source-count',items.filter(item=>!item.hidden).length+' scopes');}
 for(const control of [sourceSearch,sourceMode,sourceFilter])control.addEventListener(control===sourceSearch?'input':'change',()=>{if(data){renderWorkspaceInventory(data);filterSources();}});

 // Map already has focus controls; tuck its explanatory material into one disclosure.
 const mapLegend=document.querySelector('.map-legend'),mapNote=el('details',undefined,'view-note');mapNote.append(el('summary','Map legend & observation limits'));const mapCaveat=mapLegend.nextElementSibling;mapLegend.before(mapNote);mapNote.append(mapLegend,mapCaveat);
 const priorRender=render;
 render=function(result){
  const focus=focusToken(document.activeElement);
  priorRender(result);renderHandoffView(result);renderReferences(result);filterSources();
  if(paneIdentity){const current=paneRecord(result,paneIdentity);if(!current)pane.close();else if(JSON.stringify(current)!==paneIdentity.signature){
   const scope=$('setup-scope')?.value,checkout=$('setup-checkout')?.value;
   const scroll=pane.scrollTop,details=[...paneBody.querySelectorAll('details')].map(detail=>detail.open),controlIndex=[...paneBody.querySelectorAll('button,summary,a,input,select')].indexOf(document.activeElement);
   const refreshButton=paneIdentity.kind==='picker'?setupButton:recordNode(paneIdentity.recordKey)?.querySelector('button');
   if(refreshButton){refreshButton.click();if(scope!==undefined&&$('setup-scope')){$('setup-scope').value=scope;$('setup-checkout').value=checkout;$('setup-scope').dispatchEvent(new Event('input'));}paneBody.querySelectorAll('details').forEach((detail,index)=>{detail.open=details[index]||false;});pane.scrollTop=scroll;if(controlIndex>=0)paneBody.querySelectorAll('button,summary,a,input,select')[controlIndex]?.focus({preventScroll:true});}else pane.close();
  }}
  if(!focus.element?.isConnected)restoreFocus(focus);
 };
 $('scope').addEventListener('change',()=>{pane.close();paneBody.replaceChildren();developerLimit=12;handoffLimit=40;developerMore.hidden=true;handoffMore.hidden=true;setupButton.hidden=true;for(const id of ['work-count','handoff-count','architecture-count','environment-count','source-count'])$(id).textContent='Awaiting scope';});
 if(data)render(data);
})(typeof globalThis==='undefined'?this:globalThis);
