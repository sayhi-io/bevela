/* Read-only, current-page index. No copied interactive DOM or additional data source. */
(() => {
 'use strict';
 const main=document.querySelector('main');
 const make=(tag,text,className)=>{const node=document.createElement(tag);if(text!==undefined)node.textContent=text;if(className)node.className=className;return node;};
 const vector=(kind)=>{const svg=document.createElementNS('http://www.w3.org/2000/svg','svg');svg.setAttribute('viewBox','0 0 24 24');svg.setAttribute('aria-hidden','true');const path=document.createElementNS(svg.namespaceURI,'path');path.setAttribute('d',({map:'M4 4h5v16H4zM12 4h8v6h-8zM12 14h8v6h-8z',list:'M9 6h12M9 12h12M9 18h12M3 6h1M3 12h1M3 18h1',cards:'M4 3h16v7H4zM4 14h16v7H4z',close:'M6 6l12 12M18 6L6 18'})[kind]);svg.append(path);return svg;};
 const button=(label,kind)=>{const b=make('button');b.type='button';b.setAttribute('aria-label',label);b.title=label;b.append(vector(kind));return b;};
 const dock=make('div',undefined,'minimap-dock');
 const trigger=button('Open page minimap','map');trigger.id='minimap-toggle';trigger.setAttribute('aria-expanded','false');trigger.setAttribute('aria-controls','page-minimap');trigger.append(make('span','Page map'));
 const panel=make('aside');panel.id='page-minimap';panel.hidden=true;panel.setAttribute('aria-labelledby','minimap-title');
 const header=make('div',undefined,'minimap-header');const title=make('h2','On this page');title.id='minimap-title';
 const close=button('Close page minimap','close');header.append(title,close);
 const toolbar=make('div',undefined,'minimap-toolbar');const modes=make('div',undefined,'minimap-modes');modes.setAttribute('role','group');modes.setAttribute('aria-label','Minimap view');
 const list=button('List view','list'),cards=button('Card view','cards');list.setAttribute('aria-pressed','true');cards.setAttribute('aria-pressed','false');modes.append(list,cards);
 const context=make('span',undefined,'minimap-context');toolbar.append(modes,context);
 const index=make('nav');index.id='minimap-index';index.setAttribute('aria-label','Sections on this page');
 const source=make('p',undefined,'minimap-source');source.setAttribute('role','status');
 const footer=make('div',undefined,'minimap-footer');
 const sizeLabel=make('label','Width');sizeLabel.htmlFor='minimap-width';const width=make('input');width.type='range';width.id='minimap-width';width.step='8';width.title='Page minimap width';footer.append(sizeLabel,width,make('span','Jump to context'));
 const grip=make('div',undefined,'minimap-grip');grip.setAttribute('aria-hidden','true');grip.append(make('span'));
 panel.append(header,toolbar,index,source,footer,grip);dock.append(panel,trigger);document.body.append(dock);
 let items=[],signature='',mode='list',wantedWidth=304,activeKey=null,scheduled=false;
 function bounds(){const left=innerWidth<=700?16:120;return {min:Math.min(264,innerWidth-left-20),max:Math.min(520,innerWidth-left-20)};}
 function resize(value){const b=bounds();wantedWidth=Math.min(b.max,Math.max(b.min,value));panel.style.width=wantedWidth+'px';width.min=b.min;width.max=b.max;width.value=wantedWidth;}
 resize(wantedWidth);
 function setOpen(open,restore=true){panel.hidden=!open;trigger.setAttribute('aria-expanded',String(open));trigger.setAttribute('aria-label',open?'Close page minimap':'Open page minimap');if(open){refresh();close.focus();}else if(restore)trigger.focus();}
 trigger.onclick=()=>setOpen(panel.hidden);close.onclick=()=>setOpen(false);
 document.addEventListener('keydown',event=>{if(event.key==='Escape'&&!panel.hidden&&!document.querySelector('dialog[open]')){event.preventDefault();setOpen(false);}});
 function setMode(value){mode=value;panel.dataset.mode=mode;list.setAttribute('aria-pressed',String(mode==='list'));cards.setAttribute('aria-pressed',String(mode==='cards'));}
 list.onclick=()=>setMode('list');cards.onclick=()=>setMode('cards');setMode(mode);
 width.oninput=()=>resize(Number(width.value));
 let drag=null;
 grip.addEventListener('pointerdown',event=>{if(event.button!==0)return;drag={x:event.clientX,width:panel.getBoundingClientRect().width};grip.setPointerCapture(event.pointerId);panel.classList.add('resizing');event.preventDefault();});
 grip.addEventListener('pointermove',event=>{if(drag)resize(drag.width+event.clientX-drag.x);});
 const endDrag=()=>{drag=null;panel.classList.remove('resizing');};grip.addEventListener('pointerup',endDrag);grip.addEventListener('pointercancel',endDrag);grip.addEventListener('lostpointercapture',endDrag);
 function collect(){const sections=[...main.querySelectorAll(':scope > section[data-view]')].filter(s=>!s.hidden);return sections.flatMap(section=>{
  const container=section.querySelector('.tiles, #workstreams');
  const key=container?.id;const heading=section.querySelector('h2');
  if(!key||!heading)return null;
  const entries=[...container.children].filter(node=>!node.hidden&&!node.classList.contains('empty'));
  if(sections.length===1&&entries.length){const seen=new Map();return entries.map(node=>{
   const title=(node.querySelector('.qualified-name')||node.querySelector('h3'))?.textContent||heading.textContent;
   const scope=node.querySelector('.scope-name')?.textContent||'';
   const identity=JSON.stringify([key,scope,title]);const duplicate=seen.get(identity)||0;seen.set(identity,duplicate+1);
   return {key:identity+':'+duplicate,section:node,title,count:null,previews:[scope,node.querySelector('p')?.textContent].filter(Boolean),empty:null};
  });}
  const previews=entries.slice(0,3).map(node=>{
   const label=node.querySelector('.work-title,h3,.qualified-name,.identity-name');
   return (label?.textContent||node.querySelector('p')?.textContent||'').trim();
  }).filter(Boolean);
  return {key,section,title:heading.textContent,count:entries.length,previews,empty:container.querySelector('.empty')?.textContent||null};
 }).filter(Boolean);}
 function refresh(){
  items=collect();context.textContent=document.querySelector('#view-title').textContent;
  source.textContent=document.querySelector('#connection-summary').textContent;
  source.classList.toggle('is-retained',!document.querySelector('#error').hidden);
  const next=JSON.stringify(items.map(({key,title,count,previews,empty})=>({key,title,count,previews,empty})));
  if(next!==signature){
   signature=next;const focused=document.activeElement?.closest('[data-map-key]')?.dataset.mapKey;const scroll=index.scrollTop;
   index.replaceChildren();
   items.forEach((item,i)=>{
    const entry=make('button',undefined,'minimap-entry');entry.type='button';entry.dataset.mapKey=item.key;
    entry.setAttribute('aria-label',`${i+1}. ${item.title}`+(item.count===null?'':`, ${item.count} visible items`));
    const number=make('span',String(i+1).padStart(2,'0'),'minimap-number');number.setAttribute('aria-hidden','true');
    const body=make('span',undefined,'minimap-entry-body');body.append(make('strong',item.title),make('span',item.count===null?'Page item':item.count+' visible '+(item.count===1?'item':'items'),'minimap-count'));
    const preview=make('span',undefined,'minimap-preview');preview.setAttribute('aria-hidden','true');
    for(const text of item.previews)preview.append(make('span',text,'minimap-preview-row'));
    if(item.count===0)preview.append(make('span',item.empty||'No items in this observation','minimap-preview-empty'));
    if(item.count>3)preview.append(make('span','+'+(item.count-3)+' more','minimap-more'));
    body.append(preview);entry.append(number,body);
    entry.onclick=()=>{const current=items.find(candidate=>candidate.key===item.key);if(!current)return;const heading=current.section.querySelector('h2,h3')||current.section;heading.tabIndex=-1;heading.focus({preventScroll:true});current.section.scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth',block:'start'});activeKey=current.key;markActive();};
    index.append(entry);
   });
   index.scrollTop=scroll;
   if(focused){const target=[...index.children].find(e=>e.dataset.mapKey===focused);if(target)target.focus({preventScroll:true});else close.focus({preventScroll:true});}
  }
  track();
 }
 function markActive(){for(const entry of index.children){if(entry.dataset.mapKey===activeKey)entry.setAttribute('aria-current','location');else entry.removeAttribute('aria-current');}}
 function track(){const threshold=innerWidth<=700?110:90;let selected=items[0];for(const item of items){if(item.section.getBoundingClientRect().top<=threshold)selected=item;else break;}const previous=items.find(item=>item.key===activeKey);if(previous&&selected&&Math.abs(previous.section.getBoundingClientRect().top-selected.section.getBoundingClientRect().top)<2)selected=previous;activeKey=selected?.key||null;markActive();}
 function schedule(){if(scheduled)return;scheduled=true;requestAnimationFrame(()=>{scheduled=false;refresh();});}
 new MutationObserver(schedule).observe(main,{childList:true,subtree:true,attributes:true,attributeFilter:['hidden']});
 window.addEventListener('scroll',track,{passive:true});window.addEventListener('resize',()=>{resize(wantedWidth);track();});
 document.querySelector('#scope').addEventListener('change',()=>{items=[];signature='';index.replaceChildren();activeKey=null;});
 refresh();
})();
