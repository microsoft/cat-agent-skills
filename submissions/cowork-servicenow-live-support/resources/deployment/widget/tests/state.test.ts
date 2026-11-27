import test from "node:test";
import assert from "node:assert/strict";
import {
  canSend, demoAllowed, isTerminal, mergeEvents, mergeSnapshot, nextCallDelay, parseDemoResult, parseToolResult,
  pollDelay, prepareMessage, SerialExecutor, shouldPoll,
  type ChatEvent, type Snapshot,
} from "../src/state.ts";

const event = (sequence: number, text = `Message ${sequence}`, id = `event-${sequence}`): ChatEvent => ({
  id, sequence, kind: "agent", author: "Taylor · Support", text, timestamp: "2026-10-16T14:00:00Z",
});
const snapshot = (overrides: Partial<Snapshot> = {}): Snapshot => ({
  sessionId: "session-1", status: "connected", summary: "VPN help", interactionNumber: "INT0001",
  events: [], nextCursor: 0, hasMore: false, ...overrides,
});

test("structured result and JSON text fallback read the same contract", () => {
  const data = snapshot();
  assert.deepEqual(parseToolResult({ structuredContent: data }), data);
  assert.deepEqual(parseToolResult({ content: [{ type: "text", text: "Status" }, { type: "text", text: JSON.stringify(data) }] }), data);
});

test("development adapter accepts root snapshots without relaxing the production MCP contract", () => {
  const data = snapshot();
  assert.deepEqual(parseDemoResult(data), data);
  assert.deepEqual(parseDemoResult({ structuredContent: data }), data);
  assert.throws(() => parseToolResult(data), /no readable/);
  assert.throws(() => parseDemoResult({ ...data, isError: true, content: [{ type: "text", text: "Demo failure" }] }), /Demo failure/);
});

test("isError never falls through to a success-shaped root", () => {
  assert.throws(() => parseToolResult({ isError: true, structuredContent: snapshot(), content: [{ type: "text", text: "Session expired" }] }), /Session expired/);
  assert.throws(() => parseToolResult({ isError: true }), /could not complete/);
});

test("malformed payloads and invalid events are explicit errors", () => {
  assert.throws(() => parseToolResult({ structuredContent: snapshot({ status: "invented" as Snapshot["status"] }) }), /invalid session/);
  assert.throws(() => parseToolResult({ structuredContent: snapshot({ events: [{ ...event(1), sequence: -1 }] }) }), /invalid transcript/);
  assert.throws(() => parseToolResult({ content: [] }), /no readable/);
});

test("nullable optional fields from a C# JSON result are accepted", () => {
  const root = { ...snapshot(), events: [{ ...event(1), originalText: null, language: null }] };
  const parsed = parseToolResult({ structuredContent: root });
  assert.equal(parsed.events[0].originalText, undefined);
  assert.equal(parsed.events[0].language, undefined);
});

test("events are sorted and deduplicated across replays and overlapping pages", () => {
  assert.deepEqual(mergeEvents([event(3), event(1)], [event(2), event(1), event(3)]).map(e => e.sequence), [1, 2, 3]);
  assert.equal(mergeEvents([event(1)], [event(1, "Corrected")])[0].text, "Corrected");
  assert.equal(mergeEvents([event(1)], [event(1, "Replay", "alternate-id")]).length, 1);
});

test("mutation pages never advance cursor and cause lost transcript messages", () => {
  const initial = mergeSnapshot(undefined, snapshot({ events: [event(9)], nextCursor: 9 }), false);
  assert.equal(initial.cursor, 0);
  const polled = mergeSnapshot(initial, snapshot({ events: [event(1), event(2)], nextCursor: 2, hasMore: true }), true);
  assert.equal(polled.cursor, 2);
  assert.deepEqual(polled.events.map(e => e.sequence), [1, 2, 9]);
  const sent = mergeSnapshot(polled, snapshot({ events: [event(10)], nextCursor: 10 }), false);
  assert.equal(sent.cursor, 2);
});

test("remount replays from zero instead of trusting an old host cursor", () => {
  const remount = mergeSnapshot(undefined, snapshot({ nextCursor: 80, events: [event(80)] }), false);
  assert.equal(remount.cursor, 0);
  const replay = mergeSnapshot(remount, snapshot({ nextCursor: 2, events: [event(1), event(2)], hasMore: true }), true);
  assert.deepEqual(replay.events.map(e => e.sequence), [1, 2, 80]);
});

test("stalled cursors and cross-session data fail without skipping", () => {
  const initial = mergeSnapshot(undefined, snapshot({ nextCursor: 3 }), true);
  assert.throws(() => mergeSnapshot(initial, snapshot({ hasMore: true, nextCursor: 3 }), true), /stopped advancing/);
  assert.throws(() => mergeSnapshot(initial, snapshot({ sessionId: "other" }), false), /different session/);
});

test("closed remote sessions keep polling for delayed delivery without reopening input", () => {
  const closing = mergeSnapshot(undefined, snapshot({ status: "closed", hasMore: true, nextCursor: 1, events: [event(1)] }), true);
  assert.equal(shouldPoll(closing, true, false), true);
  const complete = mergeSnapshot(closing, snapshot({ status: "closed", nextCursor: 2, events: [event(2, "Agent’s final response")] }), true);
  assert.equal(shouldPoll(complete, true, false), true);
  assert.equal(complete.events.at(-1)?.text, "Agent’s final response");
  assert.equal(shouldPoll(complete, true, false, true), true);
  assert.equal(shouldPoll({ ...complete, interactionNumber: null }, true, false), false);
  assert.equal(shouldPoll(complete, false, false), false);
  assert.equal(canSend(complete.status), false);
});

test("visibility, teardown, and draft consent pause polling", () => {
  const active = mergeSnapshot(undefined, snapshot(), false);
  const draft = mergeSnapshot(undefined, snapshot({ status: "draft" }), false);
  assert.equal(shouldPoll(active, false, false), false);
  assert.equal(shouldPoll(active, true, true), false);
  assert.equal(shouldPoll(draft, true, false), false);
  assert.equal(shouldPoll(draft, true, false, true), true);
  assert.equal(shouldPoll(undefined, true, false, true), false);
});

test("failure backoff is bounded and returns to four seconds on success", () => {
  assert.deepEqual([0, 1, 2, 3, 4, 50].map(pollDelay), [4000, 8000, 16000, 32000, 60000, 60000]);
  assert.equal(pollDelay(0), 4000);
});

test("one budget spaces sends, polls and user-turn messages below the conversation cap", () => {
  assert.equal(nextCallDelay([], 1000), 0);
  assert.equal(nextCallDelay([1000], 1100), 1400);
  const crowded = Array.from({ length: 40 }, (_, i) => i * 1000 + 1000);
  assert.equal(nextCallDelay(crowded, 42_000), 19_001);
  assert.equal(nextCallDelay(crowded, 101_000), 0);
  const calls: number[] = [];
  let now = 0;
  for (let i = 0; i < 120; i++) {
    now += nextCallDelay(calls, now);
    calls.push(now);
    assert.ok(calls.filter(t => t > now - 60_000).length <= 40);
  }
});

test("ambiguous send retries preserve the original delivery id", () => {
  const pending = prepareMessage(undefined, "  Hello  ", () => "stable-id");
  assert.deepEqual(pending, { clientMessageId: "stable-id", text: "Hello" });
  assert.equal(prepareMessage(pending, "Hello", () => "new-id"), pending);
  assert.throws(() => prepareMessage(pending, "Changed message", () => "new-id"), /Retry the unconfirmed/);
  assert.throws(() => prepareMessage(undefined, " ", () => "id"), /Enter a message/);
});

test("end requested keeps messaging but never pretends to be closed", () => {
  assert.equal(canSend("end_requested"), true);
  assert.equal(isTerminal("end_requested"), false);
  assert.equal(canSend("waiting"), false);
  assert.equal(canSend("closing"), false);
  assert.equal(canSend("closed"), false);
});

test("serialized broker has no overlapping calls and recovers after an error", async () => {
  const executor = new SerialExecutor();
  const order: string[] = [];
  let release!: () => void;
  const barrier = new Promise<void>(resolve => { release = resolve; });
  const first = executor.run(async () => { order.push("first"); await barrier; order.push("done"); throw new Error("Ambiguous"); });
  const second = executor.run(async () => { order.push("second"); return 2; });
  await Promise.resolve();
  assert.deepEqual(order, ["first"]);
  release();
  await assert.rejects(first, /Ambiguous/);
  assert.equal(await second, 2);
  assert.deepEqual(order, ["first", "done", "second"]);
});

test("demo needs explicit flag, loopback origin, and a top-level browser page", () => {
  assert.equal(demoAllowed(new URL("http://127.0.0.1:5099/?demo=1"), true), true);
  assert.equal(demoAllowed(new URL("http://localhost:5173/?demo=1"), true), true);
  assert.equal(demoAllowed(new URL("https://example.com/?demo=1"), true), false);
  assert.equal(demoAllowed(new URL("http://localhost/?demo=1"), false), false);
  assert.equal(demoAllowed(new URL("http://localhost/"), true), false);
  assert.equal(demoAllowed(new URL("file:///widget/index.html?demo=1"), true), false);
});
