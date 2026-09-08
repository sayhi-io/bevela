// Study03 draft acceptance. No live services; candidate is read-only input.
import test from 'node:test';
import assert from 'node:assert/strict';
import { DatabaseSync } from 'node:sqlite';
import { readFileSync, readdirSync } from 'node:fs';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

if (!process.env.TRIAL_CHECKOUT) throw new Error('TRIAL_CHECKOUT required');
const root = resolve(process.env.TRIAL_CHECKOUT);
const worker = (await import(pathToFileURL(root + '/src/worker.mjs'))).default;
const { ensureComponents } = await import(pathToFileURL(root + '/src/state.mjs'));
const { COMPONENTS } = await import(pathToFileURL(root + '/src/components.mjs'));

async function fixture(t) {
  const sqlite = new DatabaseSync(':memory:');
  t.after(() => sqlite.close());
  for (const file of readdirSync(root + '/migrations').filter(f => f.endsWith('.sql')).sort()) {
    sqlite.exec(readFileSync(root + '/migrations/' + file, 'utf8'));
  }
  const db = {
    prepare(sql) {
      const statement = sqlite.prepare(sql);
      const bound = (values = []) => ({
        bind: (...args) => bound(args),
        all: async () => ({ results: statement.all(...values), success: true }),
        first: async column => {
          const row = statement.get(...values);
          return column ? row?.[column] ?? null : row ?? null;
        },
        run: async () => ({ ...statement.run(...values), success: true }),
      });
      return bound();
    },
    async batch(statements) {
      sqlite.exec('BEGIN');
      try {
        const results = [];
        for (const statement of statements) results.push(await statement.run());
        sqlite.exec('COMMIT'); return results;
      } catch (error) { sqlite.exec('ROLLBACK'); throw error; }
    },
  };
  await ensureComponents(db, '2026-01-01T00:00:00.000Z');
  const rows = Array.from({ length: 67 }, (_, i) => ({
    id: `incident-${String(i).padStart(3, '0')}`, componentId: COMPONENTS[i % 2].id,
    state: i % 3 ? 'investigating' : 'resolved',
    startedAt: new Date(Date.UTC(2026, 0, 1, 0, Math.floor(i / 3))).toISOString(),
  }));
  const insert = row => sqlite.prepare(`INSERT INTO incidents
    (id,component_id,summary,severity,state,started_at,updated_at,resolved_at)
    VALUES (?,?,?,'degraded',?,?,?,?)`).run(row.id,row.componentId,row.id,row.state,
      row.startedAt,row.startedAt,row.state === 'resolved' ? row.startedAt : null);
  rows.forEach(insert);
  const get = params => worker.fetch(new Request('http://localhost/api/incidents?' +
    new URLSearchParams(params)), { DB: db }, {});
  const page = async params => {
    const response = await get({ view: 'history-v2', ...params });
    assert.equal(response.status, 200);
    const body = await response.json();
    assert.ok(Array.isArray(body.incidents));
    assert.ok(body.snapshot?.id && Number.isFinite(Date.parse(body.snapshot.expiresAt)));
    assert.ok(body.nextCursor === null || typeof body.nextCursor === 'string');
    return body;
  };
  return { sqlite, rows, insert, get, page };
}
const sorted = rows => [...rows].sort((a,b) =>
  b.startedAt.localeCompare(a.startedAt) || b.id.localeCompare(a.id));

test('snapshot traversal preserves membership and displayed state after updates and backdated inserts', async t => {
  const f = await fixture(t);
  const filters = { component: COMPONENTS[0].id, state: 'investigating', limit: '3' };
  const expected = sorted(f.rows.filter(r => r.componentId === filters.component && r.state === filters.state));
  let current = await f.page(filters);
  const snapshot = current.snapshot.id;
  assert.ok(current.nextCursor);
  f.sqlite.prepare("UPDATE incidents SET state='resolved',summary='changed',resolved_at=? WHERE id=?")
    .run('2026-02-01T00:00:00.000Z', expected[5].id);
  f.insert({ id:'late-backdated',componentId:filters.component,state:'investigating',startedAt:expected[7].startedAt });
  const observed = [...current.incidents]; let count = 0;
  while (current.nextCursor) {
    current = await f.page({ ...filters, cursor:current.nextCursor });
    assert.equal(current.snapshot.id, snapshot);
    observed.push(...current.incidents);
    assert.ok(++count < 30, 'bounded traversal must terminate');
  }
  assert.deepEqual(observed.map(r => r.id), expected.map(r => r.id));
  assert.equal(observed.find(r => r.id === expected[5].id).state, 'investigating');
  assert.equal(observed.find(r => r.id === expected[5].id).summary, expected[5].id);
  const refreshed = await f.page({ ...filters, limit:'50' });
  assert.notEqual(refreshed.snapshot.id, snapshot);
  assert.ok(refreshed.incidents.some(r => r.id === 'late-backdated'));
  assert.ok(!refreshed.incidents.some(r => r.id === expected[5].id));
});

test('a cursor cannot be rebound to another filter', async t => {
  const f = await fixture(t);
  const first = await f.page({ component: COMPONENTS[0].id, state:'investigating', limit:'3' });
  for (const filter of [{ component:COMPONENTS[1].id,state:'investigating' },
                        { component:COMPONENTS[0].id,state:'resolved' }]) {
    assert.equal((await f.get({ view:'history-v2', ...filter, cursor:first.nextCursor })).status,400);
  }
});

test('expired snapshot is explicit 410 and does not silently restart traversal', async t => {
  const f = await fixture(t);
  const first = await f.page({ limit:'3' });
  assert.ok(first.nextCursor);
  const expiry = Date.parse(first.snapshot.expiresAt);
  assert.ok(expiry > Date.now() && expiry <= Date.now()+30*60*1000+2000);
  const OriginalDate = Date;
  globalThis.Date = class extends OriginalDate {
    constructor(...args) { super(...(args.length ? args : [expiry+1000])); }
    static now() { return expiry+1000; }
  };
  try {
    const response = await f.get({ view:'history-v2',limit:'3',cursor:first.nextCursor });
    assert.equal(response.status,410);
    assert.equal((await response.json()).error,'history_snapshot_expired');
  } finally { globalThis.Date=OriginalDate; }
});
