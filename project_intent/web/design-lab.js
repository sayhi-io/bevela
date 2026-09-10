/* Optional UI compositions over existing components. No model or provider writes. */
(() => {
 const F=window.IntentIdentity;
 const selected=F.design(new URLSearchParams(location.search).get('design'));
 document.documentElement.dataset.design=selected;
 function avatar(work){
  const {hue,cells}=F.pattern(work.scope_id,work.id),ns='http://www.w3.org/2000/svg';
  const svg=document.createElementNS(ns,'svg');svg.setAttribute('viewBox','0 0 36 36');svg.setAttribute('class','work-identicon');svg.setAttribute('aria-hidden','true');svg.setAttribute('focusable','false');
  const tile=(x,y,w,h,fill,rx)=>{const r=document.createElementNS(ns,'rect');for(const [k,v] of Object.entries({x,y,width:w,height:h,fill,rx}))r.setAttribute(k,String(v));svg.append(r);};
  tile(0,0,36,36,`hsl(${hue} 24% 91%)`,8);
  for(const [x,y] of cells)tile(5+x*5.2,5+y*5.2,4.7,4.7,`hsl(${hue} 40% 34%)`,.6);
  return svg;
 }
 const priorCard=renderWorkCard;
 window.workIdenticon=avatar;
 renderWorkCard=function(w){const card=priorCard(w);card.querySelector('.work-title').prepend(avatar(w));return card;};
 const priorDetail=showDetail;
 showDetail=function(key){priorDetail(key);const w=data?.workstreams.find(w=>w.key===key);if(w)$('detail-content').querySelector('.detail-hero')?.prepend(avatar(w));};
 const priorReport=reportCard;
 reportCard=function(report,work,full=false){const card=priorReport(report,work,full);card.prepend(avatar(work));return card;};
 const picker=el('label',undefined,'design-picker');picker.append(el('span','Design'));
 const select=el('select');select.setAttribute('aria-label','Mission Control design');
 for(const [id,name] of [['default','Current'],['plan','Plan'],['studio','Studio'],['console','Console']]){const option=el('option',name);option.value=id;select.append(option);}
 select.value=selected;select.onchange=()=>{const url=new URL(location.href);if(select.value==='default')url.searchParams.delete('design');else url.searchParams.set('design',select.value);location.assign(url.href);};picker.append(select);document.querySelector('.display-options-panel').append(picker);
 // Marks are generated client-side from the same scoped Workstream identity.
 // No external avatar service, new PM fields, title hash, or status-based color.
})();
