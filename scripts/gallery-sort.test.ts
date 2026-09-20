import assert from "node:assert/strict";
import test from "node:test";
import { compareNewest } from "../src/lib/gallery-sort";

const item = (
  name: string,
  created: string | undefined,
  updated?: string,
  sample = "0",
) => ({
  dataset: { name, created, updated, sample },
});

test("newest orders skills by creation date rather than update date", () => {
  const older = item("older", "100", "900");
  const newest = item("newest", "300", "300");
  const middle = item("middle", "200", "200");

  assert.deepEqual([older, newest, middle].sort(compareNewest), [
    newest,
    middle,
    older,
  ]);
});

test("newest keeps missing dates last and breaks ties by name", () => {
  const undated = item("undated", undefined);
  const beforeEpoch = item("before-epoch", "-100");
  const beta = item("beta", "100");
  const alpha = item("alpha", "100");

  assert.deepEqual([undated, beforeEpoch, beta, alpha].sort(compareNewest), [
    alpha,
    beta,
    beforeEpoch,
    undated,
  ]);
});
