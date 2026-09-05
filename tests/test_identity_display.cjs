/* DOM-construction checks without a browser or provider connection. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const context = {document: {createElement: tag => ({
  tag, children: [], append(...nodes) { this.children.push(...nodes); },
})}};
vm.createContext(context);
const source = fs.readFileSync(path.join(__dirname, '../project_intent/web/app.js'), 'utf8');
vm.runInContext(source.split('function empty(')[0], context);
const text = node => node.textContent ?? node.children.map(text).join('');
for (const scope of ['sayhi/sparkops', 'sayhi/project-intent', 'org/product/subproject', 'standalone']) {
  const card = context.scopeName('span', scope);
  const detail = context.scopeName('p', scope);
  assert.equal(text(card), scope);
  assert.equal(card.children.at(-1).tag, 'mark');
  assert.equal(text(card.children.at(-1)), scope.slice(scope.lastIndexOf('/') + 1));
  assert.equal(card.children.at(-1).className, detail.children.at(-1).className);
  assert.equal(text(context.qualifiedName('li', scope + ':DEV-CLI-CI-01')), scope + ':DEV-CLI-CI-01');
}
for (const id of ['DEV-CLI-CI-01', 'DEV-FRONTEND-CI-01', 'DEV-MCP-COMPAT-01']) {
  const work = {id, key: 'sayhi/sparkops:' + id};
  const card = context.workstreamName('strong', work);
  assert.equal(text(card), id);
  assert.equal(text(card.children[1]), id.slice(4, -3));
  assert.equal(card.children[1].className, context.workstreamName('h2', work).children[1].className);
}
// Untrusted labels stay text, not HTML.
assert.equal(context.scopeName('span', 'sayhi/<img onerror=bad>').children.at(-1).textContent, '<img onerror=bad>');
console.log('Identity display checks passed: intact identifiers, distinct scope segments, stable colors, text-only labels.');
const observe=context.executionObservation;
assert.equal(observe({state:'active'},1000).kind,'unknown');
assert.equal(observe({activity:{status:'recent',last_report_at:980}},1000).kind,'reporting');
assert.equal(observe({activity:{status:'recent',last_report_at:800}},1000).kind,'unknown');
assert.equal(observe({activity:{status:'recent',last_report_at:1100}},1000).kind,'unknown');
assert.equal(observe({workers:[{status:'active',expires_at:'1970-01-01T00:20:00Z'}]},1000).kind,'present');
assert.equal(observe({workers:[{status:'active',expires_at:'1970-01-01T00:10:00Z'}]},1000).kind,'unknown');
console.log('Execution-label checks passed: lifecycle is not live, recent/stale/future reports, fresh/expired leases.');
