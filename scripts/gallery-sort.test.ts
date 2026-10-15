import assert from "node:assert/strict";
import test from "node:test";
import { compareNewest, compareRecentlyUpdated } from "../src/lib/gallery-sort";

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

test("recently updated prefers update dates and falls back to creation dates", () => {
  const updatedOlder = item("updated-older", "100", "900");
  const newlyCreated = item("newly-created", "500");
  const unchanged = item("unchanged", "300", "300");
  const updateOnly = item("update-only", undefined, "700");

  assert.deepEqual(
    [unchanged, newlyCreated, updatedOlder, updateOnly].sort(compareRecentlyUpdated),
    [updatedOlder, updateOnly, newlyCreated, unchanged],
  );
});

test("recently updated keeps missing dates last and breaks ties by name", () => {
  const undatedBeta = item("undated-beta", undefined);
  const undatedAlpha = item("undated-alpha", undefined);
  const beforeEpoch = item("before-epoch", undefined, "-100");
  const beta = item("beta", "100");
  const alpha = item("alpha", "50", "100");

  assert.deepEqual(
    [undatedBeta, beta, beforeEpoch, undatedAlpha, alpha].sort(compareRecentlyUpdated),
    [alpha, beta, beforeEpoch, undatedAlpha, undatedBeta],
  );
});

test("recently updated preserves a zero update timestamp", () => {
  const epoch = item("epoch", "900", "0");
  const afterEpoch = item("after-epoch", "100");

  assert.deepEqual([epoch, afterEpoch].sort(compareRecentlyUpdated), [afterEpoch, epoch]);
});