import test from "node:test";
import assert from "node:assert/strict";
import { definitelyNotSent, parseToolResult, ToolError } from "../src/state.ts";

test("definitive pre-send rejection allows editing without labeling it ambiguous", () => {
  for (const code of ["invalid_argument", "invalid_state", "not_found", "chat_closed_not_sent"]) {
    assert.throws(() => parseToolResult({
      isError: true, content: [{ type: "text", text: `${code}: Not sent.` }],
    }), error => error instanceof ToolError && definitelyNotSent(error));
  }
});

test("ambiguous delivery, conflicting keys and transport errors keep the existing retry reference", () => {
  for (const error of [
    new ToolError("delivery_unconfirmed: Reconcile this message."),
    new ToolError("idempotency_conflict: Existing operation."),
    new ToolError("Unclassified service error."),
    new Error("Network disconnected"),
  ]) {
    assert.equal(definitelyNotSent(error), false);
  }
});
