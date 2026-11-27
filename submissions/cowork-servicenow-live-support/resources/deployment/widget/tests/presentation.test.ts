import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { eventPresentation, supportHeader, type ChatEvent } from "../src/state.ts";

const event = (kind: string, author = "system"): ChatEvent => ({
  id: kind, sequence: 1, kind, author, text: "Update", timestamp: "2026-10-16T17:00:00Z",
});

test("request-first transcript separates routine telemetry without concealing problems", () => {
  for (const kind of ["status", "accepted", "closed"]) assert.equal(eventPresentation(event(kind)), "technical");
  for (const kind of ["error", "unavailable", "translation", "unknown"]) assert.equal(eventPresentation(event(kind)), "attention");
  assert.equal(eventPresentation(event("message", "Alex Rivera")), "conversation");
  assert.equal(eventPresentation(event("message", "user")), "conversation");
  assert.equal(eventPresentation(event("late_message", "Alex Rivera")), "conversation");
});

test("one concise heading reflects queue, representative and terminal state honestly", () => {
  assert.equal(supportHeader({ status: "draft", events: [] }), "IT support");
  assert.equal(supportHeader({ status: "waiting", events: [] }), "Waiting for support");
  assert.equal(supportHeader({ status: "connected", events: [event("accepted", "Alex Rivera"), event("message", "user")] }), "Alex Rivera · IT support");
  assert.equal(supportHeader({ status: "closed", events: [event("accepted", "Alex Rivera")] }), "Chat ended");
  assert.equal(supportHeader({ status: "end_requested", events: [] }), "End requested");
});

test("technical metadata is collapsed and request consent stays visible", () => {
  const html = readFileSync(new URL("../index.html", import.meta.url), "utf8");
  assert.match(html, /<details id="session-details" class="session-details">/);
  assert.match(html, /<summary>Details<\/summary>/);
  assert.match(html, /<label for="summary-input">Your request<\/label>/);
  assert.match(html, /id="confirm-button" type="button"[^>]*>Request support</);
  assert.match(html, /Sends this request to IT support/);
  const details = html.slice(html.indexOf('<details id="session-details"'), html.indexOf("</details>", html.indexOf('<details id="session-details"')));
  for (const id of ["interaction-number", "technical-status", "sync-status", "technical-events"]) {
    assert.ok(details.includes(`id="${id}"`), `${id} must be secondary`);
  }
});
