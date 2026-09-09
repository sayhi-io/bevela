// Frozen Luna evaluator acceptance.  It tests only the public release contract;
// candidate cursors, snapshot IDs and storage schema remain opaque.
import test from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, readFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import { spawn } from "node:child_process";
import { createFixture } from "./luna_release_fixture.mjs";

const root = resolve(process.env.TRIAL_CHECKOUT || "");
if (!process.env.TRIAL_CHECKOUT) throw new Error("TRIAL_CHECKOUT required");
const components = ["sayhi-web", "sayhi-studio"];
const json = response => response.json();

function expectedPublic(row) {
  return {
    id: row.id, componentId: row.componentId, summary: row.summary,
    severity: row.severity, state: row.state, startedAt: row.startedAt,
    updatedAt: row.startedAt, resolvedAt: row.state === "resolved" ? row.startedAt : null,
  };
}

function sorted(rows) {
  return [...rows].sort((a, b) => b.startedAt.localeCompare(a.startedAt) || b.id.localeCompare(a.id));
}

async function withFixture(fn, options) {
  const fixture = await createFixture(root, options);
  try { return await fn(fixture); } finally { fixture.close(); }
}

test("R1 snapshot freezes membership and displayed public values", async () => withFixture(async fixture => {
  const first = await fixture.get({ view: "history-v2", component: components[0], state: "investigating", limit: "3" });
  assert.equal(first.status, 200);
  const initial = await json(first);
  assert.ok(initial.snapshot?.id && initial.snapshot?.createdAt && initial.snapshot?.expiresAt);
  assert.ok(initial.nextCursor);
  const snapshotId = initial.snapshot.id;
  fixture.mutate();
  const seen = [...initial.incidents];
  let page = initial;
  while (page.nextCursor) {
    const response = await fixture.get({ view: "history-v2", component: components[0], state: "investigating", limit: "3", cursor: page.nextCursor });
    assert.equal(response.status, 200);
    page = await json(response);
    assert.equal(page.snapshot.id, snapshotId);
    seen.push(...page.incidents);
  }
  const expected = sorted(fixture.rows.filter(row => row.componentId === components[0] && row.state === "investigating"))
    .map(expectedPublic);
  assert.deepEqual(seen, expected);
  assert.equal(new Set(seen.map(row => row.id)).size, expected.length);
  assert.equal(seen.find(row => row.id === "incident-004")?.summary, "Incident fixture 4");
  const fresh = await fixture.get({ view: "history-v2", component: components[0], state: "investigating", limit: "50" });
  assert.equal(fresh.status, 200);
  const refreshed = await json(fresh);
  assert.notEqual(refreshed.snapshot.id, snapshotId);
  assert.deepEqual(refreshed.incidents.find(row => row.id === "late-backdated"), {
    id: "late-backdated", componentId: components[0], summary: "backdated fixture insert",
    severity: "degraded", state: "investigating", startedAt: fixture.rows[7].startedAt,
    updatedAt: fixture.rows[7].startedAt, resolvedAt: null,
  });
}));

test("R1 filters bind to a snapshot and reject cross-filter continuation", async () => withFixture(async fixture => {
  const first = await fixture.get({ view: "history-v2", component: components[0], state: "investigating", limit: "2" });
  const body = await json(first);
  assert.ok(body.nextCursor);
  for (const params of [
    { view: "history-v2", component: components[1], state: "investigating", limit: "2", cursor: body.nextCursor },
    { view: "history-v2", component: components[0], state: "resolved", limit: "2", cursor: body.nextCursor },
  ]) assert.equal((await fixture.get(params)).status, 400);
}));

test("R1 persistence keeps an unexpired snapshot across API re-entry", async () => withFixture(async fixture => {
  const first = await fixture.get({ view: "history-v2", limit: "4" });
  const body = await json(first);
  assert.ok(body.snapshot?.id && body.nextCursor);
  const beforeReopen = fixture.sqlite.prepare("SELECT COUNT(*) AS count FROM incidents").get().count;
  // The fixture closes its SQLite handle, then a fresh OS process imports the
  // complete candidate module graph and reads the same database file.
  const continued = await fixture.freshProcess({ view: "history-v2", limit: "4", cursor: body.nextCursor });
  assert.equal(continued.status, 200);
  assert.equal(continued.body.snapshot.id, body.snapshot.id);
  assert.equal(fixture.sqlite.prepare("SELECT COUNT(*) AS count FROM incidents").get().count, beforeReopen);
}));

test("R1 retains legacy API shape and rejects invalid inputs", async () => withFixture(async fixture => {
  const legacy = await fixture.get({});
  assert.equal(legacy.status, 200);
  const legacyBody = await json(legacy);
  assert.ok(Array.isArray(legacyBody.incidents));
  assert.equal("snapshot" in legacyBody, false);
  for (const params of [
    { view: "history-v2", limit: "0" }, { view: "history-v2", limit: "51" },
    { view: "history-v2", state: "bogus" }, { view: "history-v2", component: "not-canonical" },
    { view: "history-v2", limit: "2", extra: "x" },
  ]) assert.equal((await fixture.get(params)).status, 400);
  const duplicate = new URLSearchParams([["view", "history-v2"]]);
  duplicate.append("view", "history-v2");
  assert.equal((await fixture.get(duplicate)).status, 400);
}));

test("R2 retroactively shortens retention and returns explicit 410", async () => withFixture(async fixture => {
  const first = await fixture.get({ view: "history-v2", limit: "3" });
  const body = await json(first);
  assert.ok(body.nextCursor);
  fixture.setRetention(10);
  fixture.setTime(Date.parse(body.snapshot.createdAt) + 10 * 60 * 1000);
  const expired = await fixture.get({ view: "history-v2", limit: "3", cursor: body.nextCursor });
  assert.equal(expired.status, 410);
  assert.deepEqual(await json(expired), { error: "history_snapshot_expired" });
}));

test("R1 enforces page limits, replay from snapshot start, and snapshot mismatch", async () => withFixture(async fixture => {
  const first = await fixture.get({ view: "history-v2", limit: "1" });
  assert.equal(first.status, 200);
  const body = await json(first);
  assert.equal(body.incidents.length, 1);
  assert.ok(body.nextCursor);
  const replay = await fixture.get({ view: "history-v2", snapshot: body.snapshot.id, limit: "1" });
  assert.equal(replay.status, 200);
  assert.deepEqual((await json(replay)).incidents, body.incidents);
  const second = await fixture.get({ view: "history-v2", limit: "1" });
  assert.equal(second.status, 200);
  const secondBody = await json(second);
  assert.notEqual(secondBody.snapshot.id, body.snapshot.id);
  const mismatch = await fixture.get({ view: "history-v2", snapshot: secondBody.snapshot.id, limit: "1", cursor: body.nextCursor });
  assert.equal(mismatch.status, 400);
  const max = await fixture.get({ view: "history-v2", limit: "50" });
  assert.equal(max.status, 200);
  assert.equal((await json(max)).incidents.length, 50);
}));

test("R2 advertises retroactively shortened effective expiry", async () => withFixture(async fixture => {
  const first = await fixture.get({ view: "history-v2", limit: "2" });
  assert.equal(first.status, 200);
  const body = await json(first);
  const created = Date.parse(body.snapshot.createdAt);
  fixture.setRetention(10);
  fixture.setTime(created + 5 * 60 * 1000);
  const shortened = await fixture.get({ view: "history-v2", snapshot: body.snapshot.id, limit: "2" });
  assert.equal(shortened.status, 200);
  assert.equal(Date.parse((await json(shortened)).snapshot.expiresAt), created + 10 * 60 * 1000);
  fixture.setTime(created + 10 * 60 * 1000);
  const expired = await fixture.get({ view: "history-v2", snapshot: body.snapshot.id, limit: "2" });
  assert.equal(expired.status, 410);
}));

test("R2 never extends a snapshot originally created with shorter retention", { timeout: 20_000 }, async () => withFixture(async fixture => {
  const first = await fixture.get({ view: "history-v2", limit: "2" });
  assert.equal(first.status, 200);
  const body = await json(first);
  const created = Date.parse(body.snapshot.createdAt);
  assert.equal(Date.parse(body.snapshot.expiresAt), created + 10 * 60 * 1000);
  fixture.setRetention(60);
  fixture.setTime(created + 10 * 60 * 1000);
  const expired = await fixture.get({ view: "history-v2", snapshot: body.snapshot.id, limit: "2" });
  assert.equal(expired.status, 410);
}, { retentionMinutes: 10 }));

const support = process.env.SUPPORT_CHECKOUT && resolve(process.env.SUPPORT_CHECKOUT);
const exportScript = support && join(support, "bin", "export-history.mjs");

function runExport(args, env = {}) {
  return new Promise((resolveResult, reject) => {
    const child = spawn(process.execPath, [exportScript, ...args], {
      encoding: "utf8", env: { ...process.env, ...env },
    });
    let stdout = "";
    let stderr = "";
    const timer = setTimeout(() => {
      child.kill("SIGKILL");
      reject(new Error("export child exceeded 30 second evaluator timeout"));
    }, 30_000);
    child.stdout.on("data", chunk => { stdout += chunk; });
    child.stderr.on("data", chunk => { stderr += chunk; });
    child.once("error", reject);
    child.once("close", (status, signal) => {
      clearTimeout(timer);
      resolveResult({ status, signal, stdout, stderr });
    });
  });
}

test("R2 CLI max-pages pauses/resumes exact shared public rows and completed reruns are byte-identical", { skip: !exportScript, timeout: 120_000 }, async () => withFixture(async fixture => {
  const served = await fixture.serve();
  const directory = mkdtempSync(join(tmpdir(), "luna-export-"));
  const output = join(directory, "history.jsonl");
  const checkpoint = join(directory, "history.checkpoint.json");
  try {
    const first = await runExport(["--origin", served.origin, "--output", output, "--checkpoint", checkpoint, "--limit", "3", "--max-pages", "2"]);
    assert.equal(first.status, 0, first.stderr);
    const checkpointAfterPause = JSON.parse(readFileSync(checkpoint, "utf8"));
    assert.equal(checkpointAfterPause.complete, false);
    const paused = readFileSync(output, "utf8");
    fixture.mutate();
    const second = await runExport(["--origin", served.origin, "--output", output, "--checkpoint", checkpoint, "--limit", "3"]);
    assert.equal(second.status, 0, second.stderr);
    const lines = readFileSync(output, "utf8").trim().split("\n").filter(Boolean).map(JSON.parse);
    assert.deepEqual(lines, sorted(fixture.rows).map(expectedPublic));
    assert.equal(readFileSync(output, "utf8").startsWith(paused), true);
    assert.equal(JSON.parse(readFileSync(checkpoint, "utf8")).complete, true);
    const completedOutput = readFileSync(output, "utf8");
    const completedCheckpoint = readFileSync(checkpoint, "utf8");
    const replay = await runExport(["--origin", served.origin, "--output", output, "--checkpoint", checkpoint, "--limit", "3"]);
    assert.equal(replay.status, 0, replay.stderr);
    assert.equal(readFileSync(output, "utf8"), completedOutput);
    assert.equal(readFileSync(checkpoint, "utf8"), completedCheckpoint);
  } finally { await served.stop(); }
}));

test("R2 CLI supplied snapshot matches API values and conflicting checkpoint filters preserve files", { skip: !exportScript, timeout: 120_000 }, async () => withFixture(async fixture => {
  const served = await fixture.serve();
  const directory = mkdtempSync(join(tmpdir(), "luna-export-"));
  try {
    const api = await fixture.get({ view: "history-v2", limit: "3" });
    assert.equal(api.status, 200);
    const apiBody = await json(api);
    const output = join(directory, "snapshot.jsonl");
    const checkpoint = join(directory, "snapshot.checkpoint.json");
    const supplied = await runExport([
      "--origin", served.origin, "--output", output, "--checkpoint", checkpoint,
      "--snapshot", apiBody.snapshot.id, "--limit", "3", "--max-pages", "1",
    ]);
    assert.equal(supplied.status, 0, supplied.stderr);
    assert.deepEqual(readFileSync(output, "utf8").trim().split("\n").map(JSON.parse), apiBody.incidents);

    const conflictOutput = join(directory, "conflict.jsonl");
    const conflictCheckpoint = join(directory, "conflict.checkpoint.json");
    const initial = await runExport([
      "--origin", served.origin, "--output", conflictOutput, "--checkpoint", conflictCheckpoint,
      "--component", "sayhi-web", "--limit", "3", "--max-pages", "1",
    ]);
    assert.equal(initial.status, 0, initial.stderr);
    const beforeOutput = readFileSync(conflictOutput, "utf8");
    const beforeCheckpoint = readFileSync(conflictCheckpoint, "utf8");
    const conflict = await runExport([
      "--origin", served.origin, "--output", conflictOutput, "--checkpoint", conflictCheckpoint,
      "--component", "sayhi-studio", "--limit", "3",
    ]);
    assert.notEqual(conflict.status, 0);
    assert.equal(readFileSync(conflictOutput, "utf8"), beforeOutput);
    assert.equal(readFileSync(conflictCheckpoint, "utf8"), beforeCheckpoint);
  } finally { await served.stop(); }
}));

test("R2 CLI keeps output/checkpoint unchanged on 410 and retries a transient failure", { skip: !exportScript }, async () => withFixture(async fixture => {
  const served = await fixture.serve();
  const directory = mkdtempSync(join(tmpdir(), "luna-export-"));
  const output = join(directory, "history.jsonl");
  const checkpoint = join(directory, "history.checkpoint.json");
  try {
    const transient = await fetch(`${served.origin}/__fixture`, { method: "POST", body: JSON.stringify({ action: "fail-next", count: 1 }) });
    assert.equal(transient.status, 204);
    const ok = await runExport(["--origin", served.origin, "--output", output, "--checkpoint", checkpoint, "--limit", "3", "--max-pages", "1"]);
    assert.equal(ok.status, 0, ok.stderr);
    const beforeOutput = readFileSync(output, "utf8");
    const beforeCheckpoint = readFileSync(checkpoint, "utf8");
    const state = JSON.parse(beforeCheckpoint);
    fixture.setRetention(10);
    fixture.setTime(Date.parse(state.snapshot.createdAt) + 10 * 60 * 1000);
    const expired = await runExport(["--origin", served.origin, "--output", output, "--checkpoint", checkpoint, "--limit", "3"]);
    assert.equal(expired.status, 3, expired.stderr);
    assert.match(expired.stderr, /history_snapshot_expired/);
    assert.equal(readFileSync(output, "utf8"), beforeOutput);
    assert.equal(readFileSync(checkpoint, "utf8"), beforeCheckpoint);
  } finally { await served.stop(); }
}));
