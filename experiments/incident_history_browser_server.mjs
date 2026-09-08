// Disposable loopback adapter. Candidate source is imported, never modified.
import { createServer } from 'node:http';
import { DatabaseSync } from 'node:sqlite';
import { readFileSync, readdirSync } from 'node:fs';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

if (!process.env.TRIAL_CHECKOUT) throw new Error('TRIAL_CHECKOUT required');
const root = resolve(process.env.TRIAL_CHECKOUT);
const worker = (await import(pathToFileURL(root + '/src/worker.mjs'))).default;
const { ensureComponents } = await import(pathToFileURL(root + '/src/state.mjs'));
const { COMPONENTS } = await import(pathToFileURL(root + '/src/components.mjs'));
const sqlite = new DatabaseSync(':memory:');
for (const file of readdirSync(root + '/migrations').filter(f => f.endsWith('.sql')).sort()) {
  sqlite.exec(readFileSync(root + '/migrations/' + file, 'utf8'));
}
const db = {
  async batch(statements) {
    sqlite.exec('BEGIN');
    try {
      const results = [];
      for (const statement of statements) results.push(await statement.run());
      sqlite.exec('COMMIT');
      return results;
    } catch (error) { sqlite.exec('ROLLBACK'); throw error; }
  },
  prepare(sql) {
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
  },
};
await ensureComponents(db, '2026-01-01T00:00:00.000Z');
const marker = '<b data-history-marker="inert">literal fixture</b>';
const rows = Array.from({ length: 67 }, (_, i) => ({
  id: `incident-${String(i).padStart(3, '0')}`,
  componentId: COMPONENTS[i % 2].id,
  state: i % 3 ? 'investigating' : 'resolved',
  summary: i === 66 ? marker : `Incident fixture ${i}`,
  startedAt: new Date(Date.UTC(2026, 0, 1, 0, Math.floor(i / 3))).toISOString(),
}));
for (const row of rows) sqlite.prepare(`INSERT INTO incidents
  (id, component_id, summary, severity, state, started_at, updated_at, resolved_at)
  VALUES (?, ?, ?, 'degraded', ?, ?, ?, ?)`).run(row.id, row.componentId,
    row.summary, row.state, row.startedAt, row.startedAt,
    row.state === 'resolved' ? row.startedAt : null);

// Even accidental candidate outbound fetches cannot reach monitored services.
globalThis.fetch = async () => { throw new Error('Outbound network disabled in browser fixture'); };
const server = createServer(async (req, res) => {
  try {
    if (req.method !== 'GET') { res.writeHead(405); res.end(); return; }
    const url = `http://127.0.0.1:${server.address().port}${req.url}`;
    const response = await worker.fetch(new Request(url, { headers: req.headers }), { DB: db }, {});
    res.writeHead(response.status, Object.fromEntries(response.headers));
    res.end(Buffer.from(await response.arrayBuffer()));
  } catch (error) {
    console.error(error.stack);
    res.writeHead(500, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ error: 'Browser fixture worker failure' }));
  }
});
server.listen(0, '127.0.0.1', () => console.log(JSON.stringify({
  origin: `http://127.0.0.1:${server.address().port}`, rows,
  components: COMPONENTS.map(c => ({ id: c.id, name: c.name })), marker,
})));
process.on('SIGTERM', () => server.close(() => { sqlite.close(); process.exit(0); }));
