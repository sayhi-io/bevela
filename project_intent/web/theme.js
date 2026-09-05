/* Browser-local preference only. Never part of project/provider state. */
'use strict';
(() => {
 const key='sayhi-project-intent-theme';
 const system=window.matchMedia('(prefers-color-scheme: light)');
 let preference='system';
 try { const saved=localStorage.getItem(key);if(['light','dark','system'].includes(saved))preference=saved; } catch {}
 function apply(){document.documentElement.dataset.theme=preference==='system'?(system.matches?'light':'dark'):preference;}
 apply();
 system.addEventListener('change',()=>{if(preference==='system')apply();});
 window.addEventListener('storage',event=>{if(event.key===key){preference=['light','dark','system'].includes(event.newValue)?event.newValue:'system';apply();const control=document.getElementById('theme');if(control)control.value=preference;}});
 document.addEventListener('DOMContentLoaded',()=>{
  const control=document.getElementById('theme');control.value=preference;
  control.addEventListener('change',()=>{preference=control.value;apply();try{localStorage.setItem(key,preference);}catch{}});
 });
})();
