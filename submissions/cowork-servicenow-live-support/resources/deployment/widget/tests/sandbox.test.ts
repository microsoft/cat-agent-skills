import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

test("Cowork controls do not depend on sandbox-blocked native form submission", () => {
  const html = readFileSync(new URL("../index.html", import.meta.url), "utf8");
  const source = readFileSync(new URL("../src/main.ts", import.meta.url), "utf8");
  assert.doesNotMatch(html, /<form\b|type="submit"/i);
  assert.doesNotMatch(source, /requestSubmit|addEventListener\("submit"/);
  assert.match(source, /confirmButton\.addEventListener\("click"/);
  assert.match(source, /sendButton\.addEventListener\("click"/);
});
