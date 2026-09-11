'use strict';
const test=require('node:test');
const assert=require('node:assert/strict');
const {contains,quote,repositoryPlan,discoveryCommand}=require('../project_intent/web/workspace-views.js');

test('full-record search includes details omitted from visible previews',()=>{
 assert(contains({summary:'Short title',detail:'Tail evidence '+ 'a'.repeat(100)+' Needle'},'needle'));
 assert(contains({scope:'org/project'},' ORG/PROJECT '));
 assert(!contains({summary:'Other'},'needle'));
});
test('a configured repository does not imply worker configuration or enrollment',()=>{
 const plan=repositoryPlan({scope:'org/project',intent_status:'configured',provider_status:'offline'});
 assert.deepEqual(plan.map(s=>s.state),['Observed','Configured','Not checked','Explicit step']);
 assert.match(plan[1].description,/offline/);
});
test('unmapped and mapped-but-disconnected repositories have distinct setup gaps',()=>{
 assert.deepEqual(repositoryPlan({intent_status:'not-mapped'}).slice(0,2).map(s=>s.state),['Needs setup','Needs setup']);
 assert.deepEqual(repositoryPlan({scope:'org/project',intent_status:'scope-not-connected'}).slice(0,2).map(s=>s.state),['Observed','Needs setup']);
});
test('generated discovery is read-only and shell-quotes both inputs',()=>{
 assert.equal(discoveryCommand('org/project',"/tmp/it's $(touch secret); `id`"),"project-intent onboard --scope 'org/project' --checkout '/tmp/it'\"'\"'s $(touch secret); `id`'");
 assert.equal(quote("x'y"),"'x'\"'\"'y'");
 assert.equal(discoveryCommand('', '/tmp/task'),'');
 assert.equal(discoveryCommand('org/project','  '),'');
});
