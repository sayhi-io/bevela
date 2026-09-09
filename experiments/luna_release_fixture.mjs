// Disposable evaluator adapter for the Luna release study.  This file is not
// product code and must never be imported by the Status worker at runtime.
import { createServer } from "node:http";
import { DatabaseSync } from "node:sqlite";
import { mkdtempSync, readFileSync, readdirSync, rmSync } from "node:fs";
import { join, resolve } from "node:path";
import { tmpdir } from "node:os";
import { fileURLToPath, pathToFileURL } from "node:url";
import { spawn } from "node:child_process";

const BASELINE_MIGRATIONS = new Set([
  "0001_initial.sql",
  "0002_incident_reports.sql",
  "0003_component_versions.sql",
]);
const FIXED_START = Date.parse("2026-01-01T00:00:00.000Z");
const MARKER = '<b data-history-marker="inert">literal fixture</b>';

function makeD1(sqlite) {
  return {
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
    async batch(statements) {
      sqlite.exec("BEGIN");
      try {
        const results = [];
        for (const statement of statements) results.push(await statement.run());
        sqlite.exec("COMMIT");
        return results;
      } catch (error) {
        sqlite.exec("ROLLBACK");
        throw error;
      }
    },
  };
}

function seedRows(components) {
  return Array.from({ length: 67 }, (_, i) => ({
    id: `incident-${String(i).padStart(3, "0")}`,
    componentId: components[i % 2].id,
    state: i % 3 ? "investigating" : "resolved",
    summary: i === 66 ? MARKER : `Incident fixture ${i}`,
    severity: "degraded",
    startedAt: new Date(Date.UTC(2026, 0, 1, 0, Math.floor(i / 3))).toISOString(),
  }));
}

function insertStatement(sqlite, row) {
  return sqlite.prepare(`INSERT INTO incidents
    (id, component_id, summary, severity, state, started_at, updated_at, resolved_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)`).run(
    row.id, row.componentId, row.summary ?? row.id, row.severity ?? "degraded",
    row.state, row.startedAt, row.updatedAt ?? row.startedAt,
    row.state === "resolved" ? (row.resolvedAt ?? row.startedAt) : null,
  );
}

function installClock(now) {
  const OriginalDate = globalThis.Date;
  class StudyDate extends OriginalDate {
    constructor(...args) { super(...(args.length ? args : [now()])); }
    static now() { return now(); }
  }
  globalThis.Date = StudyDate;
  return () => { globalThis.Date = OriginalDate; };
}

export async function createFixture(root, { retentionMinutes = 30 } = {}) {
  const checkout = resolve(root);
  const databaseDirectory = mkdtempSync(join(tmpdir(), "luna-release-fixture-"));
  const databasePath = join(databaseDirectory, "fixture.sqlite");
  let sqlite = new DatabaseSync(databasePath);
  let clock = FIXED_START;
  let retention = Number(retentionMinutes);
  let failures = 0;
  let stopped = false;
  const restoreDate = installClock(() => clock);
  const originalFetch = globalThis.fetch;
  let completed = false;
  const guardedFetch = async (input, init) => {
    const url = new URL(typeof input === "string" ? input : input.url);
    if (!/^https?:\/\/(localhost|127\.0\.0\.1)(?::\d+)?\//.test(url.href)) {
      throw new Error("Outbound network disabled in Luna evaluator fixture");
    }
    return originalFetch(input, init);
  };
  // Install the guard before importing candidate modules so top-level code is
  // covered as well as request-time scheduled/check paths.
  globalThis.fetch = guardedFetch;
  try {
  const migrations = readdirSync(`${checkout}/migrations`)
    .filter((file) => file.endsWith(".sql"))
    .sort();
  if (BASELINE_MIGRATIONS.size !== 3 ||
      [...BASELINE_MIGRATIONS].some(file => !migrations.includes(file))) {
    throw new Error(`Unexpected Status baseline migrations: ${migrations.join(", ")}`);
  }
  const apply = file => sqlite.exec(readFileSync(`${checkout}/migrations/${file}`, "utf8"));
  for (const file of migrations.filter(file => BASELINE_MIGRATIONS.has(file))) apply(file);

  let worker = (await import(pathToFileURL(`${checkout}/src/worker.mjs`))).default;
  const { ensureComponents } = await import(pathToFileURL(`${checkout}/src/state.mjs`));
  const { COMPONENTS, PENDING_COMPONENT } = await import(pathToFileURL(`${checkout}/src/components.mjs`));
  const components = [...COMPONENTS, PENDING_COMPONENT].map(({ id, name }) => ({ id, name }));
  let db = makeD1(sqlite);
  await ensureComponents(db, new Date(clock).toISOString());
  const rows = seedRows(COMPONENTS);
  for (const row of rows) insertStatement(sqlite, row);
  // Candidate migrations run after legacy rows exist: this is intentional and
  // catches migrations that only work on an empty database.
  for (const file of migrations.filter(file => !BASELINE_MIGRATIONS.has(file))) apply(file);

  const env = {
    DB: db,
    get HISTORY_RETENTION_MINUTES() { return String(retention); },
    REPORT_HASH_KEY: "study-fixture-report-key",
  };
  const dispatch = async (requestUrl, headers = {}) => {
    const url = new URL(requestUrl, "http://127.0.0.1");
    if (url.pathname === "/api/incidents" && failures > 0) {
      failures -= 1;
      return new Response(JSON.stringify({ error: "fixture_transient_failure" }), {
        status: 503, headers: { "Content-Type": "application/json" },
      });
    }
    return worker.fetch(new Request(url, { headers }), env, {});
  };
  const get = async params => {
    const query = new URLSearchParams(params);
    return dispatch(`http://127.0.0.1/api/incidents?${query}`);
  };
  const request = async (path, init = {}) => dispatch(path, init.headers || {});
  const reopen = async () => {
    if (sqlite) sqlite.close();
    sqlite = new DatabaseSync(databasePath);
    db = makeD1(sqlite);
    env.DB = db;
    worker = (await import(`${pathToFileURL(`${checkout}/src/worker.mjs`)}?fixture-reopen=${Date.now()}`)).default;
    return sqlite;
  };
  const freshProcess = async params => {
    if (sqlite) {
      sqlite.close();
      sqlite = null;
    }
    try {
      return await new Promise((resolveChild, rejectChild) => {
        const child = spawn(process.execPath, [fileURLToPath(import.meta.url), "--luna-child"], {
          env: {
            ...process.env,
            LUNA_CHILD_PAYLOAD: JSON.stringify({
              root: checkout, databasePath, clock, retention,
              query: [...new URLSearchParams(params)],
            }),
          },
          stdio: ["ignore", "pipe", "pipe"],
        });
        let stdout = "";
        let stderr = "";
        child.stdout.on("data", chunk => { stdout += chunk; });
        child.stderr.on("data", chunk => { stderr += chunk; });
        child.once("error", rejectChild);
        child.once("close", status => {
          if (status !== 0) {
            rejectChild(new Error(`Fresh fixture process failed (${status}): ${stderr}`));
            return;
          }
          try { resolveChild(JSON.parse(stdout)); }
          catch (error) { rejectChild(new Error(`Invalid fresh fixture response: ${error.message}; ${stderr}`)); }
        });
      });
    } finally {
      await reopen();
    }
  };
  /*
   * Failure injection is intentionally scoped to /api/incidents. Browser page
   * loads and assets must continue through the candidate worker unchanged.
   */
  const insert = row => { insertStatement(sqlite, row); return row; };
  const setTime = ms => { clock = Number(ms); return clock; };
  const setRetention = minutes => { retention = Number(minutes); return retention; };
  const mutate = () => {
    const target = rows[4];
    sqlite.prepare("UPDATE incidents SET state='resolved', summary='changed by fixture', resolved_at=?, updated_at=? WHERE id=?")
      .run(new Date(clock).toISOString(), new Date(clock).toISOString(), target.id);
    sqlite.prepare("DELETE FROM incidents WHERE id=?").run("incident-060");
    insert({ id: "late-backdated", componentId: rows[0].componentId, state: "investigating",
      summary: "backdated fixture insert", startedAt: rows[7].startedAt });
  };
  const close = () => {
    if (stopped) return;
    stopped = true;
    restoreDate();
    globalThis.fetch = originalFetch;
    if (sqlite) sqlite.close();
    sqlite = null;
    rmSync(databaseDirectory, { recursive: true, force: true });
  };
  const serve = async () => {
    const server = createServer(async (req, res) => {
      try {
        const url = new URL(req.url, `http://127.0.0.1:${server.address()?.port || 0}`);
        if (req.method === "POST" && url.pathname === "/__fixture") {
          let body = "";
          for await (const chunk of req) body += chunk;
          const action = JSON.parse(body).action;
          if (action === "advance") setTime(clock + Number(JSON.parse(body).milliseconds));
          else if (action === "retention") setRetention(JSON.parse(body).minutes);
          else if (action === "mutate") mutate();
          else if (action === "fail-next") failures = Number(JSON.parse(body).count ?? 1);
          else throw new Error("Unknown fixture action");
          res.writeHead(204).end();
          return;
        }
        if (req.method !== "GET") { res.writeHead(405).end(); return; }
        const response = await dispatch(`http://127.0.0.1${req.url}`, req.headers);
        res.writeHead(response.status, Object.fromEntries(response.headers));
        res.end(Buffer.from(await response.arrayBuffer()));
      } catch (error) {
        res.writeHead(500, { "Content-Type": "application/json" });
        res.end(JSON.stringify({ error: "fixture_failure", detail: error.message }));
      }
    });
    await new Promise((resolveListen, reject) => {
      server.once("error", reject);
      server.listen(0, "127.0.0.1", resolveListen);
    });
    const origin = `http://127.0.0.1:${server.address().port}`;
    return {
      origin, server,
      stop: async () => { await new Promise(resolveStop => server.close(resolveStop)); close(); },
    };
  };
  const fixture = {
    get, request, reopen, rows, components, insert, setTime, setRetention, close, serve, mutate,
    freshProcess,
    marker: MARKER,
    get sqlite() { return sqlite; },
  };
  completed = true;
  return fixture;
  } finally {
    if (!completed) {
      restoreDate();
      globalThis.fetch = originalFetch;
      try { if (sqlite) sqlite.close(); } catch {}
      rmSync(databaseDirectory, { recursive: true, force: true });
    }
  }
}

async function runFreshChild() {
  const payload = JSON.parse(process.env.LUNA_CHILD_PAYLOAD || "{}");
  const restoreDate = installClock(() => Number(payload.clock));
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async (input, init) => {
    const url = new URL(typeof input === "string" ? input : input.url);
    if (!/^https?:\/\/(localhost|127\.0\.0\.1)(?::\d+)?\//.test(url.href)) {
      throw new Error("Outbound network disabled in Luna evaluator fixture");
    }
    return originalFetch(input, init);
  };
  const sqlite = new DatabaseSync(payload.databasePath);
  const db = makeD1(sqlite);
  try {
    const worker = (await import(`${pathToFileURL(`${resolve(payload.root)}/src/worker.mjs`)}?luna-child=${process.pid}`)).default;
    const response = await worker.fetch(
      new Request(`http://127.0.0.1/api/incidents?${new URLSearchParams(payload.query)}`),
      { DB: db, HISTORY_RETENTION_MINUTES: String(payload.retention) }, {},
    );
    const text = await response.text();
    let body;
    try { body = JSON.parse(text); } catch { body = text; }
    process.stdout.write(JSON.stringify({ status: response.status, body }));
  } finally {
    sqlite.close();
    restoreDate();
    globalThis.fetch = originalFetch;
  }
}

async function main() {
  if (!process.env.TRIAL_CHECKOUT) throw new Error("TRIAL_CHECKOUT required");
  const fixture = await createFixture(process.env.TRIAL_CHECKOUT);
  const served = await fixture.serve();
  console.log(JSON.stringify({ origin: served.origin, rows: fixture.rows,
    components: fixture.components, marker: fixture.marker }));
  const stop = () => served.stop().catch(error => { console.error(error); process.exitCode = 1; });
  process.once("SIGTERM", stop);
  process.once("SIGINT", stop);
}

if (process.argv[2] === "--luna-child") runFreshChild();
else if (process.argv[1] && resolve(process.argv[1]) === resolve(new URL(import.meta.url).pathname)) main();
