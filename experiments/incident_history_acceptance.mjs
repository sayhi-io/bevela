// Common black-box acceptance: same executable and facts for both arms.
// No product/network calls. TRIAL_CHECKOUT is inspected, never modified.
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

async function fixture() {
  const sqlite = new DatabaseSync(':memory:');
  for (const file of readdirSync(root + '/migrations').filter(f => f.endsWith('.sql')).sort()) {
    sqlite.exec(readFileSync(root + '/migrations/' + file, 'utf8'));
  }
  const db = { async batch(statements) {
    sqlite.exec('BEGIN');
    try {
      const results = [];
      for (const statement of statements) results.push(await statement.run());
      sqlite.exec('COMMIT');
      return results;
    } catch (error) { sqlite.exec('ROLLBACK'); throw error; }
  }, prepare(sql) {
    const statement = sqlite.prepare(sql);
    const bound = (values = []) => ({
      bind: (...args) => bound(args),
      all: async () => ({ results: statement.all(...values), success: true }),
      first: async (column) => {
        const row = statement.get(...values);
        return column ? row?.[column] ?? null : row ?? null;
      },
      run: async () => ({ ...statement.run(...values), success: true }),
    });
    return bound();
  }};
  await ensureComponents(db, '2026-01-01T00:00:00.000Z');
  const rows = Array.from({ length: 67 }, (_, i) => ({
    id: `incident-${String(i).padStart(3, '0')}`,
    componentId: COMPONENTS[i % 2].id,
    state: i % 3 ? 'investigating' : 'resolved',
    startedAt: new Date(Date.UTC(2026, 0, 1, 0, Math.floor(i / 3))).toISOString(),
  }));
  const insert = row => sqlite.prepare(`INSERT INTO incidents
    (id, component_id, summary, severity, state, started_at, updated_at, resolved_at)
    VALUES (?, ?, ?, 'degraded', ?, ?, ?, ?)`).run(row.id, row.componentId,
      row.id === 'incident-005' ? '<strong>literal incident text</strong>' : row.id,
      row.state, row.startedAt, row.startedAt,
      row.state === 'resolved' ? row.startedAt : null);
  rows.forEach(insert);
  async function get(params = '') {
    return worker.fetch(new Request('http://localhost/api/incidents' + params), { DB: db }, {});
  }
  async function page(params = '') {
    const response = await get(params);
    assert.equal(response.status, 200, 'incident history route must succeed');
    const result = await response.json();
    assert.ok(Array.isArray(result.incidents));
    assert.ok(result.nextCursor === null || (typeof result.nextCursor === 'string' && result.nextCursor.length));
    return result;
  }
  return { sqlite, rows, insert, get, page };
}

const sorted = rows => [...rows].sort((a, b) =>
  b.startedAt.localeCompare(a.startedAt) || b.id.localeCompare(a.id)).map(row => row.id);

test('default and bounded page sizes, with public incident fields', async t => {
  const f = await fixture(); t.after(() => f.sqlite.close());
  const result = await f.page();
  assert.equal(result.incidents.length, 10);
  assert.deepEqual(result.incidents.map(r => r.id), sorted(f.rows).slice(0, 10));
  for (const key of ['componentId', 'state', 'startedAt', 'summary']) assert.ok(key in result.incidents[0]);
  assert.equal((await f.page('?limit=50')).incidents.length, 50);
  assert.equal((await f.page('?limit=1')).incidents.length, 1);
});

test('filtered pagination walks all matching rows beyond the old 20-row window', async t => {
  const f = await fixture(); t.after(() => f.sqlite.close());
  const component = COMPONENTS[0].id;
  const expected = sorted(f.rows.filter(r => r.componentId === component && r.state === 'investigating'));
  const ids = []; let cursor = null; let pages = 0;
  do {
    const query = new URLSearchParams({ component, state: 'investigating', limit: '4' });
    if (cursor) query.set('cursor', cursor);
    const result = await f.page('?' + query);
    ids.push(...result.incidents.map(r => r.id)); cursor = result.nextCursor;
    assert.ok(++pages < 30, 'pagination must terminate');
  } while (cursor);
  assert.deepEqual(ids, expected);
  assert.equal(new Set(ids).size, ids.length);
});

test('newer inserts do not duplicate or displace continuation results', async t => {
  const f = await fixture(); t.after(() => f.sqlite.close());
  const first = await f.page('?limit=7');
  assert.ok(first.nextCursor);
  f.insert({ id: 'newer', componentId: COMPONENTS[0].id, state: 'investigating', startedAt: '2026-02-01T00:00:00.000Z' });
  const next = await f.page('?' + new URLSearchParams({ limit: '7', cursor: first.nextCursor }));
  assert.deepEqual(next.incidents.map(r => r.id), sorted(f.rows).slice(7, 14));
});

test('empty history returns empty results with no continuation', async t => {
  const f = await fixture(); t.after(() => f.sqlite.close());
  f.sqlite.exec('DELETE FROM incidents');
  const result = await f.page();
  assert.deepEqual(result.incidents, []);
  assert.equal(result.nextCursor, null);
});

test('invalid values and duplicate query parameters produce 400', async t => {
  const f = await fixture(); t.after(() => f.sqlite.close());
  for (const query of ['limit=0', 'limit=51', 'limit=1.5', 'limit=no',
    'state=made-up', 'component=unknown', 'cursor=not-a-valid-cursor',
    'limit=2&limit=3', 'state=resolved&state=investigating',
    'component=' + encodeURIComponent("unknown'component")]) {
    assert.equal((await f.get('?' + query)).status, 400, query);
  }
  assert.equal(f.sqlite.prepare('SELECT COUNT(*) AS count FROM incidents').get().count, 67);
});
